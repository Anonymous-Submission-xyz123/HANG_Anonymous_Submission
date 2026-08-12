import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def split(txt_path: Path, dest_dir: Path, overwrite: bool = False) -> None:
    if not txt_path.exists():
        raise FileNotFoundError(txt_path)
    if dest_dir.exists() and any(dest_dir.iterdir()) and not overwrite:
        raise FileExistsError(
            f"{dest_dir} is not empty; pass --overwrite to replace numbered files"
        )
    dest_dir.mkdir(parents=True, exist_ok=True)
    lines = txt_path.read_text(encoding="utf-8").splitlines()

    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        file_path = dest_dir / f"{idx}.txt"
        if file_path.exists() and not overwrite:
            raise FileExistsError(file_path)
        file_path.write_text(line, encoding="utf-8")

    print(f"Successfully split {len(lines)} phishing emails into {dest_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "cleaned/phishing_1000.txt")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dataset/phishing/Collection_extended",
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    split(args.input, args.output, args.overwrite)
