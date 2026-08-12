"""Trace-position residual activation-patching experiment for HANG causal analysis.

This module implements the redesigned causal leg of the HANG mechanism study.
The prior single-direction / single-layer intervention (see
``outputs/_archive/intermediate_reimplementation/``
``hang_reimplementation_20b_ak74_phase1_length_matched_1sample``) failed
its controls because a single linear direction at one layer is the wrong causal
granularity.  Here we patch the *residual-stream states at the trace token
positions* between a matched (forged-trace) run and a length-matched
unrelated-trace run, and measure how much of the Clean-Webshell continuation
margin gap is recovered.

Design principles carried over from ``phase1_controls``:
  * controls and gates are pre-registered here and imported by the runner;
    the runner never re-derives a threshold.
  * an unrelated trace must be an *exact* token-length match of the forged
    trace (difference == 0), removing the length confound that killed the
    earlier run.
  * every reused code path is validated by an identity self-patch (donor ==
    recipient must be a bitwise no-op) before any result is trusted.

Nothing here loads a model; all model interaction goes through the lean
capture/patch helpers ``capture_trace_residuals`` / ``patch_residual_positions``
which take an explicit list of positions so the random-position control shares
the exact same code path as the real patch.
"""

from __future__ import annotations

import contextlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from statistics import median
from typing import Dict, List, Optional, Sequence, Tuple

import torch

from .schemas import TokenSpans
from .scorer import (
    DEFAULT_CLEAN_PREFIX,
    DEFAULT_WEBSHELL_PREFIX,
    ScoredMarginResult,
    _score_kept_continuation_logits,
    continuation_token_partition,
    score_continuation_margin_prefix_causal,
)


# ---------------------------------------------------------------------------
# Case construction
# ---------------------------------------------------------------------------


@dataclass
class PatchCase:
    """A single case: matched (forged) prompt and its length-matched control."""

    case_id: str
    matched_ids: List[int]
    unrelated_ids: List[int]
    trace_span: Tuple[int, int]  # identical token indices in both prompts
    payload_span: Tuple[int, int]
    answer_index: int  # final prompt token index (position scored from)
    unrelated_trace_source: str
    trace_token_count: int
    length_difference_tokens: int
    unrelated_seed: int = 0


def token_spans_from_record(record: dict) -> TokenSpans:
    """Adapt a marker-ablation record's ``token_spans`` dict to ``TokenSpans``.

    The stored dict only carries marker/payload/trace spans, so system and
    task-context spans are left at their defaults.  ``final_prompt_token_index``
    is set to the last prompt token (prompt_tokens - 1).
    """
    spans = record["token_spans"]
    prompt_tokens = int(record["prompt_tokens"])
    return TokenSpans(
        trace_span=tuple(spans["trace_span"]),
        payload_span=tuple(spans["payload_span"]),
        final_prompt_token_index=prompt_tokens - 1,
        generated_token_span=(prompt_tokens, prompt_tokens),
    )


def retokenize_prompt(tokenizer, record: dict) -> List[int]:
    """Re-tokenize the record's rendered prompt and assert it round-trips.

    Guards against a stored ``token_spans`` computed under a different
    tokenizer state: the recomputed length must equal the stored
    ``prompt_tokens`` and the decoded trace span must contain forged-rule text.
    """
    ids = tokenizer(record["rendered_prompt"], add_special_tokens=False)["input_ids"]
    stored = int(record["prompt_tokens"])
    if len(ids) != stored:
        raise ValueError(
            f"{record.get('case_id')}: retokenized prompt has {len(ids)} tokens, "
            f"record claims {stored}"
        )
    return ids


def audit_trace_span(tokenizer, ids: List[int], trace_span: Tuple[int, int]) -> str:
    """Decode the trace span and sanity-check it looks like a transplanted trace.

    Returns the decoded text.  Raises if the span is empty or does not contain
    any analysis/marker-rule vocabulary, so we never splice a wrong span.
    """
    s0, s1 = trace_span
    if not (0 <= s0 < s1 <= len(ids)):
        raise ValueError(f"trace span {trace_span} out of range for {len(ids)} tokens")
    text = tokenizer.decode(ids[s0:s1])
    low = text.lower()
    # The transplanted trace references the business-core marker rule and/or
    # the analysis channel.  Require at least one hallmark so a mis-stored span
    # (e.g. pointing at the payload) is rejected loudly.
    if not text.startswith("/*\n") or not text.endswith("\n*/"):
        raise ValueError(
            "trace span does not include the exact forged-trace delimiters: "
            f"{text[:40]!r} ... {text[-40:]!r}"
        )
    hallmarks = (
        "important-business-core",
        "business-core",
        "business core",
        "classif",
        "webshell",
        "priority rule",
    )
    if not any(h in low for h in hallmarks):
        raise ValueError(
            f"trace span decode does not look like a transplanted trace: {text[:120]!r}"
        )
    return text


