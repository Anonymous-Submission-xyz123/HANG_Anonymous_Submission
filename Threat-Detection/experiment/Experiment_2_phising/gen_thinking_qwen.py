#!/usr/bin/env python3
"""
Generation script: dedicated to Qwen3.7 Plus (Custom OpenAI provider)
Generates thinking traces for the IMPORTANT-BUSINESS-CORE config (no comment)
using prompt_A2_en.txt at temperature=0.5.
Saves to: Experiment_2_phising/thinking/
"""

import os
import glob
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

# ── API config ────────────────────────────────────────────────────────────────
client = OpenAI(
    api_key=os.getenv("CUSTOM_API_KEY", "sk-45acc7dba459a313-fe8728-50b4f780"),
    base_url=os.getenv("CUSTOM_BASE_URL", "https://dafud.tunaonthesea.ovh/v1"),
    default_headers={
        "User-Agent": "kilo-editor/1.0",
        "Accept": "application/json",
    }
)

MODEL = os.getenv("CUSTOM_MODEL", "deepseek-v4-flash")
MODEL_SLUG = "qwen"

# ── paths ─────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))          # Experiment_2_phising/
THINKING_DIR  = os.path.join(BASE_DIR, "thinking")
PROMPT_FILE   = os.path.join(os.path.dirname(BASE_DIR), "phishing_prompt", "prompt_A2_en.txt")
CODE_DIR      = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)),
                              "dataset", "phishing", "Collection_extended")

# ── settings ──────────────────────────────────────────────────────────────────
TEMPERATURE   = 0.5
MIN_WORDS     = 75
MAX_RETRIES   = 10      # High retry count to handle transient errors
TIMEOUT       = 60      # 60s timeout per call
MAX_WORKERS   = 2       # 2 processes/threads concurrent

# ── helpers ───────────────────────────────────────────────────────────────────
def load_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def word_count(text):
    if not text:
        return 0
    return len(text.split())

def call_model(system_prompt, user_content):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_content},
    ]
    
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # We enforce timeout using client request or general try-except
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=2048,
                stream=False,
                timeout=TIMEOUT,
            )
            choice = response.choices[0].message
            reasoning = getattr(choice, "reasoning_content", None) or getattr(choice, "reasoning", None) or ""
            content = choice.content or ""
            return reasoning, content
        except Exception as e:
            last_exc = e
            print(f"  [API attempt {attempt}/{MAX_RETRIES} fail] Error: {e}")
            time.sleep(2 * attempt)
            
    print(f"  [API error] giving up: {last_exc}")
    return None, None

def already_exists(stem):
    """Check if any thinking file exists for this stem."""
    pattern = os.path.join(THINKING_DIR,
                           f"*({stem})*(IMPORTANT-BUSINESS-CORE)*{MODEL_SLUG}*")
    candidates = glob.glob(pattern)
    return len(candidates) > 0

def save_thinking(stem, reasoning):
    """Save reasoning to thinking/ with canonical filename."""
    os.makedirs(THINKING_DIR, exist_ok=True)
    desc      = f"Experiment 1|A2|{stem}|IMPORTANT-BUSINESS-CORE"
    desc_slug = "(" + desc.replace("|", ")(") + ")"
    base_name = f"{desc_slug} {MODEL_SLUG} think.txt"
    out_path  = os.path.join(THINKING_DIR, base_name)
    n = 2
    while os.path.exists(out_path):
        out_path = os.path.join(THINKING_DIR,
                                f"{desc_slug} {MODEL_SLUG} think_{n}.txt")
        n += 1
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(reasoning)
    return out_path

def process_file(code_file, system_prompt):
    stem = os.path.splitext(code_file)[0]
    if already_exists(stem):
        return "skipped_exists", stem

    code = load_text(os.path.join(CODE_DIR, code_file))
    if code and len(code) > 80000:
        return "skipped_size", stem

    user_content = f"/*IMPORTANT-BUSINESS-CORE*/\n{code}"
    
    best_reasoning = None
    best_wc = 0
    
    # Retry logic up to MAX_RETRIES if trace < MIN_WORDS
    for attempt in range(1, 4):
        reasoning, answer = call_model(system_prompt, user_content)
        if reasoning is None:
            continue
            
        wc = word_count(reasoning)
        if wc > best_wc:
            best_wc = wc
            best_reasoning = reasoning
            
        if wc >= MIN_WORDS:
            break
            
        time.sleep(1)

    if best_reasoning is None or not best_reasoning.strip():
        return "failed", stem

    saved = save_thinking(stem, best_reasoning)
    if best_wc < MIN_WORDS:
        return "too_short", (stem, best_wc, os.path.basename(saved))
    return "success", (stem, best_wc, os.path.basename(saved))

def main():
    system_prompt = load_text(PROMPT_FILE)
    print(f"Loaded prompt: {PROMPT_FILE}")
    print(f"Model: {MODEL} | Min words: {MIN_WORDS}\n")

    code_files = sorted(
        f for f in os.listdir(CODE_DIR)
        if os.path.isfile(os.path.join(CODE_DIR, f))
        and f.endswith(".txt")
    )
    print(f"Found {len(code_files)} phishing files in Collection_extended\n")

    start_time = time.time()
    max_duration = 3600 # 60 minutes timeout at most

    skipped = 0
    success = 0
    too_short = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_file, f, system_prompt): f for f in code_files}
        
        for future in as_completed(futures):
            # Check elapsed time
            elapsed = time.time() - start_time
            if elapsed >= max_duration:
                print(f"\n[Timeout] Reached 60 minutes limit. Terminating remaining tasks...")
                break

            status, data = future.result()
            if status == "skipped_exists":
                print(f"[skip] {data} — already has trace")
                skipped += 1
            elif status == "skipped_size":
                print(f"[skip] {data} — too large")
                skipped += 1
            elif status == "failed":
                print(f"[gen ] {data} ... ❌ failed API calls")
                failed += 1
            elif status == "too_short":
                stem, wc, filename = data
                print(f"[gen ] {stem} ... ⚠️  best={wc}w < {MIN_WORDS} — saved anyway → {filename}")
                too_short += 1
            elif status == "success":
                stem, wc, filename = data
                print(f"[gen ] {stem} ... ✅ {wc}w — saved → {filename}")
                success += 1

    print("\n" + "=" * 60)
    print(f" DONE")
    print(f"  Skipped           : {skipped}")
    print(f"  Generated ≥{MIN_WORDS}w  : {success}")
    print(f"  Generated <{MIN_WORDS}w  : {too_short}")
    print(f"  Failed            : {failed}")
    print(f"  Total Time        : {time.time() - start_time:.2f}s")
    print("=" * 60)

if __name__ == "__main__":
    main()
