"""
Data aggregation, table exporter, and figure plotter for HANG experiment analysis.
"""

import json
import os
from typing import Dict, List, Optional, Any
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from .schemas import RunRecord, AnalysisMetrics
from .cache import HANGCacheManager
from .metrics import HANGMetricsCalculator


class HANGAnalysisExporter:
    def __init__(self, runs_dir: str = "outputs/runs", tables_dir: str = "outputs/tables"):
        self.runs_dir = runs_dir
        self.tables_dir = tables_dir
        os.makedirs(tables_dir, exist_ok=True)

    def load_all_run_records(self) -> List[Dict[str, Any]]:
        records = []
        if not os.path.exists(self.runs_dir):
            return records

        for root, _, files in os.walk(self.runs_dir):
            for file in files:
                if file.endswith(".jsonl"):
                    fpath = os.path.join(root, file)
                    with open(fpath, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                records.append(json.loads(line))
        return records

    def export_summary_table(self) -> pd.DataFrame:
        records = self.load_all_run_records()
        if not records:
            df = pd.DataFrame()
            return df

        df = pd.DataFrame(records)
        csv_path = os.path.join(self.tables_dir, "runs_summary.csv")
        parquet_path = os.path.join(self.tables_dir, "runs_summary.parquet")

        # Select display columns
        cols = [
            "run_id", "base_prompt_id", "condition", "target_model",
            "generation_seed", "attack_success", "evaluator_score",
            "evaluator_output", "generated_text"
        ]
        export_df = df[[c for c in cols if c in df.columns]]

        export_df.to_csv(csv_path, index=False)
        try:
            export_df.to_parquet(parquet_path, index=False)
        except Exception:
            pass  # Fallback if pyarrow is absent

        print(f"[HANGAnalysisExporter] Exported summary table to {csv_path} ({len(export_df)} rows).")
        return export_df

    def export_saved_metrics(self, cache_dir: str) -> pd.DataFrame:
        """Rebuild per-run mechanism metrics without running a model."""
        cache_manager = HANGCacheManager(cache_dir)
        rows = []
        for raw_record in self.load_all_run_records():
            record = RunRecord.from_dict(raw_record)
            metrics = HANGMetricsCalculator.compute_saved_run_metrics(
                record, cache_manager
            )
            row = metrics.to_dict()
            row["run_id"] = record.run_id
            rows.append(row)
        result = pd.DataFrame(rows)
        if not result.empty:
            result.to_json(
                os.path.join(self.tables_dir, "mechanism_metrics.jsonl"),
                orient="records",
                lines=True,
            )
            flat = result.drop(
                columns=["cosine_similarity_trace_answer", "layerwise_logit_shifts"],
                errors="ignore",
            )
            flat.to_csv(
                os.path.join(self.tables_dir, "mechanism_metrics.csv"),
                index=False,
            )
        return result


class HANGPlotter:
    def __init__(self, figures_dir: str = "outputs/figures"):
        self.figures_dir = figures_dir
        os.makedirs(figures_dir, exist_ok=True)

        sns.set_theme(style="whitegrid")
        plt.rcParams.update({
            'font.size': 12,
            'axes.labelsize': 14,
            'axes.titlesize': 16,
            'xtick.labelsize': 12,
            'ytick.labelsize': 12,
            'figure.titlesize': 18
        })

    def plot_attack_success_rates(self, df: pd.DataFrame, filename: str = "attack_success_rate.png"):
        if df.empty or "condition" not in df.columns or "attack_success" not in df.columns:
            print("[HANGPlotter] Skipping attack success plot: empty DataFrame or missing columns.")
            return

        df_copy = df.copy()
        df_copy["attack_success_pct"] = df_copy["attack_success"].astype(int) * 100

        plt.figure(figsize=(8, 6))
        ax = sns.barplot(
            data=df_copy,
            x="condition",
            y="attack_success_pct",
            hue="condition",
            palette="viridis",
            order=["no_trace", "matched_trace", "unrelated_trace"],
            legend=False,
            capsize=0.1
        )

        plt.title("HANG Target Attack Success Rate by Condition", pad=15)
        plt.xlabel("Prompt Condition")
        plt.ylabel("Attack Success Rate (%)")
        plt.ylim(0, 105)

        for p in ax.patches:
            height = p.get_height()
            if not pd.isna(height):
                ax.annotate(f'{height:.1f}%',
                            (p.get_x() + p.get_width() / 2., height),
                            ha='center', va='bottom', xytext=(0, 5),
                            textcoords='offset points')

        plt.tight_layout()
        save_path = os.path.join(self.figures_dir, filename)
        plt.savefig(save_path, dpi=300)
        plt.savefig(save_path.replace(".png", ".pdf"))
        plt.close()
        print(f"[HANGPlotter] Saved plot to {save_path}")

    def plot_attention_routing(self, layer_attn_df: pd.DataFrame, filename: str = "attention_routing_by_layer.png"):
        if layer_attn_df.empty or "layer" not in layer_attn_df.columns:
            print("[HANGPlotter] Skipping attention routing plot: empty DataFrame.")
            return

        plt.figure(figsize=(10, 6))
        sns.lineplot(
            data=layer_attn_df,
            x="layer",
            y="mean_attention_mass",
            hue="condition",
            marker="o",
            linewidth=2.5
        )
        plt.title("Trace Attention Routing Mass Across Transformer Layers", pad=15)
        plt.xlabel("Layer Index")
        plt.ylabel("Mean Attention Mass on Trace Span")
        plt.tight_layout()

        save_path = os.path.join(self.figures_dir, filename)
        plt.savefig(save_path, dpi=300)
        plt.savefig(save_path.replace(".png", ".pdf"))
        plt.close()
        print(f"[HANGPlotter] Saved plot to {save_path}")
