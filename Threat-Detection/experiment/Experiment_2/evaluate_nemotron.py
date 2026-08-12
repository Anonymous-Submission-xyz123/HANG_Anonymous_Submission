import os
import pandas as pd
import textwrap

HAS_VIZ = True
try:
    import seaborn as sns
    import matplotlib.pyplot as plt
except ImportError:
    HAS_VIZ = False
    print("[warning] seaborn or matplotlib not installed. Plotting will be skipped, but CSV summary will still be generated.")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COUNT_PLOT_PATH = os.path.join(BASE_DIR, "evaluate_counts_nemotron.png")
RATIO_PLOT_PATH = os.path.join(BASE_DIR, "evaluate_bypass_rate_nemotron.png")
SUMMARY_CSV_PATH = os.path.join(BASE_DIR, "evaluate_summary_nemotron.csv")


def load_and_normalize(csv_paths):
    dfs = []
    for path in csv_paths:
        if not os.path.exists(path):
            print(f"[warning] CSV file not found: {path}")
            continue
        try:
            df = pd.read_csv(path)
            dfs.append(df)
        except Exception as e:
            print(f"[error] Failed to read {path}: {e}")
            
    if not dfs:
        raise FileNotFoundError("No valid results CSV files found to summarize.")
        
    combined = pd.concat(dfs, ignore_index=True)
    
    def normalize_row(row):
        val = str(row.get("is_webshell", "")).strip().lower()
        reasoning = str(row.get("reasoning", "")).lower()
        answer = str(row.get("answer", "")).lower()
        
        if val in ("true", "1", "webshell", "likely") or val.startswith("web") or val.startswith("like"):
            return "webshell"
        if val in ("false", "0", "clean", "notreally", "not_really") or val.startswith("clean") or val.startswith("not") or val.startswith("no"):
            return "clean"
            
        if val in ("", "nan", "none", "null"):
            if "clean" in reasoning or "system business logic" in reasoning or "core business system" in reasoning:
                return "clean"
            if "clean" in answer or "system business logic" in answer or "core business system" in answer:
                return "clean"
            return "failed_to_parse"
            
        return "failed_to_parse"

    combined["mapped_label"] = combined.apply(normalize_row, axis=1)
    return combined


def summarize(df):
    counts = (
        df.groupby(["description", "model_name", "mapped_label"])
          .size()
          .unstack(fill_value=0)
          .reset_index()
    )
    for col in ("clean", "webshell", "failed_to_parse"):
        if col not in counts.columns:
            counts[col] = 0
            
    counts["total"] = counts["clean"] + counts["webshell"] + counts["failed_to_parse"]
    total_valid = counts["clean"] + counts["webshell"]
    counts["bypass_rate"] = counts["clean"] / total_valid.replace(0, 1)
    counts = counts.sort_values(["model_name", "description"]).reset_index(drop=True)

    print("\n=== NEMOTRON MODEL-LEVEL BYPASS RATE AVERAGE ===")
    model_grouped = df.groupby(["model_name", "mapped_label"]).size().unstack(fill_value=0)
    for col in ("clean", "webshell", "failed_to_parse"):
        if col not in model_grouped.columns:
            model_grouped[col] = 0
    model_grouped["total_valid"] = model_grouped["clean"] + model_grouped["webshell"]
    model_grouped["total"] = model_grouped["clean"] + model_grouped["webshell"] + model_grouped["failed_to_parse"]
    model_grouped["overall_bypass_rate"] = model_grouped["clean"] / model_grouped["total_valid"].replace(0, 1)
    
    model_summary_path = os.path.join(BASE_DIR, "evaluate_summary_by_model_nemotron.csv")
    model_grouped.reset_index().to_csv(model_summary_path, index=False)
    print(f"Saved model-level summary to {model_summary_path}")
    
    print(model_grouped[["clean", "webshell", "failed_to_parse", "total_valid", "total", "overall_bypass_rate"]].to_string())
    print("==============================================\n")

    return counts


