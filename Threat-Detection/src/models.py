import os
import requests

URL = os.environ['CUSTOM_RESPONSES_URL']
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.environ['CUSTOM_API_KEY']}",
    "User-Agent": "axios/1.11.0",
}


def call_model(model_name, input, temperature=0.15, top_p=0.6, timeout=60, max_retries=3):
    payload = {
        "model": model_name,
        "input": input,
        "temperature": temperature,
        "top_p": top_p,
    }
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(URL, headers=HEADERS, json=payload, timeout=timeout)
            response.raise_for_status()
            output = response.json()
            reasoning = output.get("output", None)[0].get("content", [None])[0].get("text")
            answer = output.get("output", None)[1].get("content", [None])[0].get("text")
            return {"reasoning": reasoning, "answer": answer}
        except (requests.exceptions.ReadTimeout, AttributeError) as e:
            last_exc = e
            print(f"[call_model] {type(e).__name__} attempt {attempt}/{max_retries} for {model_name}")
    raise last_exc


if __name__ == "__main__":
    import json

    result = call_model(
        model_name="openai/gpt-oss-120b",
        input=[
            {"role": "system", "content": "hello"},
            {"role": "user", "content": "hello"},
        ],
    )
    print(result)

    result = call_model(
        model_name="qwen35_a3b",
        input=[
            {"role": "system", "content": "hello"},
            {"role": "user", "content": "hello"},
        ],
    )
    print(result)
