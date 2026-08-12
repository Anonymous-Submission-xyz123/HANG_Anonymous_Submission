"""Build the action-specific HANG trace manifest from InjecAgent cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON at {path}:{line_number}") from exc


def build_manifest(data_dir: Path) -> dict[str, dict[str, object]]:
    manifest: dict[str, dict[str, object]] = {}
    for split in ("dh", "ds"):
        path = data_dir / f"attacker_cases_{split}.jsonl"
        for record in read_jsonl(path):
            tools = record.get("Attacker Tools") or []
            instruction = str(record.get("Attacker Instruction") or "").strip()
            if not tools or not instruction:
                raise ValueError(f"Missing tool or instruction in {path}")

            first_tool = str(tools[0])
            key = f"{first_tool}|{instruction}"
            if key in manifest:
                raise ValueError(f"Duplicate trace-manifest key: {key}")
            manifest[key] = {
                "attacker_tool": first_tool,
                "attacker_instruction": instruction,
                "type": split,
                "thought_step1": "",
                "thought_step2": "",
            }
    return dict(sorted(manifest.items()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_DIR / "harvested_traces_template.json",
    )
    args = parser.parse_args()

    manifest = build_manifest(args.data_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(manifest)} trace entries to {args.output}")


if __name__ == "__main__":
    main()