def build_exact_length_unrelated_prompt(
    tokenizer,
    matched_ids: Sequence[int],
    trace_span: Tuple[int, int],
    candidate_texts: Sequence[Tuple[str, str]],
    *,
    wrap: Tuple[str, str] = ("/*\n", "\n*/"),
) -> Tuple[List[int], str]:
    """Return an unrelated-trace prompt whose trace span has the EXACT length.

    ``candidate_texts`` is a sequence of (source_name, raw_text).  Each candidate
    is wrapped in the same ``/* ... */`` delimiters the transplanted trace uses,
    tokenized, and trimmed at a sentence boundary before newline padding is
    added to hit the matched trace token count exactly.  Candidates are tried
    in the caller-provided order.  Raises if none contain a usable sentence.

    Returns (unrelated_prompt_ids, source_name).  The non-trace token ids are,
    by construction, byte-identical to ``matched_ids``.
    """
    trace_start, trace_end = trace_span
    target = trace_end - trace_start
    if target <= 0:
        raise ValueError("matched trace span is empty")
    prefix = list(matched_ids[:trace_start])
    suffix = list(matched_ids[trace_end:])
    open_ids = tokenizer(wrap[0], add_special_tokens=False)["input_ids"]
    close_ids = tokenizer(wrap[1], add_special_tokens=False)["input_ids"]
    interior_budget = target - len(open_ids) - len(close_ids)
    if interior_budget <= 0:
        raise ValueError(
            f"trace target {target} too short for wrapper "
            f"({len(open_ids)}+{len(close_ids)} tokens)"
        )

    newline_ids = tokenizer("\n", add_special_tokens=False)["input_ids"]
    if len(newline_ids) != 1:
        raise ValueError("tokenizer must encode a newline as one token")

    for name, raw in candidate_texts:
        normalized = raw.strip()
        if not normalized:
            continue
        # Preserve complete semantic units.  If the whole candidate is too
        # long, select the longest punctuation/newline boundary that fits.
        boundaries = {
            match.end()
            for match in re.finditer(r"(?:[.!?](?:[\"')\]]*)|\n)(?:\s+|$)", normalized)
        }
        boundaries.add(len(normalized))
        choices: List[Tuple[int, List[int]]] = []
        for end in sorted(boundaries):
            piece_ids = tokenizer(
                normalized[:end].rstrip(), add_special_tokens=False
            )["input_ids"]
            if piece_ids and len(piece_ids) <= interior_budget:
                choices.append((end, list(piece_ids)))
        if not choices:
            continue
        _, body_ids = max(choices, key=lambda item: len(item[1]))
        padding = [int(newline_ids[0])] * (interior_budget - len(body_ids))
        trace_ids = list(open_ids) + body_ids + padding + list(close_ids)
        if len(trace_ids) != target:
            raise AssertionError("exact-length assembly failed")
        return prefix + trace_ids + suffix, name

    raise ValueError(
        "no candidate trace could be fit to the exact matched trace length "
        f"({target} tokens); need interior >= {interior_budget} tokens"
    )


def load_marker_ablation_case(
    record_path: Path | str,
    tokenizer,
    candidate_texts: Sequence[Tuple[str, str]],
    *,
    unrelated_seed: int = 0,
) -> PatchCase:
    """Load, audit, and pair one marker-ablation record.

    The marker-ablation records are the authoritative source for this
    experiment.  Stored token counts and the decoded trace delimiters are
    checked before any replacement is constructed.
    """
    path = Path(record_path)
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("condition") != "marker_plus_harvested_trace":
        raise ValueError(f"{path}: not a marker_plus_harvested_trace record")
    if not record.get("api_compatible_success"):
        raise ValueError(f"{path}: record did not produce an API-compatible success")
    spans = token_spans_from_record(record)
    matched_ids = retokenize_prompt(tokenizer, record)
    audit_trace_span(tokenizer, matched_ids, spans.trace_span)
    unrelated_ids, source = build_exact_length_unrelated_prompt(
        tokenizer, matched_ids, spans.trace_span, candidate_texts
    )
    if len(unrelated_ids) != len(matched_ids):
        raise AssertionError("exact-length replacement changed prompt length")
    trace_count = spans.trace_span[1] - spans.trace_span[0]
    return PatchCase(
        case_id=str(record["case_id"]),
        matched_ids=matched_ids,
        unrelated_ids=unrelated_ids,
        trace_span=spans.trace_span,
        payload_span=spans.payload_span,
        answer_index=spans.final_prompt_token_index,
        unrelated_trace_source=source,
        trace_token_count=trace_count,
        length_difference_tokens=0,
        unrelated_seed=int(unrelated_seed),
    )


# ---------------------------------------------------------------------------
# Lean capture / patch (post-layer residual output)
# ---------------------------------------------------------------------------


