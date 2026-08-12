"""Plot deliberation-exit frequency from completed generation artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACTS = ROOT / "outputs/hang_eacl_claim_scaleup_20b_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--dpi", type=int, default=300)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = args.artifacts_dir / "tables/expression_generations.csv"
    if not source.exists():
        raise FileNotFoundError(f"required generation table missing: {source}")
    output_dir = args.output_dir or args.artifacts_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    generations = pd.read_csv(source)
    grouped = (
        generations.groupby(["case_id", "marker_present"])["final_channel_found"]
        .mean()
        .reset_index()
    )

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    figure, axis = plt.subplots(figsize=(3.5, 3.5))
    sns.boxplot(
        data=grouped,
        x="marker_present",
        y="final_channel_found",
        color="#F1F5F9",
        width=0.45,
        showfliers=False,
        ax=axis,
        boxprops={"edgecolor": "#94A3B8"},
        whiskerprops={"color": "#94A3B8"},
        capprops={"color": "#94A3B8"},
        medianprops={"color": "#64748B"},
    )
    sns.stripplot(
        data=grouped,
        x="marker_present",
        y="final_channel_found",
        color="#94A3B8",
        alpha=0.6,
        jitter=0.08,
        size=5,
        ax=axis,
    )
    means = grouped.groupby("marker_present")["final_channel_found"].mean()
    axis.plot(
        range(len(means)),
        means.to_numpy(),
        color="#EA580C",
        marker="D",
        markersize=6,
        linewidth=2.5,
        markeredgecolor="white",
        zorder=10,
    )
    axis.set_xticks([0, 1])
    axis.set_xticklabels(["Marker\nabsent", "Marker\npresent"])
    axis.set_ylabel("Deliberation exit frequency")
    axis.set_xlabel("")
    axis.set_ylim(-0.05, 1.05)
    axis.grid(axis="y", linestyle=":", color="#E2E8F0", zorder=0)
    axis.set_axisbelow(True)

    targets = [
        output_dir / "deliberation_exit_frequency.pdf",
        output_dir / "deliberation_exit_frequency.png",
    ]
    figure.tight_layout()
    figure.savefig(targets[0], bbox_inches="tight")
    figure.savefig(targets[1], bbox_inches="tight", dpi=args.dpi)
    plt.close(figure)
    print("\n".join(str(path) for path in targets))


if __name__ == "__main__":
    main()
