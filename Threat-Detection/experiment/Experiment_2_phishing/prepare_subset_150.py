import json
import random
from pathlib import Path


SEED = 20260709
SIZE = 150
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent.parent / "dataset" / "phishing" / "Collection_extended"
OUTPUT = BASE_DIR / "subset_150_seed_20260709.json"
AUTORAN_OUTPUT = BASE_DIR / "subset_25_seed_20260709.json"


files = sorted(path.name for path in DATA_DIR.glob("*.txt"))
if len(files) < SIZE:
    raise RuntimeError(f"dataset contains only {len(files)} samples")

rng = random.Random(SEED)
subset = sorted(rng.sample(files, SIZE), key=lambda name: int(Path(name).stem))
OUTPUT.write_text(json.dumps(subset, indent=2) + "\n", encoding="utf-8")
print(f"wrote {len(subset)} samples to {OUTPUT}")
AUTORAN_OUTPUT.write_text(
    json.dumps(subset[:25], indent=2) + "\n", encoding="utf-8"
)
print(f"wrote 25 nested AutoRAN samples to {AUTORAN_OUTPUT}")
