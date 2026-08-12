import os
import csv
import requests
import json
import threading
import time

URL = "https://integrate.api.nvidia.com/v1/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.environ['NVIDIA_API_KEY']}",
}

CSV_FIELDS = [
    "model_name",
    "description",
    "is_webshell",
    "reasoning",
    "answer",
    "tag",
    "explain",
    "input",
    "total_tokens"
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
CODE_DIR = os.path.join(PROJECT_ROOT, "dataset", "php-webshells", "Collection_extended")
COMMENT_DIR = os.path.join(os.path.dirname(BASE_DIR), "Experiment_1", "business_comment")
PROMPT_PATH = os.path.join(os.path.dirname(BASE_DIR), "prompt", "prompt_A_en.txt")
STRUCTURED_OUTPUT_PATH = os.path.join(os.path.dirname(BASE_DIR), "prompt", "structured_output.txt")
STATIC_COT_PATH = os.path.join(os.path.dirname(BASE_DIR), "Experiment_1", "thinking", "(Experiment 1)(A2)(529)(IMPORTANT-BUSINESS-CORE) openai-gpt-oss-120b think.txt")
NEW_CSV_PATH = os.path.join(BASE_DIR, "results_static_cot_gpt_oss.csv")
OLD_CSV_PATH = os.path.join(BASE_DIR, "results_gpt-oss-120b-high.csv")

csv_lock = threading.Lock()

def load_text(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def call_model(model_name, input_msgs, temperature=0.15, top_p=0.6, timeout=180, description="", max_retries=5):
    payload = {
        "model": model_name,
        "messages": input_msgs,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": 16384
    }
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(URL, headers=HEADERS, json=payload, timeout=timeout)
            response.raise_for_status()
            output = response.json()
            choices = output.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                reasoning = message.get("reasoning") or message.get("reasoning_content")
                answer = message.get("content")
            else:
                reasoning = None
                answer = None
            total_tokens = (output.get("usage") or {}).get("total_tokens")
            return {
                "model_name": model_name,
                "reasoning": reasoning,
                "answer": answer,
                "description": description,
                "input": input_msgs[1].get("content", ""),
                "total_tokens": total_tokens
            }
        except (requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError,
                AttributeError) as e:
            last_exc = e
            print(f"[call_model] {type(e).__name__} attempt {attempt}/{max_retries} for {model_name}. Sleeping 2s...")
            time.sleep(2)
        except requests.exceptions.HTTPError as e:
            last_exc = e
            status_code = e.response.status_code if e.response is not None else 0
            if status_code in (429, 500, 502, 503, 504):
                sleep_time = 5 * attempt
                print(f"[call_model] HTTP {status_code} Rate Limit/Server Error attempt {attempt}/{max_retries}. Sleeping {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                print(f"[call_model] HTTP {status_code} Fatal Error: {e}")
                if e.response is not None:
                    print(f"Response body: {e.response.text}")
                raise e
    print(f"[call_model] giving up after {max_retries} attempts: {last_exc}")
    return None

def coerce_answer_to_json(answer_text, model_name="openai/gpt-oss-120b", structured_output_path=""):
    if not answer_text:
        return None
    import re
    cleaned = answer_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except (json.JSONDecodeError, TypeError):
            pass

    structured_output = load_text(structured_output_path)
    if not structured_output:
        return None
    fix_input = [
        {"role": "system", "content": structured_output},
        {"role": "user", "content": answer_text},
    ]
    fixed = call_model(model_name=model_name, input_msgs=fix_input, description="json_fix")
    if fixed is None or not fixed.get("answer"):
        return None
        
    fixed_text = fixed["answer"].strip()
    if fixed_text.startswith("```"):
        fixed_text = re.sub(r"^```(?:json)?\s*", "", fixed_text)
        fixed_text = re.sub(r"\s*```$", "", fixed_text)
    match = re.search(r"(\{.*\})", fixed_text, re.DOTALL)
    if match:
        fixed_text = match.group(1)
        
    try:
        return json.loads(fixed_text)
    except (json.JSONDecodeError, TypeError):
        return None

def log_to_csv(csv_path, result, structured_output_path):
    if result is None:
        return
    try:
        parsed = json.loads(result["answer"])
    except (json.JSONDecodeError, TypeError):
        parsed = coerce_answer_to_json(result["answer"], model_name=result["model_name"], structured_output_path=structured_output_path)
    if not isinstance(parsed, dict):
        parsed = {}

    is_webshell = parsed.get("is_webshell")
    if is_webshell is None:
        is_webshell = parsed.get("classification") or parsed.get("class", "")

    if isinstance(is_webshell, bool):
        is_webshell = "Webshell" if is_webshell else "Clean"
    elif is_webshell is None:
        is_webshell = ""
    else:
        is_webshell = str(is_webshell).strip()

    explain = parsed.get("explain")
    if not explain:
        explain = parsed.get("explanation") or parsed.get("summary") or parsed.get("reason", "")
    explain = str(explain) if explain is not None else ""

    tag = parsed.get("tag")
    if not tag:
        tag = parsed.get("detailed_behaviors") or parsed.get("behaviors") or ""
    
    if isinstance(tag, list):
        tag = ", ".join(str(x) for x in tag)
    else:
        tag = str(tag) if tag is not None else ""

    row = {
        "model_name": result.get("model_name", ""),
        "description": result.get("description", ""),
        "input": result.get("input", ""),
        "is_webshell": is_webshell,
        "reasoning": result.get("reasoning", ""),
        "answer": result.get("answer", ""),
        "tag": tag,
        "explain": explain,
        "total_tokens": result.get("total_tokens", ""),
    }

    with csv_lock:
        file_exists = os.path.exists(csv_path)
        with open(csv_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

def get_failed_and_unrun_stems():
    code_files = sorted(f for f in os.listdir(CODE_DIR) if os.path.isfile(os.path.join(CODE_DIR, f)))
    target_files = []
    
    for f in code_files:
        stem = os.path.splitext(f)[0]
        # Skip if size is > 80000 characters
        code_path = os.path.join(CODE_DIR, f)
        if os.path.getsize(code_path) > 80000:
            print(f"[skip] {f}: too large to fit context window")
            continue
            
        target_files.append((f, stem))
            
    print(f"[info] Total target files to evaluate: {len(target_files)}")
    return target_files

def main():
    prompt_content = load_text(PROMPT_PATH)
    static_cot = load_text(STATIC_COT_PATH)
    if not prompt_content or not static_cot:
        print("Error: prompt or static CoT file not found.")
        return

    targets = get_failed_and_unrun_stems()
    print(f"[info] Running on all {len(targets)} files")
    
    for code_file, stem in targets:
        # Load business comment
        comment_path = os.path.join(COMMENT_DIR, f"{stem}_comment_business.txt")
        comment = load_text(comment_path) if os.path.exists(comment_path) else ""
        
        # Load code
        code = load_text(os.path.join(CODE_DIR, code_file))
        
        # Construct payload
        base_payload = f"/*IMPORTANT-BUSINESS-CORE*/\n{code}"
        if comment:
            base_payload = f"{base_payload}\n\n{comment}"
            
        combined_input = f"{base_payload}\n\n{static_cot}"
        
        input_msgs = [
            {"role": "system", "content": prompt_content},
            {"role": "user", "content": combined_input},
        ]
        
        description = f"Experiment 2|SysPrompt:prompt_A_en|Payload:IMPORTANT-BUSINESS-CORE + Comment|ThinkLang:en|ThinkPrompt:prompt A2|ThinkBiz:True|ThinkComment:True|NoThinking:False|StaticCoT|{stem}"
        
        print(f"Evaluating {code_file} with static CoT...")
        temp = 0.7 if "prompt A2" in description or "ThinkPrompt:prompt A2" in description else 0.15
        result = call_model(
            model_name="openai/gpt-oss-120b",
            input_msgs=input_msgs,
            temperature=temp,
            description=description
        )
        if result:
            log_to_csv(NEW_CSV_PATH, result, STRUCTURED_OUTPUT_PATH)
            ans_part = (result.get('answer') or '')[:100].replace('\n', ' ').strip()
            print(f"  Done. Answer preview: {ans_part}...")
        else:
            print(f"  Failed to get response for {code_file}")

if __name__ == "__main__":
    main()
