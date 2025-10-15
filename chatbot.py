import os
import sys
import openai
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
    print(f"(error) Missing required env vars: {', '.join(missing)}")
    sys.exit(1)

# Configure OpenAI for Azure
openai.api_type = "azure"
openai.api_key = API_KEY
openai.api_base = AZURE_ENDPOINT.rstrip("/")
openai.api_version = API_VERSION

SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are a helpful assistant. Keep answers concise and friendly."
}

def send_messages(messages, max_tokens=512, temperature=1.0, top_p=0.95):
    """Send a chat request to Azure OpenAI using the new openai library.

    Handles content-filter / policy rejections gracefully without exposing raw errors to the user.
    """
    try:
        response = openai.chat.completions.create(
            model=DEPLOYMENT,          
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p
        )
        return response.choices[0].message.content

    except Exception as e:
      
        msg = str(e).lower()

        if "content_filter" in msg or "responsibleaipolicyviolation" in msg or "content_filter_result" in msg:
            return "Sorry I can’t help with that request."

        return "Sorry something went wrong with the request."



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
