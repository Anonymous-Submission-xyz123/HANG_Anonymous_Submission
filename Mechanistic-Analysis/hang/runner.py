"""
3-condition experiment runner with checkpointing and structured record persistence.
"""

import json
import os
import hashlib
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional
import torch

from .schemas import RunRecord
from .dataset import HANGDatasetLoader
from .prompt_builder import HANGPromptBuilder
from .token_spans import HANGTokenSpanAligner
from .model_adapter import HANGModelAdapter
from .cache import HANGCacheManager
from .evaluator import HANGEvaluator


class HANGRunner:
    def __init__(
        self,
        model_adapter: HANGModelAdapter,
        dataset_loader: HANGDatasetLoader,
        prompt_builder: HANGPromptBuilder,
        evaluator: HANGEvaluator,
        cache_manager: HANGCacheManager,
        output_dir: str = "outputs/runs",
        experiment_id: str = "hang_exp_v1",
        length_matching_tolerance_tokens: int = 15,
        max_prompt_tokens: Optional[int] = None,
    ):
        self.model_adapter = model_adapter
        self.dataset_loader = dataset_loader
        self.prompt_builder = prompt_builder
        self.evaluator = evaluator
        self.cache_manager = cache_manager
        self.output_dir = output_dir
        self.experiment_id = experiment_id
        self.tolerance_tokens = length_matching_tolerance_tokens
        self.max_prompt_tokens = max_prompt_tokens

    def _max_prompt_length(self) -> int:
        if self.max_prompt_tokens is not None:
            return self.max_prompt_tokens

        tokenizer_limit = getattr(self.model_adapter.tokenizer, "model_max_length", None)
        if isinstance(tokenizer_limit, int) and 0 < tokenizer_limit < 1_000_000:
            return tokenizer_limit

        model = getattr(self.model_adapter, "model", None)
        config = getattr(model, "config", None)
        for attr in ("max_position_embeddings", "n_positions", "seq_length"):
            value = getattr(config, attr, None)
            if isinstance(value, int) and value > 0:
                return value

        return 4096

    @staticmethod
    def _safe_component(value: str) -> str:
        slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
        return slug or hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]

    def _run_id(
        self, base_prompt_id: str, condition: str, template_id: str, seed: int
    ) -> str:
        provenance = json.dumps(
            {
                "experiment_id": self.experiment_id,
                "model": self.model_adapter.model_name,
                "base_prompt_id": base_prompt_id,
                "condition": condition,
                "template_id": template_id,
                "seed": seed,
            },
            sort_keys=True,
        )
        digest = hashlib.sha256(provenance.encode("utf-8")).hexdigest()[:12]
        return (
            f"{self._safe_component(base_prompt_id)}_"
            f"{condition}_{seed}_{digest}"
        )

    @staticmethod
    def _generation_config(max_new_tokens: int, seed: int) -> Dict:
        return {
            "max_new_tokens": max_new_tokens,
            "temperature": 0.0,
            "do_sample": False,
            "seed": seed,
            "cache_scope": "prompt_and_generation_v1",
        }

    def get_prompt_output_dir(self, base_prompt_id: str) -> str:
        d = os.path.join(
            self.output_dir,
            self._safe_component(self.model_adapter.model_name),
            self._safe_component(self.experiment_id),
            self._safe_component(base_prompt_id),
        )
        os.makedirs(d, exist_ok=True)
        return d

    def get_failure_marker_path(self, base_prompt_id: str) -> str:
        return os.path.join(self.get_prompt_output_dir(base_prompt_id), "_failure.json")

    def _save_failure_marker(self, base_prompt_id: str, error: Exception) -> None:
        marker = self.get_failure_marker_path(base_prompt_id)
        payload = {
            "base_prompt_id": base_prompt_id,
            "target_model": self.model_adapter.model_name,
            "experiment_id": self.experiment_id,
            "error_type": type(error).__name__,
            "error": str(error),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        with open(marker, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)

    def run_base_prompt(
        self,
        base_prompt_id: str,
        template_id: str = "default",
        seed: int = 42,
        max_new_tokens: int = 128,
        record_activations: bool = True
    ) -> Dict[str, RunRecord]:
        """Runs all 3 HANG conditions for a single base prompt instance."""
        base_prompt = self.dataset_loader.base_prompts[base_prompt_id]
        out_dir = self.get_prompt_output_dir(base_prompt_id)

        failure_marker = self.get_failure_marker_path(base_prompt_id)
        if os.path.exists(failure_marker):
            print(
                f"[HANGRunner] Base prompt '{base_prompt_id}' has a failure "
                "marker from a previous run. Skipping."
            )
            return {}

        # Check existing checkpoint
        conditions = ["no_trace", "matched_trace", "unrelated_trace"]
        existing_records = {}
        all_completed = True

        for cond in conditions:
            fpath = os.path.join(out_dir, f"{cond}.jsonl")
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8") as f:
                    line = f.readline().strip()
                    if line:
                        record = RunRecord.from_dict(json.loads(line))
                        expected_generation = self._generation_config(
                            max_new_tokens, seed
                        )
                        if (
                            record.base_prompt_id == base_prompt_id
                            and record.condition == cond
                            and record.target_model == self.model_adapter.model_name
                            and record.generation_seed == seed
                            and record.template_id == template_id
                            and record.generation_config == expected_generation
                        ):
                            existing_records[cond] = record
                        else:
                            all_completed = False
                    else:
                        all_completed = False
            else:
                all_completed = False

        if all_completed and len(existing_records) == 3:
            print(f"[HANGRunner] Base prompt '{base_prompt_id}' already completed. Skipping.")
            return existing_records

        # Load matched & unrelated traces
        try:
            matched_trace = self.dataset_loader.get_matched_trace(base_prompt_id)
            unrelated_trace = self.dataset_loader.get_unrelated_trace(base_prompt_id, self.tolerance_tokens)
        except Exception as e:
            print(f"[HANGRunner] Error loading traces for '{base_prompt_id}': {e}")
            raise e

        # Construct prompt records
        p_no = self.prompt_builder.build_prompt(base_prompt, trace=None, condition="no_trace", template_id=template_id)
        p_match = self.prompt_builder.build_prompt(base_prompt, trace=matched_trace, condition="matched_trace", template_id=template_id)
        p_unrelated = self.prompt_builder.build_prompt(base_prompt, trace=unrelated_trace, condition="unrelated_trace", template_id=template_id)

        tokenizer = self.model_adapter.tokenizer
        max_prompt_length = self._max_prompt_length()
        spans_no, ids_no = HANGTokenSpanAligner.align(
            p_no, tokenizer, max_length=max_prompt_length
        )
        spans_match, ids_match = HANGTokenSpanAligner.align(
            p_match, tokenizer, max_length=max_prompt_length
        )
        spans_unrelated, ids_unrelated = HANGTokenSpanAligner.align(
            p_unrelated, tokenizer, max_length=max_prompt_length
        )

        invalid_spans = {
            condition: spans
            for condition, spans in (
                ("no_trace", spans_no),
                ("matched_trace", spans_match),
                ("unrelated_trace", spans_unrelated),
            )
            if not spans.is_valid
        }
        if invalid_spans:
            details = "; ".join(
                f"{condition}: {spans.invalidation_reason}"
                for condition, spans in invalid_spans.items()
            )
            raise ValueError(f"Refusing to run prompts with invalid token spans: {details}")

        # The target tokenizer is the final authority for the control constraint.
        valid_len, diff = HANGTokenSpanAligner.validate_length_matching(spans_match, spans_unrelated, self.tolerance_tokens)
        if not valid_len:
            raise ValueError(
                f"Unrelated trace differs from matched trace by {diff} target-model "
                f"tokens; hard tolerance is {self.tolerance_tokens}."
            )

        prompts_to_run = [
            ("no_trace", p_no, spans_no, ids_no),
            ("matched_trace", p_match, spans_match, ids_match),
            ("unrelated_trace", p_unrelated, spans_unrelated, ids_unrelated)
        ]

        run_records = {}

        for cond_name, p_rec, spans_obj, token_ids in prompts_to_run:
            if cond_name in existing_records:
                print(
                    f"[HANGRunner] Condition '{cond_name}' for base prompt "
                    f"'{base_prompt_id}' already completed. Skipping."
                )
                run_records[cond_name] = existing_records[cond_name]
                continue

            run_id = self._run_id(
                base_prompt_id, cond_name, p_rec.template_id, seed
            )
            print(f"[HANGRunner] Running condition '{cond_name}' for base prompt '{base_prompt_id}'...")

            # Run model pass
            model_out = self.model_adapter.run_with_cache(
                token_ids=token_ids,
                max_new_tokens=max_new_tokens,
                temperature=0.0,
                do_sample=False,
                seed=seed,
                record_activations=record_activations
            )

            # Save tensor cache if requested
            act_path, logits_path, attn_path, metadata_path = None, None, None, None
            if record_activations:
                cache_dict = {}
                if model_out.logits is not None:
                    cache_dict["logits"] = model_out.logits
                for l_idx, hs in model_out.layer_hidden_states.items():
                    cache_dict[f"hidden_state_layer_{l_idx}"] = hs
                for l_idx, att in model_out.layer_attentions.items():
                    cache_dict[f"attention_layer_{l_idx}"] = att
                for l_idx, mlp in model_out.layer_mlp_outputs.items():
                    cache_dict[f"mlp_output_layer_{l_idx}"] = mlp

                saved_paths = self.cache_manager.save_cache(run_id, cache_dict)
                logits_path = saved_paths.get("logits")
                act_path = saved_paths.get(f"hidden_state_layer_0")
                attn_path = saved_paths.get("attention_layer_0")
                metadata_path = self.cache_manager.save_metadata(
                    run_id, model_out.cache_semantics, cache_dict
                )

            # Run evaluation
            eval_res = self.evaluator.evaluate(run_id, model_out.generated_text)

            # Update generated token span bookkeeping
            prompt_len = len(token_ids)
            gen_len = len(model_out.generated_token_ids)
            spans_obj.generated_token_span = (prompt_len, prompt_len + gen_len)

            rec = RunRecord(
                run_id=run_id,
                base_prompt_id=base_prompt_id,
                condition=cond_name,
                target_model=self.model_adapter.model_name,
                generation_seed=seed,
                prompt_token_ids=token_ids,
                token_spans=spans_obj.to_dict(),
                generated_token_ids=model_out.generated_token_ids,
                generated_text=model_out.generated_text,
                attack_success=eval_res.attack_success,
                evaluator_version=eval_res.evaluator_version,
                evaluator_score=eval_res.score,
                evaluator_output=eval_res.rationale,
                activation_cache_path=act_path,
                logits_cache_path=logits_path,
                attention_cache_path=attn_path,
                rendered_prompt=p_rec.rendered_prompt,
                trace_id=p_rec.trace_id,
                template_id=p_rec.template_id,
                generation_config=self._generation_config(max_new_tokens, seed),
                cache_metadata_path=metadata_path,
            )

            # Persist run record JSONL
            fpath = os.path.join(out_dir, f"{cond_name}.jsonl")
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(json.dumps(rec.to_dict()) + "\n")

            run_records[cond_name] = rec

        return run_records

    def run_batch(
        self,
        base_prompt_ids: Optional[List[str]] = None,
        template_id: str = "default",
        seed: int = 42,
        max_new_tokens: int = 128,
        record_activations: bool = True,
    ) -> Dict[str, Dict[str, RunRecord]]:
        """Runs 3-condition evaluation across a batch of base prompts."""
        if base_prompt_ids is None:
            base_prompt_ids = list(self.dataset_loader.base_prompts.keys())

        results = {}
        for b_id in base_prompt_ids:
            try:
                res = self.run_base_prompt(
                    b_id,
                    template_id=template_id,
                    seed=seed,
                    max_new_tokens=max_new_tokens,
                    record_activations=record_activations,
                )
                results[b_id] = res
            except Exception as e:
                print(f"[HANGRunner] Failed base prompt '{b_id}': {e}")
                if "out of memory" in str(e).lower():
                    self._save_failure_marker(b_id, e)
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
        return results
