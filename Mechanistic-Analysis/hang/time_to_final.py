"""Censoring-aware timing measurements for GPT-OSS final-channel entry."""

from __future__ import annotations

import itertools
import re
import statistics
from collections import defaultdict
from typing import Iterable, Sequence


TIME_TO_FINAL_PROTOCOL = "final_channel_time_to_event_v1"
DEFAULT_TIME_CHECKPOINTS = (128, 256, 384, 512, 768, 1024, 1536, 2048)


def _token_ids(tokenizer, text: str) -> list[int]:
    return list(tokenizer(text, add_special_tokens=False)["input_ids"])


def _subsequence_starts(
    values: Sequence[int], pattern: Sequence[int]
) -> Iterable[int]:
    width = len(pattern)
    if width == 0:
        return
    target = [int(value) for value in pattern]
    for start in range(len(values) - width + 1):
        if [int(value) for value in values[start : start + width]] == target:
            yield start


def final_channel_event_token(
    tokenizer,
    generated_token_ids: Sequence[int],
) -> int | None:
    """Return the one-based token index where the final channel begins.

    GPT-OSS may include a constraint segment between the ``final`` channel
    declaration and the message token. The parser therefore anchors on the
    channel and message special-token sequences, then validates the decoded
    header rather than assuming one exact header tokenization.
    """
    token_ids = [int(value) for value in generated_token_ids]
    channel = _token_ids(tokenizer, "<|channel|>")
    message = _token_ids(tokenizer, "<|message|>")
    if not channel or not message:
        raise ValueError("tokenizer cannot encode GPT-OSS channel delimiters")

    header_pattern = re.compile(
        r"^<\|channel\|>final"
        r"(?:\s*<\|constrain\|>[^<]+)?"
        r"<\|message\|>$",
        flags=re.DOTALL,
    )
    message_starts = list(_subsequence_starts(token_ids, message))
    for channel_start in _subsequence_starts(token_ids, channel):
        for message_start in message_starts:
            if message_start < channel_start + len(channel):
                continue
            if message_start - channel_start > 128:
                break
            header_end = message_start + len(message)
            header = tokenizer.decode(
                token_ids[channel_start:header_end],
                skip_special_tokens=False,
            )
            if header_pattern.fullmatch(header):
                return channel_start + 1
    return None


def annotate_generation_timing(
    tokenizer,
    row: dict,
    *,
    max_new_tokens: int,
) -> dict:
    """Add final-entry event time and explicit censoring fields to a record."""
    token_ids = [int(value) for value in row.get("generated_token_ids", [])]
    generated_tokens = int(row.get("generated_tokens", len(token_ids)))
    if generated_tokens != len(token_ids):
        raise ValueError("generated token count does not match stored token IDs")
    if max_new_tokens <= 0:
        raise ValueError("max_new_tokens must be positive")

    event_token = final_channel_event_token(tokenizer, token_ids)
    event_observed = event_token is not None
    stopped_at_cap = generated_tokens >= int(max_new_tokens)
    right_censored = not event_observed and stopped_at_cap
    terminal_without_final = not event_observed and not stopped_at_cap
    parser_found = bool(row.get("final_channel_found", event_observed))
    return {
        "time_to_final_protocol": TIME_TO_FINAL_PROTOCOL,
        "generation_max_new_tokens": int(max_new_tokens),
        "final_channel_event_observed": event_observed,
        "final_channel_event_token": event_token,
        "time_to_final_or_censor_tokens": (
            int(event_token) if event_observed else generated_tokens
        ),
        "generation_stopped_at_cap": stopped_at_cap,
        "right_censored_at_token_cap": right_censored,
        "terminal_without_final_channel": terminal_without_final,
        "timing_parser_matches_final_parser": parser_found == event_observed,
    }


def _percentile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return float("nan")
    return ordered[int(probability * (len(ordered) - 1))]


def _exact_case_bootstrap_ci(values: Sequence[float]) -> list[float]:
    clean = [float(value) for value in values]
    if not clean:
        return [float("nan"), float("nan")]
    n = len(clean)
    means = [
        statistics.mean(clean[index] for index in sample)
        for sample in itertools.product(range(n), repeat=n)
    ]
    return [_percentile(means, 0.025), _percentile(means, 0.975)]


def _paired_sign_flip_p(values: Sequence[float]) -> float:
    nonzero = [float(value) for value in values if abs(float(value)) > 1e-12]
    if not nonzero:
        return 1.0
    observed = abs(statistics.mean(nonzero))
    magnitudes = [abs(value) for value in nonzero]
    candidates = [
        abs(
            statistics.mean(
                sign * magnitude
                for sign, magnitude in zip(signs, magnitudes)
            )
        )
        for signs in itertools.product((-1.0, 1.0), repeat=len(magnitudes))
    ]
    return (
        sum(value >= observed - 1e-12 for value in candidates)
        / len(candidates)
    )