def _resolve_layers(adapter):
    """Return the decoder ModuleList regardless of adapter/model shape."""
    if hasattr(adapter, "layers"):
        return adapter.layers
    if hasattr(adapter, "model") and hasattr(adapter.model, "layers"):
        return adapter.model.layers
    raise AttributeError("adapter exposes no decoder layers")


def _forward(adapter, input_ids, **kwargs):
    model = adapter.model if hasattr(adapter, "model") else adapter
    return model(input_ids, **kwargs)


def _model_device(adapter):
    model = adapter.model if hasattr(adapter, "model") else adapter
    return next(model.parameters()).device


@torch.inference_mode()
def capture_trace_residuals(
    adapter,
    token_ids: Sequence[int],
    positions: Sequence[int],
    layers: Sequence[int],
) -> Dict[int, torch.Tensor]:
    """Capture post-layer residual states at ``positions`` for each layer.

    Returns ``{layer_idx: tensor[1, len(positions), hidden]}`` on CPU float32.
    Positions are captured explicitly (not as a contiguous slice) so that the
    random-position control captures/patches by the same mechanism.
    """
    decoder = _resolve_layers(adapter)
    normalized_positions = sorted(set(int(p) for p in positions))
    normalized_layers = sorted(set(int(layer) for layer in layers))
    if not normalized_positions:
        raise ValueError("at least one capture position is required")
    if not normalized_layers:
        raise ValueError("at least one capture layer is required")
    if normalized_positions[0] < 0:
        raise ValueError("capture positions must be nonnegative")
    pos = torch.tensor(normalized_positions, dtype=torch.long)
    captured: Dict[int, torch.Tensor] = {}
    handles = []

    def register(layer_idx: int):
        module = decoder[layer_idx]

        def hook(_m, _inp, output):
            value = output[0] if isinstance(output, tuple) else output
            if value.dim() >= 3 and value.shape[1] > int(pos.max()):
                idx = pos.to(value.device)
                captured[layer_idx] = value[:, idx, :].detach().to("cpu", torch.float32)
            return output

        handles.append(module.register_forward_hook(hook))

    for layer_idx in normalized_layers:
        if not 0 <= layer_idx < len(decoder):
            raise IndexError(f"layer {layer_idx} outside [0, {len(decoder)})")
        register(layer_idx)

    try:
        device = _model_device(adapter)
        input_ids = torch.tensor([list(token_ids)], dtype=torch.long, device=device)
        _forward(adapter, input_ids, use_cache=False, return_dict=True)
    finally:
        for handle in handles:
            handle.remove()

    missing = [l for l in normalized_layers if l not in captured]
    if missing:
        raise RuntimeError(f"failed to capture residuals for layers {missing}")
    return captured


@contextlib.contextmanager
def patch_residual_positions(
    adapter,
    donor: Dict[int, torch.Tensor],
    positions: Sequence[int],
    layers: Sequence[int],
):
    """Overwrite post-layer residual states at ``positions`` with donor values.

    ``donor[layer]`` must have shape ``[1, len(positions), hidden]`` in the same
    position order as ``positions`` (as produced by ``capture_trace_residuals``).
    """
    decoder = _resolve_layers(adapter)
    normalized_positions = sorted(set(int(p) for p in positions))
    normalized_layers = sorted(set(int(layer) for layer in layers))
    if not normalized_positions:
        raise ValueError("at least one patch position is required")
    if not normalized_layers:
        raise ValueError("at least one patch layer is required")
    if normalized_positions[0] < 0:
        raise ValueError("patch positions must be nonnegative")
    pos = torch.tensor(normalized_positions, dtype=torch.long)
    handles = []

    def register(layer_idx: int):
        module = decoder[layer_idx]
        donor_acts = donor[layer_idx]
        if donor_acts.dim() != 3 or donor_acts.shape[0] < 1:
            raise ValueError(
                f"layer {layer_idx} donor must have shape [batch, positions, hidden]"
            )
        if donor_acts.shape[1] != len(normalized_positions):
            raise ValueError(
                f"layer {layer_idx} donor has {donor_acts.shape[1]} positions, "
                f"expected {len(normalized_positions)}"
            )

        def hook(_m, _inp, output):
            value = output[0] if isinstance(output, tuple) else output
            if value.dim() < 3 or value.shape[1] <= int(pos.max()):
                return output
            patched = value.clone()
            idx = pos.to(value.device)
            src = donor_acts.to(device=value.device, dtype=value.dtype)
            if src.shape[0] not in (1, value.shape[0]):
                raise ValueError(
                    f"layer {layer_idx} donor batch {src.shape[0]} "
                    f"does not match recipient batch {value.shape[0]}"
                )
            patched[:, idx, :] = src
            if isinstance(output, tuple):
                return (patched,) + tuple(output[1:])
            return patched

        handles.append(module.register_forward_hook(hook))

    for layer_idx in normalized_layers:
        if not 0 <= layer_idx < len(decoder):
            raise IndexError(f"layer {layer_idx} outside [0, {len(decoder)})")
        if layer_idx not in donor:
            raise KeyError(f"missing donor activation for layer {layer_idx}")
        register(layer_idx)

    try:
        yield
    finally:
        for handle in handles:
            handle.remove()


