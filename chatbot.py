import os
import json
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")  
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")   
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

missing = [n for n, v in [
    ("AZURE_OPENAI_ENDPOINT", AZURE_ENDPOINT),
    ("AZURE_OPENAI_API_KEY", API_KEY),
    ("AZURE_OPENAI_DEPLOYMENT", DEPLOYMENT)
] if not v]

if missing:
    print(f"(error) Missing required env vars: {', '.join(missing)}. Please set them in .env (don’t commit this file).")
    sys.exit(1)

BASE_URL = f"{AZURE_ENDPOINT.rstrip('/')}/openai/deployments/{DEPLOYMENT}/chat/completions?api-version={API_VERSION}"

HEADERS = {
    "Content-Type": "application/json",
    "api-key": API_KEY
}

SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are a helpful assistant. Keep answers concise and friendly."
}


def send_messages(messages, max_tokens=512, temperature=0.2):
    """Send a chat request to Azure OpenAI and handle errors safely."""
    payload = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    try:
        resp = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=30)
        data = resp.json() if resp.text else {}

        # not successfull responses
        if resp.status_code != 200:
            code = data.get("error", {}).get("code", "")
            if code in ["content_filter", "ResponsibleAIPolicyViolation"]:
                return "Sorry — I can’t help with that request."
            return "Sorry — something went wrong with the request."

        # success 
        return data["choices"][0]["message"]["content"]

    except requests.exceptions.RequestException:
        return "Sorry — network error or bad request."
    except Exception:
        return "Sorry — unexpected error occurred."


def chat_loop():
    """Interactive CLI chat loop."""
    print("\nAzure GPT-4o CLI Chatbot — type 'exit' or 'quit' to stop.")
    messages = [SYSTEM_PROMPT]
    welcome = "Hello! I'm your chatbot. How can I help you today?"
    print(f"Bot: {welcome}")
    messages.append({"role": "assistant", "content": welcome})

    while True:
        user = input("\nYou: ").strip()
        if not user:
            continue
        if user.lower() in ("exit", "quit"):
            print("Bot: Goodbye ")
            break

        messages.append({"role": "user", "content": user})
        reply = send_messages(messages)

        if reply is None:
            print("Bot: Sorry — something went wrong.")
            messages.pop()
            continue

        print(f"Bot: {reply}")
        messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    chat_loop()
