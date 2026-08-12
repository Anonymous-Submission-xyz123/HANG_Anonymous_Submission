"""Shared plotting utilities for the mechanistic-analysis figure scripts."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


METHODS = ("bypass_derived", "synthesized_cot_forgery")
METHOD_LABELS = {
    "bypass_derived": "Harvested (HANG)",
    "synthesized_cot_forgery": "Synthesized (CoT Forgery)",
}

NAVY = "#102A43"
BLUE = "#2563EB"
PURPLE = "#7C3AED"
PURPLE_LIGHT = "#C4B5FD"
ORANGE = "#EA580C"
TEAL = "#0F766E"
GRAY = "#64748B"
GRAY_LIGHT = "#CBD5E1"
INK = "#172033"
MUTED = "#526071"
GRID = "#E6EAF0"
WHITE = "#FFFFFF"


def style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.labelsize": 9,
            "axes.labelcolor": INK,
            "axes.edgecolor": GRAY_LIGHT,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "grid.color": GRID,
            "grid.linewidth": 0.7,
            "grid.alpha": 0.9,
            "legend.frameon": False,
            "figure.facecolor": WHITE,
            "axes.facecolor": WHITE,
            "savefig.facecolor": WHITE,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def title_block(
    figure: plt.Figure,
    title: str,
    subtitle: str,
    *,
    title_y: float = 0.975,
    subtitle_y: float = 0.935,
) -> None:
    figure.text(
        0.06,
        title_y,
        title,
        ha="left",
        va="top",
        color=INK,
        fontsize=16,
        fontweight="bold",
    )
    figure.text(
        0.06,
        subtitle_y,
        subtitle,
        ha="left",
        va="top",
        color=MUTED,
        fontsize=9,
    )


def panel_label(axis: plt.Axes, label: str) -> None:
    axis.text(
        -0.12,
        1.06,
        label,
        transform=axis.transAxes,
        ha="left",
        va="bottom",
        color=INK,
        fontsize=10,
        fontweight="bold",
    )


def footer(figure: plt.Figure, value: str) -> None:
    figure.text(0.06, 0.018, value, ha="left", va="bottom", color=GRAY, fontsize=7)


def save_figure(
    figure: plt.Figure,
    output_dir: Path,
    stem: str,
    dpi: int,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    targets = [output_dir / f"{stem}.png", output_dir / f"{stem}.pdf"]
    figure.savefig(targets[0], dpi=dpi, bbox_inches="tight")
    figure.savefig(targets[1], bbox_inches="tight")
    plt.close(figure)
    return targets


def auc_score(labels: Iterable[bool], scores: Iterable[float]) -> float:
    y = np.asarray(list(labels), dtype=bool)
    values = np.asarray(list(scores), dtype=float)
    positive = values[y]
    negative = values[~y]
    if positive.size == 0 or negative.size == 0:
        return float("nan")
    comparisons = positive[:, None] - negative[None, :]
    return float(
        (np.count_nonzero(comparisons > 0) + 0.5 * np.count_nonzero(comparisons == 0))
        / comparisons.size
    )


def fit_logistic(x: np.ndarray, y: np.ndarray) -> Callable[[np.ndarray], np.ndarray]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    center = float(x.mean())
    scale = float(x.std()) or 1.0
    design = np.c_[np.ones_like(x), (x - center) / scale]
    beta = np.zeros(2, dtype=float)
    for _ in range(100):
        eta = np.clip(design @ beta, -30, 30)
        probability = 1 / (1 + np.exp(-eta))
        weights = np.clip(probability * (1 - probability), 1e-6, None)
        hessian = design.T @ (weights[:, None] * design)
        gradient = design.T @ (y - probability)
        try:
            step = np.linalg.solve(hessian + np.eye(2) * 1e-8, gradient)
        except np.linalg.LinAlgError:
            break
        beta += step
        if np.max(np.abs(step)) < 1e-9:
            break

    def predict(values: np.ndarray) -> np.ndarray:
        values = np.asarray(values, dtype=float)
        eta = beta[0] + beta[1] * (values - center) / scale
        return 1 / (1 + np.exp(-np.clip(eta, -30, 30)))

    return predict


def rank_correlation(x: pd.Series, y: pd.Series) -> float:
    return float(x.rank(method="average").corr(y.rank(method="average")))
