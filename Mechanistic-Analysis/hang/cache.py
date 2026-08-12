"""
Tensor caching utility for HANG activations, attention weights, and logits.
"""

import os
import json
from typing import Dict, Any, Optional
import torch


class HANGCacheManager:
    def __init__(self, cache_dir: str = "outputs/caches"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def get_run_cache_dir(self, run_id: str) -> str:
        d = os.path.join(self.cache_dir, run_id)
        os.makedirs(d, exist_ok=True)
        return d

    def save_cache(self, run_id: str, cache_dict: Dict[str, torch.Tensor]) -> Dict[str, str]:
        """Saves activation, attention, and logit tensors to disk and returns paths dict."""
        run_dir = self.get_run_cache_dir(run_id)
        saved_paths = {}

        for key, tensor in cache_dict.items():
            if tensor is None:
                continue
            filename = f"{key}.pt"
            filepath = os.path.join(run_dir, filename)
            # Move tensor to CPU before saving
            cpu_tensor = tensor.detach().cpu() if isinstance(tensor, torch.Tensor) else tensor
            torch.save(cpu_tensor, filepath)
            saved_paths[key] = filepath

        return saved_paths

    def save_metadata(
        self, run_id: str, semantics: Dict[str, str],
        cache_dict: Dict[str, torch.Tensor]
    ) -> str:
        """Persist cache meanings, dtypes, and exact tensor shapes."""
        run_dir = self.get_run_cache_dir(run_id)
        filepath = os.path.join(run_dir, "metadata.json")
        metadata = {
            "semantics": semantics,
            "tensors": {
                key: {
                    "shape": list(value.shape),
                    "dtype": str(value.dtype),
                }
                for key, value in cache_dict.items()
                if isinstance(value, torch.Tensor)
            },
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, sort_keys=True)
        return filepath

    def load_cache(self, run_id: str, key: str) -> Optional[torch.Tensor]:
        """Loads a specific cached tensor for a run_id."""
        run_dir = os.path.join(self.cache_dir, run_id)
        filepath = os.path.join(run_dir, f"{key}.pt")
        if not os.path.exists(filepath):
            return None
        return torch.load(filepath, map_location="cpu")

    def load_all_caches(self, run_id: str) -> Dict[str, torch.Tensor]:
        """Loads all cached tensors for a run_id."""
        run_dir = os.path.join(self.cache_dir, run_id)
        if not os.path.exists(run_dir):
            return {}
        result = {}
        for fname in os.listdir(run_dir):
            if fname.endswith(".pt"):
                key = fname[:-3]
                result[key] = torch.load(os.path.join(run_dir, fname), map_location="cpu")
        return result
