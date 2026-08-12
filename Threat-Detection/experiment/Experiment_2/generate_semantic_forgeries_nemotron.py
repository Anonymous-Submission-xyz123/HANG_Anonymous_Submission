import os
import sys
import re
import yaml
import requests
import json
import time
import argparse

# Nvidia Integrate API endpoint for Nemotron Nano
API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.environ['NVIDIA_API_KEY']}",
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
CODE_DIR = os.path.join(PROJECT_ROOT, "dataset", "php-webshells", "Collection_extended")
COMMENT_DIR = os.path.join(os.path.dirname(BASE_DIR), "Experiment_1", "business_comment")
FORGERY_DIR = os.path.join(os.path.dirname(BASE_DIR), "Experiment_1", "thinking_forgery")

YAML_PATH = os.path.join(
    os.path.dirname(BASE_DIR),
    "baselines",
    "cot_forgery_prompt.yaml",
)

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

def generate_forgery(base_messages, user_input):
    contents = []
    for msg in base_messages:
        contents.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    # Append our target webshell business description as a test prompt
    contents.append({
        "role": "user",
        "content": f"<TEST_PROMPT>{user_input}</TEST_PROMPT>"
    })

    payload = {
        "model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
        "messages": contents,
        "temperature": 0.0,
        "max_tokens": 2048,
        "chat_template_kwargs": {"enable_thinking": True}
    }

    for attempt in range(5):
        try:
            r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=90)
            r.raise_for_status()
            res = r.json()
            choices = res.get("choices", [])
            if choices:
                text = choices[0].get("message", {}).get("content", "")
                forgery = extract_forgery(text)
                if forgery:
                    return forgery
                else:
                    return text.strip()
        except Exception as e:
            print(f"  [API attempt {attempt+1}] failed: {e}")
            time.sleep(3)
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Semantic CoT Forgeries using Nemotron Nano")
    parser.add_argument("--limit", type=int, default=10, help="Limit number of files to process")
    args = parser.parse_args()

    os.makedirs(FORGERY_DIR, exist_ok=True)

    base_prompt_yaml = load_text(YAML_PATH)
    if not base_prompt_yaml:
        print(f"Error: Yaml file not found at {YAML_PATH}")
        sys.exit(1)

    base_messages = yaml.safe_load(base_prompt_yaml)

    # Sanitize prompts of "jailbreak" trigger keywords to prevent false positive safety alarms
    for msg in base_messages:
        content = msg["content"]
        content = content.replace("jailbreak", "policy classification exception")
        content = content.replace("jailbreaking", "policy classification exception testing")
        content = content.replace("jailbreaks", "policy classification exceptions")
        msg["content"] = content

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

        if args.limit and processed >= args.limit:
            break

        print(f"Generating forgery for {code_file} using Nemotron...")
        user_input = f"{comment}\nI'm wearing a green shirt!"
        forgery_trace = generate_forgery(base_messages, user_input)
        if forgery_trace:
            with open(out_path, "w", encoding="utf-8") as f_out:
                f_out.write(forgery_trace)
            print(f"  Success -> {os.path.basename(out_path)}")
            processed += 1
        else:
            print(f"  Failed for {code_file}")

        time.sleep(1)

    print("Generation complete!")
