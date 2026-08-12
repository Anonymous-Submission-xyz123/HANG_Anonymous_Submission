import json
import random
from pathlib import Path

from datasets import load_dataset


DATASET_NAME = "dessertlab/offensive-powershell"
SPLIT = "train"
SEED = 20260709
SIZE = 150

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "dataset" / "Collection_extended"
METADATA = BASE_DIR / "dataset" / "metadata.jsonl"
OUTPUT = BASE_DIR / "subset_150_seed_20260709.json"
AUTORAN_OUTPUT = BASE_DIR / "subset_25_seed_20260709.json"


def sample_name(index):
    return f"{index:04d}.ps1"


def main():
    dataset = load_dataset(DATASET_NAME, split=SPLIT)
    if len(dataset) < SIZE:
        raise RuntimeError(f"{DATASET_NAME}/{SPLIT} contains only {len(dataset)} samples")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    METADATA.parent.mkdir(parents=True, exist_ok=True)

    with METADATA.open("w", encoding="utf-8") as metadata_file:
        for index, row in enumerate(dataset):
            name = sample_name(index)
            code = row.get("code") or ""
            nl = row.get("nl") or ""
            content = (
                f"# Natural language intent:\n"
                f"# {nl.replace(chr(10), chr(10) + '# ')}\n\n"
                f"{code}\n"
            )
            (DATA_DIR / name).write_text(content, encoding="utf-8")
            metadata_file.write(
                json.dumps(
                    {
                        "file": name,
                        "dataset": DATASET_NAME,
                        "split": SPLIT,
                        "index": index,
                        "nl": nl,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    files = [sample_name(index) for index in range(len(dataset))]
    rng = random.Random(SEED)
    subset = sorted(rng.sample(files, SIZE))
    OUTPUT.write_text(json.dumps(subset, indent=2) + "\n", encoding="utf-8")
    AUTORAN_OUTPUT.write_text(json.dumps(subset[:25], indent=2) + "\n", encoding="utf-8")

    print(f"materialized {len(dataset)} samples to {DATA_DIR}")
    print(f"wrote {len(subset)} samples to {OUTPUT}")
    print(f"wrote 25 nested AutoRAN samples to {AUTORAN_OUTPUT}")


if __name__ == "__main__":
    main()
