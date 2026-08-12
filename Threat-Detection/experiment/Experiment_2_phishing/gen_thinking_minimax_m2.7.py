#!/usr/bin/env python3
"""
Generation script: dedicated to MiniMax-M2.7
Generates thinking traces for the IMPORTANT-BUSINESS-CORE config (no comment)
using prompt_A2_en.txt at temperature=0.5.
Saves to: Experiment_2_phishing/thinking/
"""

import os
import glob
import requests
import json
import time

# ── API config ────────────────────────────────────────────────────────────────
URL = os.getenv(
    "MINIMAX_BASE_URL",
    "https://api.minimax.io/v1/text/chatcompletion_v2",
)
API_KEY = os.getenv("MINIMAX_API_KEY", "")

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
    "User-Agent": "axios/1.11.0",
}

# ── paths ─────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))          # Experiment_2_phishing/
THINKING_DIR  = os.path.join(BASE_DIR, "thinking")
PROMPT_FILE   = os.path.join(os.path.dirname(BASE_DIR), "phishing_prompt", "prompt_A2_en.txt")
CODE_DIR      = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)),
                              "dataset", "phishing", "Collection_extended")

# ── settings ──────────────────────────────────────────────────────────────────
MODEL         = "MiniMax-M2.7"
MODEL_SLUG    = "minimax-m2.7"
TEMPERATURE   = 0.5
TOP_P         = 0.9
MIN_WORDS     = 75
MAX_RETRIES   = 5       # retries per case if trace < MIN_WORDS
TIMEOUT       = 120

# ── helpers ───────────────────────────────────────────────────────────────────
def load_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def word_count(text):
    if not text:
        return 0
    return len(text.split())

def call_model(system_prompt, user_content):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content},
        ],
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "max_tokens": 2048,
    }
    
    try:
        resp = requests.post(URL, headers=HEADERS, json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        out = resp.json()
        
        base = out.get("base_resp") or {}
        if base.get("status_code", 0) not in (0, None):
            raise RuntimeError(f"MiniMax error {base.get('status_code')}: {base.get('status_msg')}")
            
        choices = out.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            reasoning = message.get("reasoning_content") or message.get("reasoning") or ""
            answer = message.get("content") or ""
            return reasoning, answer
        return "", ""
        
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else 0
        print(f"  [API HTTP error] {status_code}: {e}")
        return None, None
    except Exception as e:
        print(f"  [API error] {type(e).__name__}: {e}")
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

# ── load prompt ───────────────────────────────────────────────────────────────
system_prompt = load_text(PROMPT_FILE)
print(f"Loaded prompt: {PROMPT_FILE}")
print(f"Model: {MODEL}  |  Temp: {TEMPERATURE}  |  Min words: {MIN_WORDS}\n")

# ── collect code files ────────────────────────────────────────────────────────
code_files = sorted(
    f for f in os.listdir(CODE_DIR)
    if os.path.isfile(os.path.join(CODE_DIR, f))
    and f.endswith(".txt")
)
print(f"Found {len(code_files)} phishing files in Collection_extended\n")

# ── main loop ─────────────────────────────────────────────────────────────────
skipped  = 0
success  = 0
too_short = 0
failed   = 0

for code_file in code_files:
    stem = os.path.splitext(code_file)[0]   # e.g. "529"

    if already_exists(stem):
        print(f"[skip] {stem} — already has trace")
        skipped += 1
        continue

    code = load_text(os.path.join(CODE_DIR, code_file))
    if code and len(code) > 80000:
        print(f"[skip] {code_file} — too large ({len(code)} chars)")
        skipped += 1
        continue

    user_content = f"/*IMPORTANT-BUSINESS-CORE*/\n{code}"

    print(f"[gen ] {stem} ...", end="", flush=True)

    best_reasoning = None
    best_wc        = 0

    for attempt in range(1, MAX_RETRIES + 1):
        reasoning, answer = call_model(system_prompt, user_content)
        if reasoning is None:
            print(f" [attempt {attempt} API fail]", end="", flush=True)
            time.sleep(2 * attempt) # Basic backoff
            continue
            
        wc = word_count(reasoning)
        if wc > best_wc:
            best_wc        = wc
            best_reasoning = reasoning
            
        if wc >= MIN_WORDS:
            break
            
        print(f" [attempt {attempt}: {wc}w]", end="", flush=True)
        time.sleep(1)

    if best_reasoning is None:
        print(f" ❌ all API calls failed")
        failed += 1
        continue

    if best_wc < MIN_WORDS:
        print(f" ⚠️  best={best_wc}w < {MIN_WORDS} — saving best anyway")
        too_short += 1
    else:
        print(f" ✅ {best_wc}w")
        success += 1

    saved = save_thinking(stem, best_reasoning)
    print(f"       saved → {os.path.basename(saved)}")

# ── summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f" DONE")
print(f"  Skipped (exists)  : {skipped}")
print(f"  Generated ≥{MIN_WORDS}w  : {success}")
print(f"  Generated <{MIN_WORDS}w  : {too_short}  (saved best attempt)")
print(f"  Failed (API)      : {failed}")
print("=" * 60)