def summarize_time_to_final(
    rows: Sequence[dict],
    *,
    checkpoints: Sequence[int] = DEFAULT_TIME_CHECKPOINTS,
) -> dict:
    """Summarize within-budget final entry without treating capped runs as exits.

    The cumulative-incidence curve uses all runs in the denominator. Runs that
    terminate without entering the final channel remain non-events, while runs
    still deliberating at the generation cap are explicitly right-censored.
    The restricted mean is ``mean(min(T_final, horizon))`` with non-events set
    to the common horizon, so a smaller value means earlier final entry.
    """
    if not rows:
        return {
            "protocol": TIME_TO_FINAL_PROTOCOL,
            "n": 0,
            "rates_by_marker": {},
            "case_count": 0,
        }
    protocols = {
        str(row.get("time_to_final_protocol")) for row in rows
    }
    if protocols != {TIME_TO_FINAL_PROTOCOL}:
        raise ValueError(f"incompatible timing protocols: {sorted(protocols)}")
    horizons = {
        int(row["generation_max_new_tokens"]) for row in rows
    }
    if len(horizons) != 1:
        raise ValueError(
            "time-to-final summary requires one common generation horizon"
        )
    horizon = horizons.pop()
    valid_checkpoints = sorted(
        {
            int(value)
            for value in checkpoints
            if 0 < int(value) <= horizon
        }
        | {horizon}
    )

    grouped: dict[bool, list[dict]] = defaultdict(list)
    by_case_marker: dict[tuple[str, bool], list[dict]] = defaultdict(list)
    for row in rows:
        marker = bool(row["marker_present"])
        grouped[marker].append(row)
        by_case_marker[(str(row["case_id"]), marker)].append(row)

    rates = {}
    for marker in (False, True):
        values = grouped.get(marker, [])
        event_times = [
            int(row["final_channel_event_token"])
            for row in values
            if bool(row["final_channel_event_observed"])
        ]
        restricted_times = [
            (
                int(row["final_channel_event_token"])
                if bool(row["final_channel_event_observed"])
                else horizon
            )
            for row in values
        ]
        rates[str(marker)] = {
            "n": len(values),
            "event_count": len(event_times),
            "event_rate_by_horizon": (
                len(event_times) / len(values) if values else float("nan")
            ),
            "right_censored_count": sum(
                bool(row["right_censored_at_token_cap"]) for row in values
            ),
            "terminal_without_final_count": sum(
                bool(row["terminal_without_final_channel"]) for row in values
            ),
            "median_event_token_among_events": (
                statistics.median(event_times)
                if event_times
                else float("nan")
            ),
            "restricted_mean_tokens_to_final": (
                statistics.mean(restricted_times)
                if restricted_times
                else float("nan")
            ),
            "cumulative_final_incidence": [
                {
                    "token": checkpoint,
                    "rate": (
                        sum(time <= checkpoint for time in event_times)
                        / len(values)
                        if values
                        else float("nan")
                    ),
                }
                for checkpoint in valid_checkpoints
            ],
        }

    complete_cases = sorted(
        {
            case
            for case, _marker in by_case_marker
            if (case, False) in by_case_marker
            and (case, True) in by_case_marker
        }
    )
    case_rows = []
    event_rate_deltas = []
    restricted_mean_deltas = []
    for case in complete_cases:
        case_values = {}
        for marker in (False, True):
            values = by_case_marker[(case, marker)]
            event_rate = statistics.mean(
                bool(row["final_channel_event_observed"]) for row in values
            )
            restricted_mean = statistics.mean(
                (
                    int(row["final_channel_event_token"])
                    if bool(row["final_channel_event_observed"])
                    else horizon
                )
                for row in values
            )
            case_values[marker] = (event_rate, restricted_mean)
        event_delta = case_values[True][0] - case_values[False][0]
        restricted_delta = case_values[True][1] - case_values[False][1]
        event_rate_deltas.append(event_delta)
        restricted_mean_deltas.append(restricted_delta)
        case_rows.append(
            {
                "case_id": case,
                "event_rate_without_marker": case_values[False][0],
                "event_rate_with_marker": case_values[True][0],
                "marker_event_rate_delta": event_delta,
                "restricted_mean_without_marker": case_values[False][1],
                "restricted_mean_with_marker": case_values[True][1],
                "marker_restricted_mean_delta": restricted_delta,
            }
        )

    return {
        "protocol": TIME_TO_FINAL_PROTOCOL,
        "n": len(rows),
        "generation_horizon_tokens": horizon,
        "rates_by_marker": rates,
        "case_count": len(complete_cases),
        "case_level_rates": case_rows,
        "mean_paired_case_event_rate_delta": (
            statistics.mean(event_rate_deltas)
            if event_rate_deltas
            else float("nan")
        ),
        "paired_case_event_rate_delta_ci95": (
            _exact_case_bootstrap_ci(event_rate_deltas)
        ),
        "paired_case_event_rate_sign_flip_p": (
            _paired_sign_flip_p(event_rate_deltas)
        ),
        "mean_paired_case_restricted_mean_delta": (
            statistics.mean(restricted_mean_deltas)
            if restricted_mean_deltas
            else float("nan")
        ),
        "paired_case_restricted_mean_delta_ci95": (
            _exact_case_bootstrap_ci(restricted_mean_deltas)
        ),
        "paired_case_restricted_mean_sign_flip_p": (
            _paired_sign_flip_p(restricted_mean_deltas)
        ),
        "all_timing_parsers_match": all(
            bool(row["timing_parser_matches_final_parser"]) for row in rows
        ),
    }