@contextlib.contextmanager
def add_residual_delta_positions(
    adapter,
    delta: Dict[int, torch.Tensor],
    positions: Sequence[int],
    layers: Sequence[int],
    scale: float = 1.0,
):
    """Add a residual-stream direction at explicit positions and layers.

    ``delta[layer]`` has shape ``[batch, positions, hidden]``. A batch of one
    is broadcast; otherwise it must match the active forward batch. Additive
    interventions let a cross-case latent direction be tested without
    overwriting the recipient with task-specific donor content.
    """
    decoder = _resolve_layers(adapter)
    normalized_positions = sorted(set(int(p) for p in positions))
    normalized_layers = sorted(set(int(layer) for layer in layers))
    if not normalized_positions:
        raise ValueError("at least one intervention position is required")
    if not normalized_layers:
        raise ValueError("at least one intervention layer is required")
    if normalized_positions[0] < 0:
        raise ValueError("intervention positions must be nonnegative")
    if not torch.isfinite(torch.tensor(float(scale))):
        raise ValueError("intervention scale must be finite")
    pos = torch.tensor(normalized_positions, dtype=torch.long)
    handles = []

    def register(layer_idx: int):
        module = decoder[layer_idx]
        layer_delta = delta[layer_idx]
        if layer_delta.dim() != 3 or layer_delta.shape[0] < 1:
            raise ValueError(
                f"layer {layer_idx} delta must have shape "
                "[batch, positions, hidden]"
            )
        if layer_delta.shape[1] != len(normalized_positions):
            raise ValueError(
                f"layer {layer_idx} delta has {layer_delta.shape[1]} positions, "
                f"expected {len(normalized_positions)}"
            )

        def hook(_module, _inputs, output):
            value = output[0] if isinstance(output, tuple) else output
            if value.dim() < 3 or value.shape[1] <= int(pos.max()):
                return output
            changed = value.clone()
            idx = pos.to(value.device)
            src = layer_delta.to(device=value.device, dtype=value.dtype)
            if src.shape[0] not in (1, value.shape[0]):
                raise ValueError(
                    f"layer {layer_idx} delta batch {src.shape[0]} "
                    f"does not match recipient batch {value.shape[0]}"
                )
            changed[:, idx, :] = changed[:, idx, :] + float(scale) * src
            if isinstance(output, tuple):
                return (changed,) + tuple(output[1:])
            return changed

        handles.append(module.register_forward_hook(hook))

    for layer_idx in normalized_layers:
        if not 0 <= layer_idx < len(decoder):
            raise IndexError(f"layer {layer_idx} outside [0, {len(decoder)})")
        if layer_idx not in delta:
            raise KeyError(f"missing delta for layer {layer_idx}")
        register(layer_idx)

    try:
        yield
    finally:
        for handle in handles:
            handle.remove()


def make_hooked_forward(adapter, donor=None, positions=None, layers=None):
    """Return a ``hooked_forward(input_ids, logits_to_keep=...)`` for the scorer.

    With ``donor is None`` the forward is unmodified (baseline scoring).  With a
    donor, residual positions are patched during the forward.  The scorer calls
    this twice (Clean / Webshell continuations); the patch positions/layers are
    identical across both calls, which is what we want.
    """
    model = adapter.model if hasattr(adapter, "model") else adapter

    if donor is None:
        def hooked_forward(input_ids, logits_to_keep=0):
            return model(input_ids, use_cache=False, return_dict=True,
                         logits_to_keep=logits_to_keep)
        return hooked_forward

    def hooked_forward(input_ids, logits_to_keep=0):
        with patch_residual_positions(adapter, donor, positions, layers):
            return model(input_ids, use_cache=False, return_dict=True,
                         logits_to_keep=logits_to_keep)
    return hooked_forward


MAX_LAYER_SETS_PER_CALL = 4


def _scoring_sequences(
    tokenizer, prompt_token_ids: Sequence[int]
) -> List[Tuple[List[int], List[int]]]:
    """Build the two exact candidate sequences used by the canonical scorer."""
    shared, clean_suffix, webshell_suffix = continuation_token_partition(
        tokenizer, DEFAULT_CLEAN_PREFIX, DEFAULT_WEBSHELL_PREFIX
    )
    context = list(prompt_token_ids) + shared
    return [
        (context + clean_suffix, clean_suffix),
        (context + webshell_suffix, webshell_suffix),
    ]


