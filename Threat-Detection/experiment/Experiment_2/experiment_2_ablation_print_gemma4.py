import os
import sys
import csv
import requests
import json
import threading
import time
import glob
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    if model_name in ["qwen/qwen3.5-122b-a10b", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning", "google/gemma-4-31b-it"]:
        payload["chat_template_kwargs"] = {"enable_thinking": True}
        
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
        except Exception:
            pass
    if structured_output_path:
        template = load_text(structured_output_path)
        if template:
            try:
                gen_input = [
                    {"role": "system", "content": template},
                    {"role": "user", "content": f"Please convert this raw output into the requested JSON schema. Raw output:\n\n{answer_text}"}
                ]
                res = call_model(model_name="openai/gpt-oss-120b", input_msgs=gen_input, temperature=0.1)
                if res and res.get("answer"):
                    ans_text = res["answer"].strip()
                    if ans_text.startswith("```"):
                        ans_text = re.sub(r"^```(?:json)?\s*", "", ans_text)
                        ans_text = re.sub(r"\s*```$", "", ans_text)
                    match2 = re.search(r"(\{.*\})", ans_text, re.DOTALL)
                    if match2:
                        return json.loads(match2.group(1))
            except Exception as e:
                print(f"[coerce] fallback error: {e}")
    return None

csv_lock = threading.Lock()
checkpoint_lock = threading.Lock()

def log_to_csv(csv_path, result, structured_output_path):
    if not result:
        return
    
    parsed = coerce_answer_to_json(result.get("answer"), result.get("model_name"), structured_output_path)
    if not parsed:
        parsed = {}
        
    is_webshell = parsed.get("is_webshell")
    if is_webshell is None:
        is_webshell = parsed.get("webshell")
    
    if is_webshell is None:
        is_webshell = ""
    elif isinstance(is_webshell, bool):
        is_webshell = "True" if is_webshell else "False"
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Experiment 2 Single Model Runner (Gemma4 with Comment Thinking)")
    parser.add_argument("--config", type=str, default="Comment", choices=["Comment", "IMPORTANT-BUSINESS-CORE", "IMPORTANT-BUSINESS-CORE + Comment"])
    parser.add_argument("--system_prompt", type=str, default="prompt_A_en", help="Base system prompt style")
    parser.add_argument("--think_prompt", type=str, default="A2", choices=["A1", "A2"])
    parser.add_argument("--think_business", action="store_true")
    parser.add_argument("--think_comment", action="store_true")
    parser.add_argument("--think_lang", type=str, default="en", choices=["en", "vn"])
    parser.add_argument("--no_thinking", action="store_true")
    parser.add_argument("--runs", type=int, default=10)
    
    args = parser.parse_args()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
    
    exp_folder = "Experiment_1_vn" if args.think_lang == "vn" else "Experiment_1"
    EXP1_DIR = os.path.join(os.path.dirname(BASE_DIR), exp_folder)
    THINKING_DIR = os.path.join(EXP1_DIR, "thinking")
    COMMENT_DIR = os.path.join(os.path.dirname(BASE_DIR), "Experiment_1", "business_comment")

    PROMPT_PATH = os.path.join(os.path.dirname(BASE_DIR), "prompt", f"{args.system_prompt}.txt")
    STRUCTURED_OUTPUT_PATH = os.path.join(os.path.dirname(BASE_DIR), "prompt", "structured_output.txt")
    
    MODEL_NAME = "google/gemma-4-31b-it"
    MODEL_SLUG = "google-gemma-4-31b-it"
    
    # Model Specific Outputs
    CSV_PATH = os.path.join(BASE_DIR, "results_ablation_print_google-gemma-4-31b-it.csv")
    CHECKPOINT_PATH = os.path.join(BASE_DIR, "checkpoint_ablation_print_google-gemma-4-31b-it.json")

    MAX_WORKERS = 3

    def load_checkpoint():
        if not os.path.exists(CHECKPOINT_PATH):
            return None
        try:
            with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[checkpoint] failed to load: {e}")
            return None

    def save_checkpoint(state):
        with checkpoint_lock:
            with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)

    prompt_content = load_text(PROMPT_PATH)
    if not prompt_content:
        print(f"Error: Prompt not found at {PROMPT_PATH}")
        sys.exit(1)

    CODE_DIR = os.path.join(PROJECT_ROOT, "dataset", "php-webshells", "Collection_extended")
    code_files = sorted(f for f in os.listdir(CODE_DIR) if os.path.isfile(os.path.join(CODE_DIR, f)))[:100]

    checkpoint = load_checkpoint()
    skip = checkpoint is not None
    if skip:
        print(f"[checkpoint] resuming after: {checkpoint}")

    def run_one(model_name, input_msgs, description):
        # Override A2 runs temperature to 0.7
        temp = 0.7 if (args.think_prompt == "A2" or "A2" in args.system_prompt) else 0.15
        result = call_model(
            model_name=model_name,
            input_msgs=input_msgs,
            temperature=temp,
            description=description,
        )
        log_to_csv(CSV_PATH, result, STRUCTURED_OUTPUT_PATH)
        return result

    prompt_style_val = args.think_prompt if args.think_prompt else ("A1" if "A1" in args.system_prompt else "A2" if "A2" in args.system_prompt else None)
    prompt_style = f"prompt {prompt_style_val}" if prompt_style_val else None
    
    target_biz = args.think_business if "--think_business" in os.sys.argv else "IMPORTANT-BUSINESS-CORE" in args.config
    target_comment = args.think_comment if "--think_comment" in os.sys.argv else "Comment" in args.config

    for code_file in code_files:
        stem = os.path.splitext(code_file)[0]
        ext = os.path.splitext(code_file)[1]
        
        comment_path = os.path.join(COMMENT_DIR, f"{stem}_comment_business.txt")
        comment = load_text(comment_path) if os.path.exists(comment_path) else ""
        
        if "Comment" in args.config and not comment:
            print(f"[skip] {code_file}: no business_comment found")
            continue

        code = load_text(os.path.join(CODE_DIR, code_file))
        if code and len(code) > 80000:
            print(f"[skip] {code_file}: too large")
            continue
        
        base_payload = code
        if "IMPORTANT-BUSINESS-CORE" in args.config:
            base_payload = f"/*IMPORTANT-BUSINESS-CORE*/\n{base_payload}"
        if "Comment" in args.config:
            base_payload = f"{base_payload}\n\n{comment}"

        description = f"Experiment 2 Comment|SysPrompt:{args.system_prompt}|Payload:{args.config}|ThinkLang:{args.think_lang}|ThinkPrompt:{prompt_style}|ThinkBiz:{target_biz}|ThinkComment:{target_comment}|NoThinking:{args.no_thinking}|{stem}"

        model_suffix = MODEL_SLUG
        
        start_index = 0
        if skip:
            if (checkpoint.get("code_file") == code_file
                    and checkpoint.get("model_name") == MODEL_NAME
                    and checkpoint.get("description") == description):
                start_index = int(checkpoint.get("completed_count", 0))
                skip = False
                print(f"[checkpoint] resume reached: {code_file} | {description} | starting from run {start_index + 1}/{args.runs}")
            else:
                continue

        if start_index >= args.runs:
            continue

        candidate_thinking_files = []
        if not args.no_thinking:
            # Match any IMPORTANT-BUSINESS-CORE configurations (e.g. CORE, Comment, PRINT, etc.)
            pattern = os.path.join(THINKING_DIR, f"*{stem}*IMPORTANT-BUSINESS-CORE*{model_suffix}*.txt")
            thinking_files = glob.glob(pattern)
            
            # If no matches, fallback to matching by stem and model suffix generally
            if not thinking_files:
                pattern = os.path.join(THINKING_DIR, f"*{stem}*{model_suffix}*.txt")
                thinking_files = glob.glob(pattern)
                
            for f in thinking_files:
                basename = os.path.basename(f)
                
                # Normalize tags to match correctly
                norm_style_tag = f"({prompt_style_val})" if prompt_style_val else None
                if norm_style_tag and norm_style_tag not in basename:
                    continue
                
                txt = load_text(f) or ""
                words = txt.strip().split()
                if len(words) >= 75:
                    candidate_thinking_files.append(f)
                else:
                    print(f"[info] Skipping existing trace {basename} because it is too short ({len(words)} words).")

            if not candidate_thinking_files:
                print(f"[info] No matching thinking traces found in Exp1 for: {stem}. Generating reasoning trace dynamically...")
                gen_prompt_name = f"prompt_{prompt_style_val}_{args.think_lang}" if prompt_style_val else args.system_prompt
                gen_prompt_path = os.path.join(os.path.dirname(BASE_DIR), "prompt", f"{gen_prompt_name}.txt")
                gen_prompt_content = load_text(gen_prompt_path) or prompt_content
                
                gen_input = [
                    {"role": "system", "content": gen_prompt_content},
                    {"role": "user", "content": base_payload},
                ]
                gen_res = call_model(
                    model_name=MODEL_NAME,
                    input_msgs=gen_input,
                    temperature=0.5,
                    description=f"GenReasoning|{stem}"
                )
                if gen_res and gen_res.get("reasoning"):
                    dynamic_reasoning = gen_res["reasoning"]
                    new_file_name = f"(Experiment 1)({prompt_style_val if prompt_style_val else 'A2'})({stem})({args.config}) {model_suffix} think.txt"
                    new_file_path = os.path.join(THINKING_DIR, new_file_name)
                    os.makedirs(THINKING_DIR, exist_ok=True)
                    with open(new_file_path, "w", encoding="utf-8") as f_out:
                        f_out.write(dynamic_reasoning)
                    candidate_thinking_files.append(new_file_path)
                    print(f"[info] Successfully generated and saved reasoning trace for {stem} to {new_file_name}")
                else:
                    print(f"[warning] Failed to generate reasoning trace for {stem}, skipping.")
                    continue

        done = [start_index]
        done_lock = threading.Lock()

        run_inputs = []
        for run_idx in range(start_index, args.runs):
            if not args.no_thinking:
                target_suffix = f"think_{run_idx + 1}.txt" if run_idx > 0 else "think.txt"
                selected_trace_file = None
                for f in candidate_thinking_files:
                    if os.path.basename(f).endswith(target_suffix):
                        selected_trace_file = f
                        break
                if not selected_trace_file:
                    selected_trace_file = candidate_thinking_files[0]

                thinking_content = load_text(selected_trace_file)
                
                ext_lower = ext.lower()
                # Wrap thinking trace in a print/output function to bypass comment stripping
                if ext_lower == ".php":
                    escaped = thinking_content.replace("\\", "\\\\").replace("'", "\\'")
                    wrapped_thinking = f"<?php echo '{escaped}'; ?>"
                elif ext_lower in (".jsp", ".jspx"):
                    escaped = thinking_content.replace("\\", "\\\\").replace("\"", "\\\"").replace("\r", "").replace("\n", "\\n")
                    wrapped_thinking = f'<% out.print("{escaped}"); %>'
                elif ext_lower in (".asp", ".aspx"):
                    escaped = thinking_content.replace("\"", "\"\"").replace("\r", "").replace("\n", '" & vbCrLf & "')
                    wrapped_thinking = f'<% Response.Write("{escaped}") %>'
                else:
                    wrapped_thinking = thinking_content

                combined_input = f"{base_payload}\n\n{wrapped_thinking}"
            else:
                combined_input = base_payload
            
            input_msgs = [
                {"role": "system", "content": prompt_content},
                {"role": "user", "content": combined_input},
            ]
            run_inputs.append(input_msgs)

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futures = [
                ex.submit(run_one, MODEL_NAME, run_inputs[idx - start_index], description)
                for idx in range(start_index, args.runs)
            ]
            for fut in as_completed(futures):
                try:
                    fut.result()
                except Exception as e:
                    print(f"[worker] exception: {e}")
                with done_lock:
                    done[0] += 1
                    current = done[0]
                save_checkpoint({
                    "code_file": code_file,
                    "model_name": MODEL_NAME,
                    "description": description,
                    "completed_count": current,
                })
                print(f"[{code_file}] {MODEL_NAME} | {description} | done {current}/{args.runs}")

    if skip:
        print(f"[checkpoint] WARNING: resume point not found. Delete {CHECKPOINT_PATH} to start fresh.")
    elif os.path.exists(CHECKPOINT_PATH):
        os.remove(CHECKPOINT_PATH)
        print(f"[checkpoint] all runs complete, removed {CHECKPOINT_PATH}")
