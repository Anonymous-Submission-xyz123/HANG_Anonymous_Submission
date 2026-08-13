"""Deterministic case-level resampling that remains tractable at 30 cases."""

from __future__ import annotations

import hashlib
import itertools
import json
import statistics
from typing import Sequence

import numpy as np


BOOTSTRAP_DRAWS = 100_000
SIGN_FLIP_DRAWS = 200_000
EXACT_BOOTSTRAP_MAX_CASES = 6
EXACT_SIGN_FLIP_MAX_CASES = 16
BASE_SEED = 20_260_727


def _percentile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return float("nan")
    return ordered[int(probability * (len(ordered) - 1))]


def _seed(values: Sequence[float], purpose: str) -> int:
    payload = json.dumps(
        {
            "base_seed": BASE_SEED,
            "purpose": purpose,
            "values": [float(value) for value in values],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def bootstrap_mean_ci(
    values: Sequence[float],
    *,
    alpha: float = 0.05,
    draws: int = BOOTSTRAP_DRAWS,
) -> list[float]:
    """Return a case-bootstrap percentile interval for the sample mean.

    The enumeration used in the original five-case runner grows as ``n**n``
    and is not executable for the paper's 30-case cohort.  Small cohorts keep
    the exact calculation; larger cohorts use a deterministic Monte Carlo
    approximation with a fixed, data-derived seed.
    """
    clean = [float(value) for value in values]
    if not clean:
        return [float("nan"), float("nan")]
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between zero and one")
    n = len(clean)
    if n <= EXACT_BOOTSTRAP_MAX_CASES:
        means = [
            statistics.mean(clean[index] for index in sample)
            for sample in itertools.product(range(n), repeat=n)
        ]
    else:
        if draws <= 0:
            raise ValueError("draws must be positive")
        rng = np.random.default_rng(_seed(clean, "case_bootstrap_mean"))
        values_array = np.asarray(clean, dtype=np.float64)
        means_array = np.empty(draws, dtype=np.float64)
        chunk_size = 10_000
        for start in range(0, draws, chunk_size):
            stop = min(draws, start + chunk_size)
            indices = rng.integers(0, n, size=(stop - start, n))
            means_array[start:stop] = values_array[indices].mean(axis=1)
        means = means_array.tolist()
    return [
        _percentile(means, alpha / 2),
        _percentile(means, 1 - alpha / 2),
    ]


def paired_sign_flip_p(
    values: Sequence[float],
    *,
    draws: int = SIGN_FLIP_DRAWS,
) -> float:
    """Return a two-sided paired sign-flip p-value over case-level effects."""
    nonzero = [float(value) for value in values if abs(float(value)) > 1e-12]
    if not nonzero:
        return 1.0
    observed = abs(statistics.mean(nonzero))
    magnitudes = [abs(value) for value in nonzero]
    if len(magnitudes) <= EXACT_SIGN_FLIP_MAX_CASES:
        candidates = (
            abs(
                statistics.mean(
                    sign * magnitude
                    for sign, magnitude in zip(signs, magnitudes)
                )
            )
            for signs in itertools.product((-1.0, 1.0), repeat=len(magnitudes))
        )
        exceed = 0
        total = 0
        for candidate in candidates:
            total += 1
            exceed += candidate >= observed - 1e-12
        return exceed / total

    if draws <= 0:
        raise ValueError("draws must be positive")
    rng = np.random.default_rng(_seed(nonzero, "paired_sign_flip"))
    magnitude_array = np.asarray(magnitudes, dtype=np.float64)
    exceed = 1
    chunk_size = 10_000
    for start in range(0, draws, chunk_size):
        stop = min(draws, start + chunk_size)
        signs = rng.integers(0, 2, size=(stop - start, len(magnitudes)))
        signs = signs * 2 - 1
        candidates = np.abs((signs * magnitude_array).mean(axis=1))
        exceed += int(np.count_nonzero(candidates >= observed - 1e-12))
    # Plus-one correction prevents a zero Monte Carlo p-value.
    return exceed / (draws + 1)


def resampling_metadata(case_count: int) -> dict[str, object]:
    return {
        "independent_unit": "case",
        "base_seed": BASE_SEED,
        "bootstrap": (
            "exact_enumeration"
            if case_count <= EXACT_BOOTSTRAP_MAX_CASES
            else "deterministic_numpy_monte_carlo"
        ),
        "bootstrap_draws": (
            None if case_count <= EXACT_BOOTSTRAP_MAX_CASES else BOOTSTRAP_DRAWS
        ),
        "sign_flip": (
            "exact_enumeration"
            if case_count <= EXACT_SIGN_FLIP_MAX_CASES
            else "deterministic_numpy_monte_carlo_plus_one"
        ),
        "sign_flip_draws": (
            None if case_count <= EXACT_SIGN_FLIP_MAX_CASES else SIGN_FLIP_DRAWS
        ),
    }