@torch.inference_mode()
def capture_scoring_residuals(
    adapter,
    tokenizer,
    prompt_token_ids: Sequence[int],
    positions: Sequence[int],
    layers: Sequence[int],
) -> Dict[int, torch.Tensor]:
    """Capture donors on each exact batch-size-one scoring sequence.

    FlexAttention/bfloat16 kernels can produce sequence- and batch-shape
    differences even at causally earlier positions.  Clean and Webshell donor
    states are therefore captured separately on the exact sequence later used
    to score that candidate.  The returned tensors have shape
    ``[2, positions, hidden]`` in Clean/Webshell order.
    """
    decoder = _resolve_layers(adapter)
    normalized_positions = sorted(set(int(p) for p in positions))
    normalized_layers = sorted(set(int(layer) for layer in layers))
    if not normalized_positions or not normalized_layers:
        raise ValueError("capture requires positions and layers")
    pos = torch.tensor(normalized_positions, dtype=torch.long)
    captured_rows: Dict[int, List[torch.Tensor]] = {
        layer: [] for layer in normalized_layers
    }
    device = _model_device(adapter)
    for layer_idx in normalized_layers:
        if not 0 <= layer_idx < len(decoder):
            raise IndexError(f"layer {layer_idx} outside [0, {len(decoder)})")

    for token_ids, _suffix_ids in _scoring_sequences(
        tokenizer, prompt_token_ids
    ):
        captured_candidate: Dict[int, torch.Tensor] = {}
        handles = []

        def register(layer_idx: int):
            def hook(_module, _inputs, output):
                value = output[0] if isinstance(output, tuple) else output
                idx = pos.to(value.device)
                captured_candidate[layer_idx] = (
                    value[:, idx, :].detach().to("cpu", torch.float32)
                )
                return output

            handles.append(decoder[layer_idx].register_forward_hook(hook))

        for layer_idx in normalized_layers:
            register(layer_idx)
        input_ids = torch.tensor(
            [token_ids], dtype=torch.long, device=device
        )
        try:
            _forward(
                adapter,
                input_ids,
                use_cache=False,
                return_dict=True,
            )
        finally:
            for handle in handles:
                handle.remove()
        for layer_idx in normalized_layers:
            if layer_idx in captured_candidate:
                captured_rows[layer_idx].append(captured_candidate[layer_idx])

    missing = [
        layer
        for layer in normalized_layers
        if len(captured_rows[layer]) != 2
    ]
    if missing:
        raise RuntimeError(f"failed to capture scoring residuals for {missing}")
    return {
        layer: torch.cat(rows, dim=0)
        for layer, rows in captured_rows.items()
    }


@torch.inference_mode()
def capture_prefix_scaffold_residuals(
    adapter,
    tokenizer,
    prompt_token_ids: Sequence[int],
    positions: Sequence[int],
    layers: Sequence[int],
) -> Dict[int, torch.Tensor]:
    """Capture one candidate-independent state on the shared answer scaffold.

    Unlike ``capture_scoring_residuals``, this function does not append either
    divergent label suffix. The captured tensor at every layer therefore has
    shape ``[1, positions, hidden]`` and can be applied identically while
    scoring both label candidates.
    """
    shared, _clean_suffix, _webshell_suffix = continuation_token_partition(
        tokenizer, DEFAULT_CLEAN_PREFIX, DEFAULT_WEBSHELL_PREFIX
    )
    token_ids = list(prompt_token_ids) + list(shared)
    decoder = _resolve_layers(adapter)
    normalized_positions = sorted(set(int(p) for p in positions))
    normalized_layers = sorted(set(int(layer) for layer in layers))
    if not normalized_positions or not normalized_layers:
        raise ValueError("capture requires positions and layers")
    if normalized_positions[-1] >= len(token_ids):
        raise ValueError("capture position lies beyond the shared prefix")
    pos = torch.tensor(normalized_positions, dtype=torch.long)
    captured: Dict[int, torch.Tensor] = {}
    handles = []

    def register(layer_idx: int):
        def hook(_module, _inputs, output):
            value = output[0] if isinstance(output, tuple) else output
            idx = pos.to(value.device)
            captured[layer_idx] = (
                value[:, idx, :].detach().to("cpu", torch.float32)
            )
            return output

        handles.append(decoder[layer_idx].register_forward_hook(hook))

    for layer_idx in normalized_layers:
        if not 0 <= layer_idx < len(decoder):
            raise IndexError(f"layer {layer_idx} outside [0, {len(decoder)})")
        register(layer_idx)

    input_ids = torch.tensor(
        [token_ids], dtype=torch.long, device=_model_device(adapter)
    )
    try:
        _forward(
            adapter,
            input_ids,
            use_cache=False,
            return_dict=True,
            logits_to_keep=1,
        )
    finally:
        for handle in handles:
            handle.remove()
    missing = [
        layer for layer in normalized_layers if layer not in captured
    ]
    if missing:
        raise RuntimeError(
            f"failed to capture prefix scaffold residuals for {missing}"
        )
    return captured


