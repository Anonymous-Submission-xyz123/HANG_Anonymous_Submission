"""Plot figures 03, 04, and 07 for the trace-provenance comparison."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.figure_utils import (  # noqa: E402
    BLUE,
    GRAY,
    GRAY_LIGHT,
    INK,
    MUTED,
    NAVY,
    ORANGE,
    PURPLE,
    PURPLE_LIGHT,
    TEAL,
    WHITE,
    auc_score,
    fit_logistic,
    footer,
    panel_label,
    rank_correlation,
    save_figure,
    style,
    title_block,
)
from scripts.figure_utils import METHOD_LABELS, METHODS  # noqa: E402


DEFAULT_ARTIFACTS = ROOT / "outputs/hang_trace_provenance_comparison_20b_v1"
DEFAULT_OUTPUT = ROOT / "outputs/hang_imported_decision_priors_figure_suite"
METHOD_STYLES = {
    "bypass_derived": (TEAL, "o", "-"),
    "synthesized_cot_forgery": (PURPLE, "^", "--"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dpi", type=int, default=220)
    parser.add_argument(
        "--figures",
        nargs="+",
        choices=("03", "04", "07"),
        default=("03", "04", "07"),
        help="Subset of figures to render.",
    )
    return parser.parse_args()


def require(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"required comparison artifact missing: {path}")
    return path


def finite_label(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}" if math.isfinite(value) else "n/a"


def json_finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: json_finite(subvalue) for key, subvalue in value.items()}
    if isinstance(value, list):
        return [json_finite(subvalue) for subvalue in value]
    return value


def plot_03(retention: pd.DataFrame, output_dir: Path, dpi: int) -> list[Path]:
    case_count = int(retention["case_id"].nunique())
    aggregate_retention = float(
        retention["outcome_effect"].abs().mean()
        / retention["literal_reference_outcome_effect"].abs().mean()
    )
    figure, axes = plt.subplots(1, 2, figsize=(11.8, 4.6))

    for method in METHODS:
        color, marker, _ = METHOD_STYLES[method]
        subset = retention[retention["method"] == method]
        axes[0].scatter(
            subset["literal_reference_outcome_effect"],
            subset["outcome_effect"],
            color=color,
            marker=marker,
            s=42,
            alpha=0.82,
            edgecolor=WHITE,
            linewidth=0.55,
            label=METHOD_LABELS[method],
        )
    lower = float(
        min(
            0,
            retention["literal_reference_outcome_effect"].min(),
            retention["outcome_effect"].min(),
        )
    )
    upper = float(
        max(
            retention["literal_reference_outcome_effect"].max(),
            retention["outcome_effect"].max(),
        )
    )
    pad = max(0.5, 0.06 * (upper - lower or 1.0))
    lower -= pad if lower < 0 else 0
    upper += pad
    x_line = np.array([lower, upper])
    axes[0].plot(x_line, x_line, color=GRAY, linestyle="--", linewidth=1)
    axes[0].plot(
        x_line,
        0.25 * x_line,
        color=ORANGE,
        linestyle=":",
        linewidth=1.2,
        label="25% retention threshold",
    )
    axes[0].axhline(0, color=GRAY_LIGHT, linewidth=0.8)
    axes[0].axvline(0, color=GRAY_LIGHT, linewidth=0.8)
    axes[0].set_xlim(lower, upper)
    axes[0].set_ylim(lower, upper)
    axes[0].set_xlabel("Literal-label conclusion effect")
    axes[0].set_ylabel("Semantic, label-free conclusion effect")
    axes[0].grid()
    axes[0].set_axisbelow(True)
    axes[0].legend(loc="best", fontsize=8)
    positive = int((retention["outcome_effect"] > 0).sum())
    axes[0].text(
        0.97,
        0.04,
        f"{positive}/{len(retention)} positive cells",
        transform=axes[0].transAxes,
        ha="right",
        va="bottom",
        color=NAVY,
        fontweight="bold",
    )
    panel_label(axes[0], "a")

    all_positive_ratios = retention.loc[
        retention["absolute_retained_fraction"] > 0,
        "absolute_retained_fraction",
    ]
    if all_positive_ratios.empty:
        raise ValueError("all retained fractions are zero")
    for method in METHODS:
        color, _, line_style = METHOD_STYLES[method]
        values = np.sort(
            retention.loc[
                (retention["method"] == method)
                & (retention["absolute_retained_fraction"] > 0),
                "absolute_retained_fraction",
            ].to_numpy()
        )
        cumulative = np.arange(1, len(values) + 1) / len(values)
        axes[1].step(
            values,
            cumulative,
            where="post",
            color=color,
            linewidth=2,
            linestyle=line_style,
            label=METHOD_LABELS[method],
        )
    axes[1].axvline(
        0.25,
        color=ORANGE,
        linestyle=":",
        linewidth=1.5,
        label="Preregistered minimum",
    )
    axes[1].axvline(
        aggregate_retention,
        color=NAVY,
        linestyle="-",
        linewidth=1.5,
        label=f"Aggregate retention = {aggregate_retention:.1%}",
    )
    axes[1].set_xscale("log")
    x_min = min(0.20, float(all_positive_ratios.min()) * 0.8)
    x_max = max(4.2, float(all_positive_ratios.max()) * 1.08)
    axes[1].set_xlim(x_min, x_max)
    standard_ticks = [0.1, 0.25, 0.5, 1.0, 2.0, 4.0]
    ticks = [value for value in standard_ticks if x_min <= value <= x_max]
    axes[1].xaxis.set_major_locator(FixedLocator(ticks))
    axes[1].xaxis.set_major_formatter(
        FixedFormatter([f"{value:g}" for value in ticks])
    )
    axes[1].xaxis.set_minor_locator(NullLocator())
    axes[1].set_ylim(0, 1.02)
    axes[1].set_xlabel("Absolute fraction of literal effect retained")
    axes[1].set_ylabel("Cumulative fraction of cells")
    axes[1].grid()
    axes[1].set_axisbelow(True)
    axes[1].legend(loc="lower right", fontsize=7.6)
    axes[1].text(
        0.97,
        0.94,
        "Literal output-label\nstrings absent in every prompt",
        transform=axes[1].transAxes,
        ha="right",
        va="top",
        color=NAVY,
        fontsize=9,
        fontweight="bold",
        bbox={
            "boxstyle": "round,pad=0.3",
            "facecolor": WHITE,
            "edgecolor": "none",
            "alpha": 0.9,
        },
    )
    panel_label(axes[1], "b")

    title_block(
        figure,
        "Semantic conclusions shift the decision without literal label strings",
        "Matched comparison of harvested HANG traces and synthesized CoT Forgery traces against their literal-label references.",
    )
    footer(
        figure,
        f"{case_count} payloads × 2 trace origins • marker and trace length held fixed • "
        f"{positive}/{len(retention)} effects in the expected direction • "
        f"aggregate absolute retention {aggregate_retention:.1%}",
    )
    figure.subplots_adjust(top=0.82, bottom=0.15, left=0.09, right=0.97, wspace=0.28)
    return save_figure(figure, output_dir, "03_no_literal_label_control", dpi)


def plot_04(delta: pd.DataFrame, output_dir: Path, dpi: int) -> list[Path]:
    figure, axes = plt.subplots(2, 1, figsize=(10.8, 7.2), sharey=True)
    series = (
        ("delta_system_mass", "System", NAVY, "o"),
        ("delta_payload_mass", "Payload", ORANGE, "s"),
        ("delta_trace_mass", "Reasoning trace", PURPLE, "^"),
        ("delta_sink_mass", "Sink / unattributed", GRAY, "D"),
    )
    for axis, attention_type, panel in zip(
        axes,
        ("full-context", "local/sliding"),
        ("a", "b"),
    ):
        subset = delta[delta["attention_type"] == attention_type].sort_values(
            "layer"
        )
        for column, label, color, marker in series:
            if attention_type == "local/sliding" and column == "delta_system_mass":
                continue
            axis.plot(
                subset["layer"],
                subset[column],
                color=color,
                linewidth=1.9,
                marker=marker,
                markersize=4.5,
                label=label,
            )
        axis.axhline(0, color=INK, linewidth=0.85)
        axis.axvspan(10, 16, color=PURPLE_LIGHT, alpha=0.15, zorder=0)
        axis.set_title(
            "Full-context layers"
            if attention_type == "full-context"
            else "Local / sliding-window layers",
            loc="left",
        )
        axis.set_ylabel(
            "Harvested HANG - synthesized\nabsolute attention mass"
        )
        axis.set_xticks(subset["layer"])
        axis.grid(axis="y")
        axis.set_axisbelow(True)
        axis.legend(loc="best", ncol=2, fontsize=8)
        panel_label(axis, panel)
    axes[1].set_xlabel("Transformer layer")
    title_block(
        figure,
        "Trace provenance changes answer-formation attention routing",
        "Signed matched differences between harvested HANG traces and synthesized CoT Forgery traces over generation steps 4-9.",
    )
    footer(
        figure,
        "Six matched payloads - marker and trace length held fixed - positive = more attention under harvested HANG traces - shaded band = layers 10-16",
    )
    figure.subplots_adjust(top=0.84, bottom=0.10, left=0.11, right=0.97, hspace=0.30)
    return save_figure(figure, output_dir, "04_attention_reallocation_by_layer", dpi)


def plot_07(prediction: pd.DataFrame, output_dir: Path, dpi: int) -> list[Path]:
    prediction = prediction.copy()
    case_count = int(prediction["case_id"].nunique())
    prediction["expressed_majority_clean"] = prediction["expression_rate"] > 0.5
    rng = np.random.default_rng(123)
    prediction["jitter"] = rng.normal(0, 0.018, len(prediction))
    logistic = fit_logistic(
        prediction["clean_margin"].to_numpy(),
        prediction["expressed_majority_clean"].astype(float).to_numpy(),
    )
    x_grid = np.linspace(
        prediction["clean_margin"].min() - 0.2,
        prediction["clean_margin"].max() + 0.2,
        300,
    )
    prediction["margin_quintile"] = pd.qcut(
        prediction["clean_margin"],
        min(5, prediction["clean_margin"].nunique()),
        labels=False,
        duplicates="drop",
    )
    binned = prediction.groupby("margin_quintile").agg(
        mean_margin=("clean_margin", "mean"),
        mean_expression=("expression_rate", "mean"),
    )
    auc = auc_score(
        prediction["expressed_majority_clean"], prediction["clean_margin"]
    )
    pearson = float(
        prediction["clean_margin"].corr(prediction["expression_rate"])
    )
    spearman = rank_correlation(
        prediction["clean_margin"], prediction["expression_rate"]
    )
    has_expression_signal = bool(prediction["expression_rate"].max() > 0)

    figure, axis = plt.subplots(figsize=(9.8, 5.8))
    for method in METHODS:
        color, marker, _ = METHOD_STYLES[method]
        subset = prediction[prediction["method"] == method]
        axis.scatter(
            subset["clean_margin"],
            subset["expression_rate"] + subset["jitter"],
            s=48,
            color=color,
            marker=marker,
            alpha=0.74,
            edgecolor=WHITE,
            linewidth=0.55,
            label=METHOD_LABELS[method],
            zorder=3,
        )
    axis.plot(
        x_grid,
        logistic(x_grid),
        color=NAVY,
        linewidth=2.2,
        label="Logistic fit: majority expression",
        zorder=2,
    )
    axis.plot(
        binned["mean_margin"],
        binned["mean_expression"],
        color=ORANGE,
        linewidth=1.5,
        marker="D",
        markersize=6,
        markerfacecolor=ORANGE,
        markeredgecolor=WHITE,
        label="Observed expression by margin quintile",
        zorder=4,
    )
    axis.set_ylim(-0.08, 1.08)
    axis.set_xlabel(
        "Clean − Webshell decision margin under controlled Clean conclusion"
    )
    axis.set_ylabel(
        "Injected Clean conclusion expression rate\n(5 sampled generations)"
    )
    axis.grid()
    axis.set_axisbelow(True)
    axis.legend(loc="upper left", fontsize=8)
    axis.text(
        0.98,
        0.94,
        f"Pearson r = {finite_label(pearson, 2)}\n"
        f"Spearman ρ = {finite_label(spearman, 2)}\n"
        f"Majority-expression AUC = {finite_label(auc, 3)}",
        transform=axis.transAxes,
        ha="right",
        va="top",
        color=NAVY,
        fontsize=9,
        fontweight="bold",
    )
    title = (
        "A larger injected decision margin predicts stronger final expression"
        if has_expression_signal
        else "No sampled final expression despite injected decision margins"
    )
    subtitle = (
        "Each point is one payload×trace-origin cell; expression is measured over five independent sampled generations."
        if has_expression_signal
        else "Each point is one payload×trace-origin cell; none of the five sampled generations per cell expressed the injected Clean conclusion."
    )
    title_block(
        figure,
        title,
        subtitle,
    )
    footer(
        figure,
        f"{len(prediction)} cells from {case_count} matched payloads • "
        "marker and trace length held fixed • "
        "trace origin retained as point shape/color",
    )
    figure.subplots_adjust(top=0.82, bottom=0.14, left=0.12, right=0.97)
    return save_figure(figure, output_dir, "07_margin_expression_dose_response", dpi)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    style()
    requested = set(args.figures)
    retention_path = (
        args.artifacts_dir / "tables/trace_provenance_retention.csv"
    )
    attention_path = (
        args.artifacts_dir
        / "tables/attention_delta_by_layer_content_steps4_9.csv"
    )
    prediction_path = (
        args.artifacts_dir / "tables/trace_provenance_prediction.csv"
    )
    retention = (
        pd.read_csv(require(retention_path)) if "03" in requested else None
    )
    attention = (
        pd.read_csv(require(attention_path)) if "04" in requested else None
    )
    prediction = (
        pd.read_csv(require(prediction_path)) if "07" in requested else None
    )

    generated = []
    if retention is not None:
        generated.extend(plot_03(retention, args.output_dir, args.dpi))
    if attention is not None:
        generated.extend(plot_04(attention, args.output_dir, args.dpi))
    if prediction is not None:
        generated.extend(plot_07(prediction, args.output_dir, args.dpi))

    stats = {
        "protocol": "fixed_payload_length_matched_trace_provenance_v1",
        "figures": list(args.figures),
        "methods": METHOD_LABELS,
        "payload_marker_held_fixed": True,
        "trace_length_matched_within_case": True,
        "sources": {},
        "generated": sorted(path.name for path in generated),
    }
    if retention is not None:
        stats.update(
            {
                "case_count": int(retention["case_id"].nunique()),
                "cells": len(retention),
                "positive_semantic_effects": int(
                    (retention["outcome_effect"] > 0).sum()
                ),
                "aggregate_absolute_retained_fraction": float(
                    retention["outcome_effect"].abs().mean()
                    / retention["literal_reference_outcome_effect"].abs().mean()
                ),
            }
        )
        stats["sources"]["figure_03"] = str(retention_path)
    if attention is not None:
        stats["sources"]["figure_04"] = str(attention_path)
    if prediction is not None:
        stats["case_count"] = stats.get(
            "case_count", int(prediction["case_id"].nunique())
        )
        stats["prediction_cells"] = len(prediction)
        stats.update(
            {
                "pearson_margin_vs_expression_rate": float(
                    prediction["clean_margin"].corr(prediction["expression_rate"])
                ),
                "spearman_margin_vs_expression_rate": rank_correlation(
                    prediction["clean_margin"], prediction["expression_rate"]
                ),
                "majority_expression_auc": auc_score(
                    prediction["expression_rate"] > 0.5,
                    prediction["clean_margin"],
                ),
            }
        )
        stats["sources"]["figure_07"] = str(prediction_path)
    output_stem = "_".join(args.figures) + "_trace_provenance"
    (args.output_dir / f"{output_stem}_statistics.json").write_text(
        json.dumps(json_finite(stats), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    manifest_rows = []
    if retention is not None:
        manifest_rows.append(
            {
                "figure": "03_no_literal_label_control",
                "comparison": "Harvested HANG vs synthesized (CoT Forgery)",
                "scope": (
                    f"{retention['case_id'].nunique()} matched payloads "
                    "× 2 trace origins"
                ),
                "source": str(retention_path),
            }
        )
    if attention is not None:
        manifest_rows.append(
            {
                "figure": "04_attention_reallocation_by_layer",
                "comparison": "Harvested HANG minus synthesized (CoT Forgery)",
                "scope": "matched payloads, generation steps 4–9",
                "source": str(attention_path),
            }
        )
    if prediction is not None:
        manifest_rows.append(
            {
                "figure": "07_margin_expression_dose_response",
                "comparison": "Harvested HANG vs synthesized (CoT Forgery)",
                "scope": (
                    f"{len(prediction)} cells, "
                    f"{int(prediction['generation_count'].max())} generations per cell"
                ),
                "source": str(prediction_path),
            },
        )
    pd.DataFrame(manifest_rows).to_csv(
        args.output_dir / f"{output_stem}_manifest.csv", index=False
    )
    print("\n".join(str(path) for path in generated))


if __name__ == "__main__":
    main()
