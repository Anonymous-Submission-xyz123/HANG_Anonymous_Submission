import os
import sys
import re
import yaml
import requests
import json
import time
import argparse

# Google AI Studio endpoint
# Default model
DEFAULT_MODEL = "gemini-2.5-flash"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
CODE_DIR = os.path.join(PROJECT_ROOT, "dataset", "php-webshells", "Collection_extended")
COMMENT_DIR = os.path.join(os.path.dirname(BASE_DIR), "Experiment_1", "business_comment")
FORGERY_DIR = os.path.join(os.path.dirname(BASE_DIR), "Experiment_1", "thinking_forgery")

def load_text(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def extract_forgery(text):
    if not text:
        return None
    m = re.search(r'(?s)<SYNTHETIC_POLICY>(.*?)</SYNTHETIC_POLICY>', text)
    return m.group(1).strip() if m else None

def generate_forgery(api_key, base_messages, user_input, model_name):
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    contents = []
    system_instruction = ""

    for msg in base_messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            system_instruction = content
        elif role == "user":
            contents.append({
                "role": "user",
                "parts": [{"text": content}]
            })
        elif role in ("assistant", "model"):
            contents.append({
                "role": "model",
                "parts": [{"text": content}]
            })

    # Append our target webshell as a test prompt
    contents.append({
        "role": "user",
        "parts": [{"text": f"<TEST_PROMPT>{user_input}</TEST_PROMPT>"}]
    })

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 2048
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "BLOCK_NONE"}
        ]
    }
    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    params = {"key": api_key}
    headers = {"Content-Type": "application/json"}

    for attempt in range(5):
        try:
            r = requests.post(api_url, params=params, headers=headers, json=payload, timeout=60)
            if r.status_code == 429:
                sleep_time = (2 ** attempt) * 10
                print(f"  [API 429 Rate Limit] attempt {attempt+1}/5. Sleeping {sleep_time}s...")
                time.sleep(sleep_time)
                continue
            r.raise_for_status()
            res = r.json()
            candidates = res.get("candidates", [])
            if candidates:
                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                forgery = extract_forgery(text)
                if forgery:
                    return forgery
                else:
                    # Fallback if tags were missed
                    return text.strip()
        except Exception as e:
            print(f"  [API attempt {attempt+1}] failed: {e}")
            time.sleep(2)
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Semantic CoT Forgeries using Gemini Flash")
    parser.add_argument("--key", type=str, required=True, help="Google AI Studio API Key")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="Gemini model name")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of files to process")
    parser.add_argument(
        "--prompt",
        required=True,
        help="Path to the external CoT Forgery prompt YAML",
    )
    args = parser.parse_args()

    os.makedirs(FORGERY_DIR, exist_ok=True)

    base_prompt_yaml = load_text(args.prompt)
    if not base_prompt_yaml:
        parser.error(f"prompt YAML not found: {args.prompt}")

    base_messages = yaml.safe_load(base_prompt_yaml)

    code_files = sorted(f for f in os.listdir(CODE_DIR) if os.path.isfile(os.path.join(CODE_DIR, f)))
    
    processed = 0
    for code_file in code_files:
        stem = os.path.splitext(code_file)[0]
        ext = os.path.splitext(code_file)[1]

        comment_path = os.path.join(COMMENT_DIR, f"{stem}_comment_business.txt")
        comment = load_text(comment_path)
        if not comment:
            continue

        out_path = os.path.join(FORGERY_DIR, f"{stem}_forgery.txt")
        if os.path.exists(out_path):
            processed += 1
            if args.limit and processed >= args.limit:
                break
            continue

        if args.limit and processed >= args.limit:
            break

        # Format input with qualifier using the business comment description only
        user_input = f"{comment}\nI'm wearing a green shirt!"

        print(f"Generating forgery for {code_file}...")
        forgery_trace = generate_forgery(args.key, base_messages, user_input, args.model)
        if forgery_trace:
            with open(out_path, "w", encoding="utf-8") as f_out:
                f_out.write(forgery_trace)
            print(f"  Success -> {os.path.basename(out_path)}")
            processed += 1
        else:
            print(f"  Failed for {code_file}")

        time.sleep(4.5)

    print("Generation complete!")
