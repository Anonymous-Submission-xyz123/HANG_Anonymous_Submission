import os
import time
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent

PROMPT_PATH = BASE_DIR / "comment_business_generate_prompt_en.md"
CODE_DIR = PROJECT_ROOT / "dataset" / "phishing" / "Collection_extended"
OUTPUT_DIR = BASE_DIR / "business_comment"

URL = "https://integrate.api.nvidia.com/v1/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.environ['NVIDIA_API_KEY']}",
}

MODEL = "openai/gpt-oss-120b"


def build_prompt(template: str, code: str) -> str:
    return f'{template}\n"""\n{code}\n"""\nOutput:\n'


def generate_for_file(template: str, code_path: Path, out_path: Path):
    code = code_path.read_text(encoding="utf-8", errors="replace")
    prompt = build_prompt(template, code)
    
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.15,
        "top_p": 0.6,
        "max_tokens": 1024
    }
    
    response = requests.post(URL, headers=HEADERS, json=payload, timeout=300)
    response.raise_for_status()
    output = response.json()
    
    choices = output.get("choices", [])
    if not choices:
        raise ValueError("Empty response choices from model")
    
    answer = choices[0].get("message", {}).get("content")
    if not answer:
        raise ValueError("Empty response content from model")
        
    out_path.write_text(answer, encoding="utf-8")
    print(f"[ok] {code_path.name} -> {out_path.name}")


def main():
    template = PROMPT_PATH.read_text(encoding="utf-8")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    code_files = sorted(p for p in CODE_DIR.iterdir() if p.is_file())
    print(f"Processing files in {CODE_DIR} using {MODEL}")

    tasks = []
    for code_path in code_files:
        stem = code_path.stem
        out_path = OUTPUT_DIR / f"{stem}_comment_business.txt"
        
        # Skip if the comment file already exists
        if out_path.exists():
            continue
            
        if code_path.stat().st_size > 80000:
            print(f"[skip] {code_path.name}: too large ({code_path.stat().st_size} bytes)")
            continue

        tasks.append((code_path, out_path))

    print(f"Queueing {len(tasks)} files for comment generation with 4 workers...")

    def worker(task):
        code_path, out_path = task
        try:
            generate_for_file(template, code_path, out_path)
            time.sleep(0.5)  # Brief pause between requests
        except Exception as e:
            print(f"[error] {code_path.name}: {e}")

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(worker, t) for t in tasks]
        for fut in as_completed(futures):
            try:
                fut.result()
            except Exception as e:
                print(f"[executor error] Task execution failed: {e}")

if __name__ == "__main__":
    main()
