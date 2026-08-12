"""Run missing causal intervention experiments for authentic HANG controls.

This script consumes the already-persisted three-condition records from the
authentic overnight run:

    no_trace / matched_trace / unrelated_trace

and writes an intervention table suitable for the mechanism-section outline.
It keeps tensor capture lean: donor activations are captured only over the
trace span and only at the selected layers.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hang.evaluator import HANGEvaluator
from hang.interventions import HANGInterventions
from hang.model_adapter import ModelRunResult, HANGModelAdapter


DEFAULT_MODEL_PATH = (
    "/home/huynp2/.cache/huggingface/hub/"
    "models--openai--gpt-oss-20b/snapshots/"
    "6cee5e81ee83917806bbde320786a8fb61efebee"
)

DEFAULT_CASES = [
    "AK-74",
    "CasuS-1.5",
    "GRP_WebShell",
    "DTool_Pro",
    "Dive_Shell",
    "Ajax_PHP_Command_Shell",
]


def load_record(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                return json.loads(line)
    raise ValueError(f"empty record file: {path}")


def load_completed_records(path: Path) -> tuple[set[tuple[str, str]], list[dict]]:
    completed: set[tuple[str, str]] = set()
    rows: list[dict] = []
    if not path.exists():
        return completed, rows
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            key = (str(row.get("case_id")), str(row.get("intervention")))
            completed.add(key)
            rows.append(row)
    return completed, rows


def span_tuple(record: dict, name: str) -> Tuple[int, int]:
    value = record["token_spans"][name]
    return int(value[0]), int(value[1])


def choose_layers(metrics_csv: Path, top_k: int, num_layers: int) -> List[int]:
    if metrics_csv.exists():
        df = pd.read_csv(metrics_csv)
        if {
            "layer",
            "condition",
            "generated_trace_attention_mean",
        }.issubset(df.columns):
            grouped = (
                df.groupby(["layer", "condition"])["generated_trace_attention_mean"]
                .mean()
                .unstack()
            )
            if {"matched_trace", "unrelated_trace"}.issubset(grouped.columns):
                grouped["delta"] = grouped["matched_trace"] - grouped["unrelated_trace"]
                ranked = grouped.sort_values("delta", ascending=False)
                positive = [int(layer) for layer, row in ranked.iterrows() if row["delta"] > 0]
                if positive:
                    return positive[:top_k]
            if "matched_trace" in grouped.columns:
                ranked = grouped.sort_values("matched_trace", ascending=False)
                return [int(layer) for layer in ranked.index[:top_k]]
    if num_layers <= top_k:
        return list(range(num_layers))
    return sorted(set(round(x) for x in torch.linspace(0, num_layers - 1, top_k).tolist()))


def random_control_layers(target_layers: List[int], num_layers: int, seed: int) -> List[int]:
    rng = random.Random(seed)
    pool = [idx for idx in range(num_layers) if idx not in set(target_layers)]
    if len(pool) < len(target_layers):
        pool = list(range(num_layers))
    return sorted(rng.sample(pool, len(target_layers)))


def same_length_payload_region(record: dict, desired_len: int) -> Tuple[int, int]:
    p0, p1 = span_tuple(record, "payload_span")
    return p0, min(p1, p0 + desired_len)


def first_token_id_options(tokenizer, strings: Iterable[str]) -> List[int]:
    ids = []
    for text in strings:
        encoded = tokenizer(text, add_special_tokens=False)["input_ids"]
        if encoded:
            ids.append(int(encoded[0]))
    return sorted(set(ids))


def clean_webshell_margin(tokenizer, logits: torch.Tensor, prompt_len: int) -> float:
    clean_ids = first_token_id_options(
        tokenizer,
        ["Clean", " Clean", '"Clean"', ' "Clean"', ":Clean", ': "Clean"'],
    )
    webshell_ids = first_token_id_options(
        tokenizer,
        ["Webshell", " Webshell", '"Webshell"', ' "Webshell"', ":Webshell", ': "Webshell"'],
    )
    row = logits[0, prompt_len - 1].float()
    clean = torch.stack([row[i] for i in clean_ids]).max()
    webshell = torch.stack([row[i] for i in webshell_ids]).max()
    return float((clean - webshell).item())


@torch.no_grad()
def capture_span_activations(
    adapter: HANGModelAdapter,
    token_ids: List[int],
    span: Tuple[int, int],
    layers: List[int],
    location: str,
) -> Dict[int, torch.Tensor]:
    handles = []
    captured: Dict[int, torch.Tensor] = {}
    s0, s1 = span

    def register(module, layer_idx: int):
        def hook(_module, _inputs, output):
            value = output[0] if isinstance(output, tuple) else output
            if value.dim() >= 3 and value.shape[1] > s0:
                captured[layer_idx] = value[:, s0:min(s1, value.shape[1]), :].detach().cpu()
            return output

        handles.append(module.register_forward_hook(hook))

    for layer_idx in layers:
        layer = adapter.layers[layer_idx]
        if location == "attention_output":
            register(layer.self_attn, layer_idx)
        elif location == "mlp_output":
            register(layer.mlp, layer_idx)
        elif location == "post_mlp_residual":
            register(layer, layer_idx)
        else:
            raise ValueError(f"unknown patch location: {location}")

    try:
        device = next(adapter.model.parameters()).device
        input_ids = torch.tensor([token_ids], dtype=torch.long, device=device)
        adapter.model(input_ids, use_cache=False, return_dict=True)
    finally:
        for handle in handles:
            handle.remove()
    return captured


@contextlib.contextmanager
def patch_span_context(
    adapter: HANGModelAdapter,
    donor_span_acts: Dict[int, torch.Tensor],
    target_span: Tuple[int, int],
    layers: List[int],
    location: str,
):
    handles = []
    t0, t1 = target_span

    def register(module, layer_idx: int):
        donor = donor_span_acts[layer_idx]

        def hook(_module, _inputs, output):
            value = output[0] if isinstance(output, tuple) else output
            if value.dim() < 3 or value.shape[1] <= t0:
                return output
            end = min(t1, value.shape[1], t0 + donor.shape[1])
            if end <= t0:
                return output
            patched = value.clone()
            donor_slice = donor[:, : end - t0, :].to(device=patched.device, dtype=patched.dtype)
            patched[:, t0:end, :] = donor_slice
            if isinstance(output, tuple):
                return (patched,) + output[1:]
            return patched

        handles.append(module.register_forward_hook(hook))

    for layer_idx in layers:
        if layer_idx not in donor_span_acts:
            raise KeyError(f"missing donor activation for layer {layer_idx} at {location}")
        layer = adapter.layers[layer_idx]
        if location == "attention_output":
            register(layer.self_attn, layer_idx)
        elif location == "mlp_output":
            register(layer.mlp, layer_idx)
        elif location == "post_mlp_residual":
            register(layer, layer_idx)
        else:
            raise ValueError(f"unknown patch location: {location}")

    try:
        yield
    finally:
        for handle in handles:
            handle.remove()


def run_generation(
    adapter: HANGModelAdapter,
    token_ids: List[int],
    max_new_tokens: int,
    seed: int,
) -> ModelRunResult:
    return adapter.run_with_cache(
        token_ids=token_ids,
        max_new_tokens=max_new_tokens,
        temperature=0.0,
        do_sample=False,
        seed=seed,
        record_activations=False,
    )


def output_row(
    *,
    evaluator: HANGEvaluator,
    adapter: HANGModelAdapter,
    case: str,
    intervention: str,
    source_condition: str,
    target_layers: List[int],
    span_name: str,
    baseline_record: dict,
    result: ModelRunResult,
    extra: dict | None = None,
) -> dict:
    run_id = f"{case}::{intervention}"
    evaluation = evaluator.evaluate(run_id, result.generated_text)
    row = {
        "case_id": case,
        "intervention": intervention,
        "source_condition": source_condition,
        "target_layers": ",".join(str(x) for x in target_layers),
        "span_name": span_name,
        "baseline_attack_success": bool(baseline_record["attack_success"]),
        "intervention_attack_success": bool(evaluation.attack_success),
        "asr_delta": float(evaluation.attack_success) - float(baseline_record["attack_success"]),
        "clean_webshell_margin": clean_webshell_margin(
            adapter.tokenizer, result.logits, len(result.prompt_token_ids)
        )
        if result.logits is not None
        else None,
        "generated_text": result.generated_text,
        "evaluator_output": evaluation.rationale,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        row.update(extra)
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-runs", default="outputs/hang_overnight_20b/runs/openai_gpt-oss-20b/hang_overnight_20b")
    parser.add_argument("--attention-metrics", default="outputs/hang_mechanism_attention_subset_20b/tables/mechanism_subset_metrics.csv")
    parser.add_argument("--output", default="outputs/hang_missing_interventions_20b")
    parser.add_argument("--model-path", default=DEFAULT_MODEL_PATH)
    parser.add_argument("--cases", nargs="*", default=DEFAULT_CASES)
    parser.add_argument("--top-k-layers", type=int, default=4)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    output = Path(args.output)
    tables = output / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    records_path = output / "intervention_records.jsonl"
    failures_path = output / "failures.jsonl"

    adapter = HANGModelAdapter(
        args.model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        local_files_only=True,
    )
    adapter.model.generation_config.pad_token_id = adapter.tokenizer.pad_token_id
    adapter.model.generation_config.eos_token_id = adapter.tokenizer.eos_token_id

    target_layers = choose_layers(Path(args.attention_metrics), args.top_k_layers, adapter.num_layers)
    control_layers = random_control_layers(target_layers, adapter.num_layers, args.seed)
    print(f"[interventions] targeted layers: {target_layers}")
    print(f"[interventions] random-control layers: {control_layers}")

    evaluator = HANGEvaluator()
    completed, rows = load_completed_records(records_path)
    if completed:
        print(f"[interventions] resuming with {len(completed)} completed record(s)")
    source = Path(args.source_runs)

    with records_path.open("a", encoding="utf-8") as rec_out, failures_path.open("a", encoding="utf-8") as fail_out:
        for case in args.cases:
            try:
                matched = load_record(source / case / "matched_trace.jsonl")
                unrelated = load_record(source / case / "unrelated_trace.jsonl")

                matched_trace_span = span_tuple(matched, "trace_span")
                matched_payload_control = same_length_payload_region(
                    matched, matched_trace_span[1] - matched_trace_span[0]
                )
                unrelated_trace_span = span_tuple(unrelated, "trace_span")

                jobs = [
                    (
                        "targeted_trace_attention_ablation",
                        "matched_trace",
                        target_layers,
                        matched_trace_span,
                        "matched_trace_span",
                    ),
                    (
                        "random_layer_trace_attention_ablation",
                        "matched_trace",
                        control_layers,
                        matched_trace_span,
                        "matched_trace_span",
                    ),
                    (
                        "payload_region_attention_ablation_control",
                        "matched_trace",
                        target_layers,
                        matched_payload_control,
                        "payload_region_same_token_count",
                    ),
                ]
                for intervention, condition, layers, span, span_name in jobs:
                    if (case, intervention) in completed:
                        print(f"[interventions] skip completed {case} {intervention}")
                        continue
                    try:
                        result = HANGInterventions.run_attention_ablation(
                            adapter,
                            matched["prompt_token_ids"],
                            span,
                            layers,
                            max_new_tokens=args.max_new_tokens,
                            seed=args.seed,
                        )
                        row = output_row(
                            evaluator=evaluator,
                            adapter=adapter,
                            case=case,
                            intervention=intervention,
                            source_condition=condition,
                            target_layers=layers,
                            span_name=span_name,
                            baseline_record=matched,
                            result=result,
                            extra={
                                "baseline_condition": "matched_trace",
                                "donor_condition": "",
                                "recipient_condition": "",
                            },
                        )
                        rows.append(row)
                        completed.add((case, intervention))
                        rec_out.write(json.dumps(row, sort_keys=True) + "\n")
                        rec_out.flush()
                        print(
                            f"[interventions] {case} {intervention}: "
                            f"success={row['intervention_attack_success']} "
                            f"margin={row['clean_webshell_margin']:.3f}"
                        )
                    except Exception as exc:
                        failure = {
                            "case_id": case,
                            "intervention": intervention,
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                        }
                        fail_out.write(json.dumps(failure, sort_keys=True) + "\n")
                        fail_out.flush()
                        print(f"[interventions] failed {case} {intervention}: {type(exc).__name__}: {exc}")
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()

                for location in ["attention_output", "mlp_output", "post_mlp_residual"]:
                    intervention = f"{location}_patch_matched_into_unrelated"
                    if (case, intervention) in completed:
                        print(f"[interventions] skip completed {case} {intervention}")
                        continue
                    try:
                        donor = capture_span_activations(
                            adapter,
                            matched["prompt_token_ids"],
                            matched_trace_span,
                            target_layers,
                            location,
                        )
                        with patch_span_context(
                            adapter,
                            donor,
                            unrelated_trace_span,
                            target_layers,
                            location,
                        ):
                            result = run_generation(
                                adapter,
                                unrelated["prompt_token_ids"],
                                args.max_new_tokens,
                                args.seed,
                            )
                        row = output_row(
                            evaluator=evaluator,
                            adapter=adapter,
                            case=case,
                            intervention=intervention,
                            source_condition="unrelated_trace",
                            target_layers=target_layers,
                            span_name="unrelated_trace_span",
                            baseline_record=unrelated,
                            result=result,
                            extra={
                                "baseline_condition": "unrelated_trace",
                                "donor_condition": "matched_trace",
                                "recipient_condition": "unrelated_trace",
                            },
                        )
                        rows.append(row)
                        completed.add((case, intervention))
                        rec_out.write(json.dumps(row, sort_keys=True) + "\n")
                        rec_out.flush()
                        print(
                            f"[interventions] {case} {intervention}: "
                            f"success={row['intervention_attack_success']} "
                            f"margin={row['clean_webshell_margin']:.3f}"
                        )
                    except Exception as exc:
                        failure = {
                            "case_id": case,
                            "intervention": intervention,
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                        }
                        fail_out.write(json.dumps(failure, sort_keys=True) + "\n")
                        fail_out.flush()
                        print(f"[interventions] failed {case} {intervention}: {type(exc).__name__}: {exc}")
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception as exc:
                failure = {
                    "case_id": case,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                }
                fail_out.write(json.dumps(failure, sort_keys=True) + "\n")
                fail_out.flush()
                print(f"[interventions] failed {case}: {type(exc).__name__}: {exc}")
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(tables / "intervention_records.csv", index=False)
        summary = (
            df.groupby("intervention", dropna=False)
            .agg(
                n=("case_id", "count"),
                baseline_asr=("baseline_attack_success", "mean"),
                intervention_asr=("intervention_attack_success", "mean"),
                mean_asr_delta=("asr_delta", "mean"),
                mean_clean_webshell_margin=("clean_webshell_margin", "mean"),
            )
            .reset_index()
        )
        summary.to_csv(tables / "intervention_summary.csv", index=False)
        with (output / "run_config.json").open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "model_path": args.model_path,
                    "source_runs": args.source_runs,
                    "attention_metrics": args.attention_metrics,
                    "cases": args.cases,
                    "target_layers": target_layers,
                    "random_control_layers": control_layers,
                    "max_new_tokens": args.max_new_tokens,
                    "seed": args.seed,
                },
                handle,
                indent=2,
                sort_keys=True,
            )
        print(f"[interventions] wrote {len(rows)} records to {records_path}")
        print(f"[interventions] wrote summary to {tables / 'intervention_summary.csv'}")


if __name__ == "__main__":
    main()
