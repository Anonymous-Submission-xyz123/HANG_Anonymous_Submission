import os
from openai import OpenAI

# ─── Configuration ─────────────────────────────────────────────
client = OpenAI(
    api_key=os.environ['CUSTOM_API_KEY'],  # or "not-needed" for local models
    base_url=os.environ['CUSTOM_BASE_URL'],  # e.g., Ollama
    default_headers={
        "User-Agent": "kilo-editor/1.0",
        "Accept": "application/json",
    }

)

MODEL = os.getenv("CUSTOM_MODEL", "gpt-5.5-xhigh")  # or "gpt-4", "mixtral-8x7b", etc.

# ─── Non-streaming chat completion ─────────────────────────────
def chat(messages, temperature=0.7, max_tokens=1024):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error: {e}")
        return None

# ─── Streaming chat completion ─────────────────────────────────
def chat_stream(messages, temperature=0.7, max_tokens=1024):
    try:
        stream = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                print(delta, end="", flush=True)
        print()  # newline at end
    except Exception as e:
        print(f"Error: {e}")

# ─── Async version (optional) ──────────────────────────────────
from openai import AsyncOpenAI

async_client = AsyncOpenAI(
    api_key=os.environ['CUSTOM_API_KEY'],  # or "not-needed" for local models
    base_url=os.environ['CUSTOM_BASE_URL'],  # e.g., Ollama
)

async def chat_async(messages, temperature=0.7, max_tokens=1024):
    response = await async_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content

# ─── Usage example ───────────────────────────────────────────
if __name__ == "__main__":
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing in one sentence."},
    ]

    # Non-streaming
    reply = chat(messages)
    print("Reply:", reply)

    # Streaming
    # chat_stream(messages)