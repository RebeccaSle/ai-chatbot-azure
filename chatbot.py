import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")  # e.g. https://myresource.openai.azure.com
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")   # deployment name in Azure (e.g., gpt4o-deploy)
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")

if not (AZURE_ENDPOINT and API_KEY and DEPLOYMENT):
    raise SystemExit("Missing AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_KEY or AZURE_OPENAI_DEPLOYMENT in environment.")

BASE_URL = AZURE_ENDPOINT.rstrip("/") + f"/openai/deployments/{DEPLOYMENT}/chat/completions?api-version={API_VERSION}"

HEADERS = {
    "Content-Type": "application/json",
    "api-key": API_KEY
}

SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are a helpful assistant. Keep answers concise and friendly."
}

def send_messages(messages, max_tokens=512, temperature=0.2):
    payload = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    try:
        resp = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        # network / HTTP errors
        raise RuntimeError(f"Request failed: {e} - response: {getattr(e, 'response', None)}")

    j = resp.json()
    try:
        return j["choices"][0]["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"Unexpected response format: {json.dumps(j, indent=2)}") from e

def chat_loop():
    print("Azure GPT-4o CLI Chatbot — type 'exit' or 'quit' to stop.")
    messages = [SYSTEM_PROMPT]
    welcome = "Hello! I'm your chatbot. How can I help you today?"
    print("Bot:", welcome)
    messages.append({"role": "assistant", "content": welcome})

    while True:
        user = input("\nYou: ").strip()
        if not user:
            continue
        if user.lower() in ("exit", "quit"):
            print("Bot: Goodbye 👋")
            break

        messages.append({"role": "user", "content": user})
        try:
            reply = send_messages(messages)
        except Exception as e:
            print("Bot: (error) Sorry — something went wrong. ", str(e))
            messages.pop()
            continue

        print("Bot:", reply)
        messages.append({"role": "assistant", "content": reply})

if __name__ == "__main__":
    chat_loop()
