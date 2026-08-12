import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

ROOT = Path("/home/huynp2/gpt_oss_lens")
sys.path.insert(0, str(ROOT))
output = ROOT / "outputs/hang_eacl_claim_scaleup_20b_v1"

df_generations = pd.read_csv(output / "tables/expression_generations.csv")
grouped = df_generations.groupby(["case_id", "marker_present"])["final_channel_found"].mean().reset_index()

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

fig, ax = plt.subplots(figsize=(3.5, 3.5))

sns.boxplot(
    data=grouped,
    x="marker_present",
    y="final_channel_found",
    color="#F1F5F9", 
    width=0.45,
    showfliers=False,
    ax=ax,
    boxprops=dict(edgecolor="#94A3B8"),
    whiskerprops=dict(color="#94A3B8"),
    capprops=dict(color="#94A3B8"),
    medianprops=dict(color="#64748B")
)

sns.stripplot(
    data=grouped,
    x="marker_present",
    y="final_channel_found",
    color="#94A3B8",
    alpha=0.6,
    jitter=0.08,
    size=5,
    ax=ax
)

means = grouped.groupby("marker_present")["final_channel_found"].mean()
ax.plot(
    [0, 1], 
    means, 
    color="#EA580C", 
    marker="D", 
    markersize=6, 
    linewidth=2.5, 
    markeredgecolor="white",
    zorder=10
)

ax.set_xticks([0, 1])
ax.set_xticklabels(["Marker\nabsent", "Marker\npresent"])
ax.set_ylabel("Deliberation exit frequency")
ax.set_xlabel("")
ax.set_ylim(-0.05, 1.05)

ax.grid(axis='y', linestyle=":", color="#E2E8F0", zorder=0)
ax.set_axisbelow(True)

figures = output / "figures"
figures.mkdir(parents=True, exist_ok=True)
pdf_path = figures / "deliberation_exit_frequency.pdf"
png_path = figures / "deliberation_exit_frequency.png"

fig.tight_layout()
fig.savefig(pdf_path, bbox_inches="tight")
fig.savefig(png_path, bbox_inches="tight", dpi=300)

print(f"Saved PDF to {pdf_path}")
print(f"Saved PNG to {png_path}")
