"""Build the single three-panel figure for the EACL mechanism section (Scale-up)."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts" / "claim_scaleup_30"

BLUE = "#2563EB"
ORANGE = "#EA580C"
GREEN = "#15803D"
GRAY = "#6B7280"
LIGHT_GRAY = "#D1D5DB"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"required completed-run artifact missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _mean_marker(ax, x: float, values: list[float], color: str) -> None:
    if values:
        ax.scatter(
            [x],
            [statistics.mean(values)],
            marker="D",
            s=54,
            color=color,
            edgecolor="white",
            linewidth=0.7,
            zorder=4,
        )


def plot_retention(ax, indirect_summary: dict) -> None:
    # Plot Literal vs Indirect margin shift
    x_vals = []
    y_vals = []

    # We will use marker_present=False for this plot
    for row in indirect_summary.get("retention_by_cell", []):
        if not row["marker_present"]:
            x_vals.append(row["literal_reference_outcome_effect"])
            y_vals.append(row["outcome_effect"])

    ax.scatter(
        x_vals,
        y_vals,
        s=28,
        color=BLUE,
        alpha=0.78,
        edgecolor="white",
        linewidth=0.5,
        zorder=3,
    )

    # Add y=x line
    min_val = min(min(x_vals), min(y_vals))
    max_val = max(max(x_vals), max(y_vals))
    ax.plot([0, max_val], [0, max_val], color=LIGHT_GRAY, linestyle="--", zorder=1)

    ax.set_xlabel("Literal outcome margin shift")
    ax.set_ylabel("Indirect outcome margin shift")
    ax.set_title("(a) Causal Retention", loc="left", fontweight="bold")


def plot_marker_neutrality(ax, indirect_summary: dict) -> None:
    # Plot Margin (Without Marker) vs Margin (With Marker)
    grouped = defaultdict(dict)
    for row in indirect_summary["outcome_effects"]:
        grouped[row["case_id"]][row["marker_present"]] = row["outcome_effect"]

    x_vals = []
    y_vals = []
    for case_id, margins in grouped.items():
        if False in margins and True in margins:
            x_vals.append(margins[False])
            y_vals.append(margins[True])

    ax.scatter(
        x_vals,
        y_vals,
        s=28,
        color=GREEN,
        alpha=0.78,
        edgecolor="white",
        linewidth=0.5,
        zorder=3,
    )

    # Add y=x line
    min_val = min(min(x_vals), min(y_vals))
    max_val = max(max(x_vals), max(y_vals))
    ax.plot([min_val, max_val], [min_val, max_val], color=LIGHT_GRAY, linestyle="--", zorder=1)

    ax.set_xlabel("Margin shift (Marker absent)")
    ax.set_ylabel("Margin shift (Marker present)")
    ax.set_title("(b) Marker Neutrality", loc="left", fontweight="bold")


def plot_expression(ax, df_generations: pd.DataFrame) -> None:
    # Compute the rate at which parsed_label == trace_outcome
    df_generations["expressed_trace"] = (df_generations["parsed_label"] == df_generations["trace_outcome"]).astype(float)

    grouped = df_generations.groupby(["case_id", "marker_present"])["expressed_trace"].mean().reset_index()
    cases = grouped["case_id"].unique()

    without_vals = []
    with_vals = []

    for case in cases:
        case_data = grouped[grouped["case_id"] == case]
        try:
            val_false = case_data[case_data["marker_present"] == False]["expressed_trace"].values[0]
            val_true = case_data[case_data["marker_present"] == True]["expressed_trace"].values[0]

            ax.plot(
                [0, 1],
                [val_false, val_true],
                color=GRAY,
                alpha=0.55,
                linewidth=1,
                marker="o",
                markersize=4,
            )
            without_vals.append(val_false)
            with_vals.append(val_true)
        except IndexError:
            continue

    if without_vals and with_vals:
        ax.plot(
            [0, 1],
            [statistics.mean(without_vals), statistics.mean(with_vals)],
            color=ORANGE,
            linewidth=2.6,
            marker="D",
            markersize=6,
            markeredgecolor="white",
        )

    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Marker\nabsent", "Marker\npresent"])
    ax.set_ylim(-0.04, 1.04)
    ax.set_ylabel("Trace expression frequency")
    ax.set_title("(c) Deliberation Exit", loc="left", fontweight="bold")


def main() -> None:
    args = parse_args()
    output = args.output_dir

    indirect_summary = load_json(output / "indirect_factorial_summary.json")
    df_generations = pd.read_csv(output / "tables/expression_generations.csv")

    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 160,
        }
    )
    figure, axes = plt.subplots(1, 3, figsize=(10.4, 3.05))
    plot_retention(axes[0], indirect_summary)
    plot_marker_neutrality(axes[1], indirect_summary)
    plot_expression(axes[2], df_generations)

    figure.suptitle(
        "Trace causality decouples internal pressure from final expression",
        y=1.01,
        fontsize=11,
        fontweight="bold",
    )
    figure.tight_layout(w_pad=1.8)

    figures = output / "figures"
    figures.mkdir(parents=True, exist_ok=True)

    figure.savefig(
        figures / "eacl_scaleup_mechanism.png",
        bbox_inches="tight",
    )
    figure.savefig(
        figures / "eacl_scaleup_mechanism.pdf",
        bbox_inches="tight",
    )
    plt.close(figure)
    print(f"Saved figure to {figures / 'eacl_scaleup_mechanism.pdf'}")


if __name__ == "__main__":
    main()
