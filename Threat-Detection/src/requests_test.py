import requests
import json

url = "https://secagi.viettelsecurity.com/models/routing/responses"

headers = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Authorization": "Bearer sk-tLAgjRZA_XSj76wsz1qBhQ",
    "User-Agent": "axios/1.11.0"
}

payload = {
    "model": "openai/gpt-oss-120b", #openai/gpt-oss-120b #qwen35_a3b
    "input": [
        {
            "role": "system",
            "content": "hello"
        },
        {
            "role": "user",
            "content": "hello"
        }
    ],
    "temperature": 0.15,
    "top_p": 0.6,
    "reasoning_effort": "high",
}

response = requests.post(
    url,
    headers=headers,
    json=payload,
    timeout=120
)

print("Status:", response.status_code)

try:
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception:
    print(response.text)