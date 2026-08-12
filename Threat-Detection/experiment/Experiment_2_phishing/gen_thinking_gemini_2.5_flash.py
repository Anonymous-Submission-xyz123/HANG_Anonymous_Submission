#!/usr/bin/env python3
"""
Generation script: dedicated to google/gemini-2.5-flash
Generates thinking traces for the IMPORTANT-BUSINESS-CORE config (no comment)
using prompt_A2_en.txt at temperature=0.15.
Saves to: Experiment_2_phishing/thinking/
"""

import os
import glob
import requests
import json
import time

# ── API config ────────────────────────────────────────────────────────────────
API_KEY = os.getenv("GEMINI_API_KEY", "")
TIMEOUT = 120

# ── paths ─────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))          # Experiment_2_phishing/
THINKING_DIR  = os.path.join(BASE_DIR, "thinking")
PROMPT_FILE   = os.path.join(os.path.dirname(BASE_DIR), "phishing_prompt", "prompt_A2_en.txt")
CODE_DIR      = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)),
                              "dataset", "phishing", "Collection_extended")

# ── settings ──────────────────────────────────────────────────────────────────
MODEL         = "google/gemini-2.5-flash"
MODEL_SLUG    = "gemini-2.5-flash"
TEMPERATURE   = 0.15
TOP_P         = 0.9
MIN_WORDS     = 75
MAX_RETRIES   = 5       # retries per case if trace < MIN_WORDS

# ── helpers ───────────────────────────────────────────────────────────────────
def load_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def word_count(text):
    if not text:
        return 0
    return len(text.split())

def call_model(system_prompt, user_content):
    """Call Gemini native generateContent with thinkingConfig + includeThoughts."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": f"System Prompt:\n{system_prompt}\n\nUser Content:\n{user_content}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": TEMPERATURE,
            "thinkingConfig": {
                "thinkingBudget": 2048,
                "includeThoughts": True
            }
        }
    }
    
    try:
        time.sleep(3)  # Basic rate limit spacing
        resp = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        out = resp.json()
        
        candidates = out.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            reasoning = ""
            answer = ""
            for part in parts:
                if part.get("thought", False):
                    reasoning += part.get("text", "")
                else:
                    answer += part.get("text", "")
            return reasoning if reasoning else answer, answer
        return "", ""
        
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else 0
        print(f"  [API HTTP error] {status_code}: {e}")
        try:
            print(f"  Error details: {e.response.text[:500]}")
        except:
            pass
        if status_code == 429:
            time.sleep(15)
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
    print(f"       saved → {os.path.basename(out_path)}")

# ── load assets ───────────────────────────────────────────────────────────────
system_prompt = load_text(PROMPT_FILE)
print(f"Loaded prompt: {PROMPT_FILE}")
print(f"Model: {MODEL}  |  Temp: {TEMPERATURE}  |  Min words: {MIN_WORDS}\n")

# Gather files
code_files = sorted(
    f for f in os.listdir(CODE_DIR)
    if os.path.isfile(os.path.join(CODE_DIR, f))
    and f.endswith(".txt")
)
print(f"Found {len(code_files)} phishing files in Collection_extended\n")

# ── main loop ─────────────────────────────────────────────────────────────────
skipped  = 0
produced = 0

for i, code_file in enumerate(code_files):
    stem = os.path.splitext(code_file)[0]
    
    if already_exists(stem):
        print(f"[skip] {stem} — already has trace")
        skipped += 1
        continue

    # Load content
    code_path = os.path.join(CODE_DIR, code_file)
    code = load_text(code_path)
    if len(code) > 80000:
        print(f"[skip] {stem} — too large")
        skipped += 1
        continue
    
    # Payload
    base_payload = f"/*IMPORTANT-BUSINESS-CORE*/\n{code}"
    
    print(f"[gen ] {stem} ...", end="", flush=True)
    
    reasoning = None
    for attempt in range(1, MAX_RETRIES + 1):
        r, a = call_model(system_prompt, base_payload)
        if r is None:
            print(f" [attempt {attempt} API fail]", end="", flush=True)
            time.sleep(2 * attempt)
            continue
        wc = word_count(r)
        if wc >= MIN_WORDS:
            reasoning = r
            print(f" ✅ {wc}w")
            break
        else:
            print(f" [attempt {attempt}: {wc}w]", end="", flush=True)
            time.sleep(1)
            
    if reasoning:
        save_thinking(stem, reasoning)
        produced += 1
    else:
        print(f" ❌ Failed to generate thinking trace for {stem}")
        
print("\n" + "=" * 50)
print(f"Completed! Produced: {produced} traces, Skipped: {skipped} traces.")
print("=" * 50)