@torch.inference_mode()
def score_margin_prefix_causal_with_patch(
    adapter,
    tokenizer,
    prompt_token_ids: Sequence[int],
    donor: Optional[Dict[int, torch.Tensor]] = None,
    positions: Optional[Sequence[int]] = None,
    layers: Optional[Sequence[int]] = None,
) -> ScoredMarginResult:
    """Prefix-causal margin with one identical patch for both candidates."""
    model = adapter.model if hasattr(adapter, "model") else adapter

    def hooked_forward(input_ids, logits_to_keep=1):
        patch_context = (
            patch_residual_positions(adapter, donor, positions, layers)
            if donor is not None
            else contextlib.nullcontext()
        )
        with patch_context:
            return model(
                input_ids,
                use_cache=False,
                return_dict=True,
                logits_to_keep=logits_to_keep,
            )

    return score_continuation_margin_prefix_causal(
        model,
        tokenizer,
        list(prompt_token_ids),
        hooked_forward=hooked_forward,
    )


@torch.inference_mode()
def score_margin_prefix_causal_with_delta(
    adapter,
    tokenizer,
    prompt_token_ids: Sequence[int],
    delta: Dict[int, torch.Tensor],
    positions: Sequence[int],
    layers: Sequence[int],
    scale: float,
) -> ScoredMarginResult:
    """Prefix-causal margin with one identical delta for both candidates."""
    model = adapter.model if hasattr(adapter, "model") else adapter

    def hooked_forward(input_ids, logits_to_keep=1):
        with add_residual_delta_positions(
            adapter, delta, positions, layers, scale
        ):
            return model(
                input_ids,
                use_cache=False,
                return_dict=True,
                logits_to_keep=logits_to_keep,
            )

    return score_continuation_margin_prefix_causal(
        model,
        tokenizer,
        list(prompt_token_ids),
        hooked_forward=hooked_forward,
    )


@torch.inference_mode()
def score_margin_with_patch(
    adapter,
    tokenizer,
    prompt_token_ids: Sequence[int],
    donor: Optional[Dict[int, torch.Tensor]] = None,
    positions: Optional[Sequence[int]] = None,
    layers: Optional[Sequence[int]] = None,
) -> ScoredMarginResult:
    """Score both labels on exact sequences with candidate-matched donors."""
    model = adapter.model if hasattr(adapter, "model") else adapter
    device = next(model.parameters()).device
    scores = []
    for candidate_index, (token_ids, suffix_ids) in enumerate(
        _scoring_sequences(tokenizer, prompt_token_ids)
    ):
        input_ids = torch.tensor(
            [token_ids], dtype=torch.long, device=device
        )
        candidate_donor = None
        if donor is not None:
            candidate_donor = {}
            for layer in layers or ():
                value = donor[int(layer)]
                if value.shape[0] != 2:
                    raise ValueError(
                        f"layer {layer} scoring donor must contain exactly "
                        "two candidate rows"
                    )
                candidate_donor[int(layer)] = value[
                    candidate_index : candidate_index + 1
                ]
        patch_context = (
            patch_residual_positions(
                adapter, candidate_donor, positions, layers
            )
            if candidate_donor is not None
            else contextlib.nullcontext()
        )
        with patch_context:
            outputs = model(
                input_ids,
                use_cache=False,
                return_dict=True,
                logits_to_keep=len(suffix_ids) + 1,
            )
        logits = outputs.logits[0] if hasattr(outputs, "logits") else outputs[0][0]
        scores.append(
            _score_kept_continuation_logits(
                logits,
                suffix_ids,
            )
        )
        del outputs, logits, input_ids
    clean_lp, webshell_lp = scores
    if not (
        torch.isfinite(torch.tensor(clean_lp))
        and torch.isfinite(torch.tensor(webshell_lp))
    ):
        raise RuntimeError("patched scoring produced non-finite log-probability")
    margin = clean_lp - webshell_lp
    return ScoredMarginResult(
        clean_lp,
        webshell_lp,
        margin,
        "Clean" if margin > 0 else "Webshell",
        margin > 0,
    )


