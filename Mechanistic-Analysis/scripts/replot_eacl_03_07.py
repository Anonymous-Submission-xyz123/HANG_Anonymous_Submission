import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator

ROOT = Path("/home/huynp2/gpt_oss_lens")
sys.path.insert(0, str(ROOT))

from scripts.plot_imported_decision_priors_suite import (
    BLUE, GRAY, GRAY_LIGHT, INK, MUTED, NAVY, ORANGE, PURPLE, PURPLE_LIGHT, TEAL, WHITE,
    auc_score, fit_logistic, rank_correlation, save_figure, style
)
METHODS = ("bypass_derived", "synthesized_cot_forgery")
METHOD_LABELS = {
    "bypass_derived": "Bypass-derived (our method)",
    "synthesized_cot_forgery": "Synthesized (CoT Forgery)",
}

METHOD_STYLES = {
    "bypass_derived": (TEAL, "o", "-"),
    "synthesized_cot_forgery": (PURPLE, "^", "--"),
}

def finite_label(value: float, digits: int = 3) -> str:
    import math
    return f"{value:.{digits}f}" if math.isfinite(value) else "n/a"

def plot_03_eacl(retention: pd.DataFrame, output_dir: Path, dpi: int) -> list[Path]:
    style()
    # 1 column EACL width is approx 3.03 inches. Using 3.3 for a bit of padding.
    figure, ax = plt.subplots(figsize=(4.0, 3.3))

    for method in METHODS:
        color, marker, _ = METHOD_STYLES[method]
        subset = retention[retention["method"] == method]
        ax.scatter(
            subset["literal_reference_outcome_effect"],
            subset["outcome_effect"],
            color=color,
            marker=marker,
            s=20,
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
    
    ax.plot(x_line, x_line, color=GRAY, linestyle="--", linewidth=1)

    ax.axhline(0, color=GRAY_LIGHT, linewidth=0.8)
    ax.axvline(0, color=GRAY_LIGHT, linewidth=0.8)
    ax.set_xlim(lower, upper)
    ax.set_ylim(lower, upper)
    ax.set_xlabel("Literal-label conclusion effect", fontsize=10)
    ax.set_ylabel("Semantic, label-free conclusion effect", fontsize=10)
    ax.tick_params(axis='both', which='major', labelsize=9)
    ax.grid()
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=7)
    

    
    figure.subplots_adjust(top=0.98, bottom=0.15, left=0.16, right=0.98)
    return save_figure(figure, output_dir, "03_no_literal_label_control_left_only", dpi)

def plot_07_eacl(prediction: pd.DataFrame, output_dir: Path, dpi: int) -> list[Path]:
    style()
    prediction = prediction.copy()
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
    auc = auc_score(prediction["expressed_majority_clean"], prediction["clean_margin"])
    pearson = float(prediction["clean_margin"].corr(prediction["expression_rate"]))
    spearman = rank_correlation(prediction["clean_margin"], prediction["expression_rate"])

    figure, ax = plt.subplots(figsize=(5.0, 3.3))
    for method in METHODS:
        color, marker, _ = METHOD_STYLES[method]
        subset = prediction[prediction["method"] == method]
        ax.scatter(
            subset["clean_margin"],
            subset["expression_rate"] + subset["jitter"],
            s=20,
            color=color,
            marker=marker,
            alpha=0.74,
            edgecolor=WHITE,
            linewidth=0.55,
            label=METHOD_LABELS[method],
            zorder=3,
        )
    
    ax.plot(
        x_grid,
        logistic(x_grid),
        color=NAVY,
        linewidth=2,
        label="Logit fit",
        zorder=2,
    )
    ax.plot(
        binned["mean_margin"],
        binned["mean_expression"],
        color=ORANGE,
        linewidth=1.2,
        marker="D",
        markersize=4,
        markerfacecolor=ORANGE,
        markeredgecolor=WHITE,
        label="Obs. quintile",
        zorder=4,
    )
    ax.set_ylim(-0.08, 1.08)
    ax.set_xlabel("Decision margin", fontsize=11)
    ax.set_ylabel("Injected conclusion expr. rate", fontsize=11)
    ax.tick_params(axis='both', which='major', labelsize=10)
    ax.grid()
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=7)
    ax.text(
        0.98,
        0.04,
        f"r = {finite_label(pearson, 2)}\n"
        f"ρ = {finite_label(spearman, 2)}\n"
        f"AUC = {finite_label(auc, 3)}",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        color=NAVY,
        fontsize=8,
        fontweight="bold",
    )
    
    figure.subplots_adjust(top=0.98, bottom=0.15, left=0.15, right=0.98)
    return save_figure(figure, output_dir, "07_margin_expression_dose_response_eacl", dpi)

def main():
    artifacts_dir = ROOT / "outputs/hang_trace_provenance_comparison_20b_n30_v2_lenient_parser"
    output_dir = ROOT / "outputs/hang_imported_decision_priors_figure_suite_n30_lenient_parser_eacl"
    output_dir.mkdir(parents=True, exist_ok=True)

    retention_path = artifacts_dir / "tables/trace_provenance_retention.csv"
    prediction_path = artifacts_dir / "tables/trace_provenance_prediction.csv"

    retention = pd.read_csv(retention_path)
    prediction = pd.read_csv(prediction_path)

    p1 = plot_03_eacl(retention, output_dir, 300)
    p2 = plot_07_eacl(prediction, output_dir, 300)
    
    print(f"Saved EACL formatted plots to {output_dir}")
    print("Files:")
    for p in p1 + p2:
        print(p)

if __name__ == "__main__":
    main()