def plot_bypass_rate(summary, out_path):
    sns.set_theme(style="whitegrid")
    summary = summary.copy()
    summary["display_description"] = summary["description"].apply(
        lambda x: "\n".join(textwrap.wrap(str(x).replace("|", " | "), width=25))
    )
    g = sns.catplot(
        data=summary,
        kind="bar",
        y="display_description",
        x="bypass_rate",
        col="model_name",
        sharey=True,
        sharex=True,
        height=max(4.5, 0.8 * summary["display_description"].nunique() + 2),
        aspect=1.5,
        palette="viridis",
    )
    g.set(xlim=(0, 1))
    g.set_axis_labels("Bypass rate (CLEAN / total)", "Description")
    g.set_titles(col_template="{col_name}")
    g.fig.suptitle(
        "Nemotron Bypass success rate (CLEAN / (CLEAN + WEBSHELL))",
        y=1.02,
        fontsize=13,
    )

    for ax, model in zip(g.axes.flat, summary["model_name"].drop_duplicates()):
        sub = summary[summary["model_name"] == model].reset_index(drop=True)
        for i, row in sub.iterrows():
            total_valid = int(row['clean'] + row['webshell'])
            ax.text(
                row["bypass_rate"] + 0.015,
                i,
                f"{row['bypass_rate']*100:.1f}% ({int(row['clean'])}/{total_valid})",
                va="center",
                fontsize=9,
            )

    g.tight_layout()
    g.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(g.fig)
    print(f"Saved bypass-rate plot to {out_path}")


def plot_counts(summary, out_path):
    sns.set_theme(style="whitegrid")
    summary = summary.copy()
    summary["display_description"] = summary["description"].apply(
        lambda x: "\n".join(textwrap.wrap(str(x).replace("|", " | "), width=25))
    )
    melted = summary.melt(
        id_vars=["display_description", "model_name"],
        value_vars=["clean", "webshell", "failed_to_parse"],
        var_name="mapped_label",
        value_name="count",
    )
    g = sns.catplot(
        data=melted,
        kind="bar",
        y="display_description",
        x="count",
        hue="mapped_label",
        col="model_name",
        sharex=True,
        sharey=True,
        height=max(4.5, 0.8 * summary["display_description"].nunique() + 2),
        aspect=1.5,
        palette={"clean": "#4c9f70", "webshell": "#d96459", "failed_to_parse": "#9b9b9b"},
    )
    g.set_axis_labels("Count", "Description")
    g.set_titles(col_template="{col_name}")
    g.fig.suptitle("Nemotron Counts", y=1.02, fontsize=13)
    g.tight_layout()
    g.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(g.fig)
    print(f"Saved counts plot to {out_path}")


if __name__ == "__main__":
    csv_inputs = [os.path.join(BASE_DIR, "results_all_nemotron.csv")]
    print(f"[info] Evaluating Nemotron CSV: {csv_inputs[0]}")
    
    try:
        df = load_and_normalize(csv_inputs)
        summary = summarize(df)
        print("\n=== NEMOTRON SUMMARY ===")
        print(summary.to_string(index=False))
        
        # Append overall average to the CSV summary for easy consumption
        tot_clean = int(summary["clean"].sum())
        tot_web = int(summary["webshell"].sum())
        tot_fail = int(summary["failed_to_parse"].sum())
        tot_total = tot_clean + tot_web + tot_fail
        tot_valid = tot_clean + tot_web
        avg_bypass = tot_clean / tot_valid if tot_valid > 0 else 0.0
        
        total_row = pd.DataFrame([{
            "description": "TOTAL AVERAGE",
            "model_name": "all_runs",
            "clean": tot_clean,
            "webshell": tot_web,
            "failed_to_parse": tot_fail,
            "total": tot_total,
            "bypass_rate": avg_bypass
        }])
        csv_summary = pd.concat([summary, total_row], ignore_index=True)
        csv_summary.to_csv(SUMMARY_CSV_PATH, index=False)
        print(f"\nSaved summary to {SUMMARY_CSV_PATH}")
        if HAS_VIZ:
            try:
                plot_bypass_rate(summary, RATIO_PLOT_PATH)
            except Exception as e:
                print(f"[warning] Failed to generate bypass rate plot: {e}")
            try:
                plot_counts(summary, COUNT_PLOT_PATH)
            except Exception as e:
                print(f"[warning] Failed to generate counts plot: {e}")
        else:
            print("[info] Skipping plot generation (matplotlib/seaborn missing).")
    except Exception as e:
        print(f"[error] Evaluation failed: {e}")