@torch.inference_mode()
def score_margin_with_delta(
    adapter,
    tokenizer,
    prompt_token_ids: Sequence[int],
    delta: Dict[int, torch.Tensor],
    positions: Sequence[int],
    layers: Sequence[int],
    scale: float,
) -> ScoredMarginResult:
    """Score both labels while adding a candidate-matched residual direction."""
    model = adapter.model if hasattr(adapter, "model") else adapter
    device = next(model.parameters()).device
    scores = []
    for candidate_index, (token_ids, suffix_ids) in enumerate(
        _scoring_sequences(tokenizer, prompt_token_ids)
    ):
        candidate_delta = {}
        for layer in layers:
            value = delta[int(layer)]
            if value.shape[0] != 2:
                raise ValueError(
                    f"layer {layer} scoring delta must contain exactly "
                    "two candidate rows"
                )
            candidate_delta[int(layer)] = value[
                candidate_index : candidate_index + 1
            ]
        input_ids = torch.tensor(
            [token_ids], dtype=torch.long, device=device
        )
        with add_residual_delta_positions(
            adapter,
            candidate_delta,
            positions,
            layers,
            scale,
        ):
            outputs = model(
                input_ids,
                use_cache=False,
                return_dict=True,
                logits_to_keep=len(suffix_ids) + 1,
            )
        logits = outputs.logits[0] if hasattr(outputs, "logits") else outputs[0][0]
        scores.append(
            _score_kept_continuation_logits(
                logits,
                suffix_ids,
            )
        )
        del outputs, logits, input_ids
    clean_lp, webshell_lp = scores
    if not (
        torch.isfinite(torch.tensor(clean_lp))
        and torch.isfinite(torch.tensor(webshell_lp))
    ):
        raise RuntimeError(
            "additive intervention produced non-finite log-probability"
        )
    margin = clean_lp - webshell_lp
    return ScoredMarginResult(
        clean_lp,
        webshell_lp,
        margin,
        "Clean" if margin > 0 else "Webshell",
        margin > 0,
    )


@torch.inference_mode()
def score_margins_many_layer_sets(
    adapter,
    tokenizer,
    prompt_token_ids: Sequence[int],
    donor: Dict[int, torch.Tensor],
    positions: Sequence[int],
    named_layer_sets: Sequence[Tuple[str, Sequence[int]]],
) -> Dict[str, ScoredMarginResult]:
    """Score layer sets sequentially under one canonical batch-size-one path.

    The previous optimization packed four interventions into an eight-row
    batch.  On FlexAttention/bfloat16 that made the measured margin depend on
    how many layer sets happened to share a call.  Sequential evaluation is
    slower but makes experimental grouping irrelevant.
    """
    if not 1 <= len(named_layer_sets) <= MAX_LAYER_SETS_PER_CALL:
        raise ValueError(f"expected 1..{MAX_LAYER_SETS_PER_CALL} layer sets")
    return {
        name: score_margin_with_patch(
            adapter,
            tokenizer,
            prompt_token_ids,
            donor,
            positions,
            layers,
        )
        for name, layers in named_layer_sets
    }


# ---------------------------------------------------------------------------
# Layer sets and position controls
# ---------------------------------------------------------------------------


def layer_sets(num_layers: int, kind: str) -> List[Tuple[str, List[int]]]:
    """Enumerate (key, layers) for a stage.

    kinds: 'all', 'prefix', 'suffix', 'window3', 'single'.
    """
    if num_layers <= 0:
        raise ValueError("num_layers must be positive")
    if kind == "all":
        return [("all", list(range(num_layers)))]
    if kind == "prefix":
        return [(f"prefix_{k}", list(range(0, k + 1))) for k in range(num_layers)]
    if kind == "suffix":
        return [(f"suffix_{k}", list(range(k, num_layers))) for k in range(num_layers)]
    if kind == "window3":
        return [
            (f"window3_{l}", [l, l + 1, l + 2])
            for l in range(0, num_layers - 2)
        ]
    if kind == "single":
        return [(f"single_{l}", [l]) for l in range(num_layers)]
    raise ValueError(f"unknown layer-set kind: {kind}")


def control_layer_windows(
    num_layers: int, window: Sequence[int], num_draws: int = 3
) -> List[List[int]]:
    """Deterministic layer-control windows of the same length, disjoint from ``window``.

    Slides a same-length block to the earliest disjoint positions.  Uses no RNG
    so results are reproducible across resume.
    """
    w = sorted(set(int(x) for x in window))
    size = len(w)
    wset = set(w)
    draws: List[List[int]] = []
    for start in range(0, num_layers - size + 1):
        block = list(range(start, start + size))
        if wset.isdisjoint(block):
            draws.append(block)
        if len(draws) >= num_draws:
            break
    if not draws:
        raise ValueError("no disjoint layer-control window fits")
    return draws


def random_nontrace_positions(
    payload_span: Tuple[int, int], count: int, seed: int
) -> List[int]:
    """Draw ``count`` distinct positions from the payload span (excludes trace)."""
    lo, hi = payload_span
    pool = list(range(lo, hi))
    if len(pool) < count:
        raise ValueError(
            f"payload span {payload_span} has {len(pool)} positions, need {count}"
        )
    g = torch.Generator().manual_seed(int(seed))
    perm = torch.randperm(len(pool), generator=g).tolist()
    return sorted(pool[i] for i in perm[:count])


# ---------------------------------------------------------------------------
# Recovery metric
# ---------------------------------------------------------------------------


def recovery_fraction(
    patched_margin: float,
    baseline_margin: float,
    gap: float,
    direction: str,
) -> float:
    """Fraction of the M-U margin gap recovered (forward) or destroyed (reverse).

    gap = margin(M) - margin(U)  (expected positive).
    forward: recipient is U, patch pushes toward M => (patched - U) / gap.
    reverse: recipient is M, patch pushes toward U => (M - patched) / gap.
    """
    if gap == 0:
        return float("nan")
    if direction == "forward":
        return (patched_margin - baseline_margin) / gap
    if direction == "reverse":
        return (baseline_margin - patched_margin) / gap
    raise ValueError(f"unknown direction: {direction}")


