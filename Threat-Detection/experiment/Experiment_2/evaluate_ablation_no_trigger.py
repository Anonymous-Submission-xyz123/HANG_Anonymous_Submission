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
RESULTS_CSV_PATH = os.path.join(BASE_DIR, "results_ablation_no_trigger.csv")
SUMMARY_CSV_PATH = os.path.join(BASE_DIR, "evaluate_summary_ablation_no_trigger.csv")
MODEL_SUMMARY_PATH = os.path.join(BASE_DIR, "evaluate_summary_by_model_ablation_no_trigger.csv")
COUNT_PLOT_PATH = os.path.join(BASE_DIR, "evaluate_counts_ablation_no_trigger.png")
RATIO_PLOT_PATH = os.path.join(BASE_DIR, "evaluate_bypass_rate_ablation_no_trigger.png")

def load_and_normalize(csv_path):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Ablation no trigger results file not found: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise IOError(f"Failed to read {csv_path}: {e}")
        
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

    df["mapped_label"] = df.apply(normalize_row, axis=1)
    return df

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

    print("\n=== ABLATION NO TRIGGER MODEL-LEVEL BYPASS RATE AVERAGE ===")
    model_grouped = df.groupby(["model_name", "mapped_label"]).size().unstack(fill_value=0)
    for col in ("clean", "webshell", "failed_to_parse"):
        if col not in model_grouped.columns:
            model_grouped[col] = 0
    model_grouped["total_valid"] = model_grouped["clean"] + model_grouped["webshell"]
    model_grouped["total"] = model_grouped["clean"] + model_grouped["webshell"] + model_grouped["failed_to_parse"]
    model_grouped["overall_bypass_rate"] = model_grouped["clean"] / model_grouped["total_valid"].replace(0, 1)
    
    model_grouped.reset_index().to_csv(MODEL_SUMMARY_PATH, index=False)
    print(f"Saved model-level summary to {MODEL_SUMMARY_PATH}")
    print(model_grouped[["clean", "webshell", "failed_to_parse", "total_valid", "total", "overall_bypass_rate"]].to_string())
    print("==========================================================\n")

    model_grouped_df = model_grouped.reset_index()
    # Add a row to the end of counts dataframe that represents the overall summary for readability
    summary_row = {
        "description": "OVERALL MODEL AVERAGE",
        "model_name": model_grouped_df.iloc[0]["model_name"] if not model_grouped_df.empty else "",
        "clean": model_grouped_df.iloc[0]["clean"] if not model_grouped_df.empty else 0,
        "webshell": model_grouped_df.iloc[0]["webshell"] if not model_grouped_df.empty else 0,
        "failed_to_parse": model_grouped_df.iloc[0]["failed_to_parse"] if not model_grouped_df.empty else 0,
        "total": model_grouped_df.iloc[0]["total"] if not model_grouped_df.empty else 0,
        "bypass_rate": model_grouped_df.iloc[0]["overall_bypass_rate"] if not model_grouped_df.empty else 0.0
    }
    counts = pd.concat([counts, pd.DataFrame([summary_row])], ignore_index=True)
    return counts

def plot_bypass_rate(summary, out_path):
    sns.set_theme(style="whitegrid")
    summary = summary.copy()
    summary["display_description"] = summary["description"].apply(
        lambda x: "\n".join(textwrap.wrap(str(x).replace("|", " | "), width=25))
    )
    g = sns.catplot(
        data=summary,
        x="display_description",
        y="bypass_rate",
        hue="model_name",
        kind="bar",
        height=6,
        aspect=1.5,
        palette="viridis"
    )
    g.set_axis_labels("Experiment Setup", "Bypass Rate")
    g.fig.suptitle("Bypass Rate by Experiment Setup (Ablation No Trigger)", y=1.02, fontsize=16)
    g.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"Saved bypass rate plot to {out_path}")
    plt.close()

def plot_counts(summary, out_path):
    sns.set_theme(style="whitegrid")
    df_melt = summary.melt(
        id_vars=["description", "model_name"],
        value_vars=["clean", "webshell", "failed_to_parse"],
        var_name="category",
        value_name="count"
    )
    df_melt["display_description"] = df_melt["display_description"].apply(
        lambda x: "\n".join(textwrap.wrap(str(x).replace("|", " | "), width=25))
    )
    
    g = sns.catplot(
        data=df_melt,
        x="display_description",
        y="count",
        hue="category",
        col="model_name",
        kind="bar",
        height=6,
        aspect=1.2,
        palette="muted"
    )
    g.set_axis_labels("Experiment Setup", "Sample Count")
    g.fig.suptitle("Classification Distribution (Ablation No Trigger)", y=1.05, fontsize=16)
    g.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"Saved counts plot to {out_path}")
    plt.close()

if __name__ == "__main__":
    try:
        combined = load_and_normalize(RESULTS_CSV_PATH)
        summary = summarize(combined)
        summary.to_csv(SUMMARY_CSV_PATH, index=False)
        print(f"Saved detailed summary to {SUMMARY_CSV_PATH}")
        
        if HAS_VIZ:
            try:
                plot_summary = summary[summary["description"] != "OVERALL MODEL AVERAGE"]
                plot_bypass_rate(plot_summary, RATIO_PLOT_PATH)
                plot_counts(plot_summary, COUNT_PLOT_PATH)
            except Exception as e:
                print(f"[error] Failed to generate plots: {e}")
        else:
            print("[info] Skipping plot generation (matplotlib/seaborn missing).")
    except Exception as e:
        print(f"Error executing evaluation: {e}")