# ---------------------------------------------------------------------------
# Pre-registered gates
# ---------------------------------------------------------------------------


def evaluate_behavioral_gates(
    per_case: Sequence[dict],
    *,
    min_gap_mean: float = 2.0,
    identity_tol: float = 1e-3,
) -> dict:
    """B1-B4 behavioral gate.

    Each row: {case_id, margin_M, margin_U, length_difference, identity_delta}.
    """
    n = len(per_case)
    if n == 0:
        return {
            "passed": False,
            "mean_gap": float("nan"),
            "max_identity_delta": float("nan"),
            "checks": {
                "B1_margin_M_positive": False,
                "B2_U_below_M_all": False,
                "B3_exact_length_all": False,
                "B4_identity_noop_all": False,
            },
        }
    margin_m = [float(r["margin_M"]) for r in per_case]
    gaps = [float(r["margin_M"]) - float(r["margin_U"]) for r in per_case]
    diffs = [int(r["length_difference"]) for r in per_case]
    identity = [abs(float(r["identity_delta"])) for r in per_case]
    checks = {
        "B1_margin_M_positive": sum(m > 0 for m in margin_m) >= max(1, n - 1),
        "B2_U_below_M_all": all(g > 0 for g in gaps) and (sum(gaps) / n) >= min_gap_mean,
        "B3_exact_length_all": all(d == 0 for d in diffs),
        "B4_identity_noop_all": all(x < identity_tol for x in identity),
    }
    return {
        "passed": all(checks.values()),
        "mean_gap": sum(gaps) / n if n else float("nan"),
        "max_identity_delta": max(identity) if identity else float("nan"),
        "checks": checks,
    }


def stage_a_gate(fwd_recoveries: Sequence[float], *, threshold: float = 0.25) -> dict:
    """Falsification checkpoint: median forward recovery over all layers."""
    med = median([float(x) for x in fwd_recoveries]) if fwd_recoveries else float("nan")
    return {
        "passed": med >= threshold,
        "median_forward_recovery_all_layers": med,
        "threshold": threshold,
    }


def evaluate_patch_gates(
    fwd_window: Sequence[float],
    rev_window: Sequence[float],
    prefix_curve: Sequence[float],
    suffix_curve: Sequence[float],
    random_position_effects: Sequence[float],
    layer_control_effects: Sequence[float],
    *,
    recovery_threshold: float = 0.50,
    sign_min: Optional[int] = None,
    mono_tol: float = 0.05,
) -> dict:
    """Primary causal gates C1-C6 on the winning window W.

    fwd_window / rev_window: per-case forward / reverse recovery at W.
    prefix_curve / suffix_curve: median forward recovery vs k (cumulative).
    random_position_effects / layer_control_effects: forward recoveries of the
    count-matched controls at W.
    """
    fwd = [float(x) for x in fwd_window]
    rev = [float(x) for x in rev_window]
    n = len(fwd)
    if sign_min is None:
        sign_min = max(1, n - 1)
    med_fwd = median(fwd) if fwd else float("nan")
    med_rev = median(rev) if rev else float("nan")
    rand_abs = [abs(float(x)) for x in random_position_effects]
    layer_abs = [abs(float(x)) for x in layer_control_effects]

    def nondecreasing(seq):
        return all(b >= a - mono_tol for a, b in zip(seq, seq[1:]))

    def nonincreasing(seq):
        return all(b <= a + mono_tol for a, b in zip(seq, seq[1:]))

    checks = {
        "C1_sufficiency": med_fwd >= recovery_threshold,
        "C2_necessity": med_rev >= recovery_threshold,
        "C3_sign_consistency": (
            sum(x > 0 for x in fwd) >= sign_min and sum(x > 0 for x in rev) >= sign_min
        ),
        "C4_position_specific": bool(rand_abs) and med_fwd > max(rand_abs)
        and med_fwd > 2 * median(rand_abs),
        "C5_layer_specific": bool(layer_abs) and med_fwd > max(layer_abs)
        and med_fwd > 2 * median(layer_abs),
        "C6a_prefix_nondecreasing": nondecreasing([float(x) for x in prefix_curve]),
        "C6b_suffix_nonincreasing": nonincreasing([float(x) for x in suffix_curve]),
    }
    return {
        "passed": all(checks.values()),
        "median_forward_recovery": med_fwd,
        "median_reverse_recovery": med_rev,
        "max_abs_random_position_effect": max(rand_abs) if rand_abs else float("nan"),
        "max_abs_layer_control_effect": max(layer_abs) if layer_abs else float("nan"),
        "checks": checks,
    }
