import os
import json
import logging
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX_NAME", "kb-index")

app = Flask(__name__, static_folder="static", static_url_path="")


try:
    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=AZURE_SEARCH_INDEX,
        credential=AzureKeyCredential(AZURE_SEARCH_KEY)
    )
    print("Azure Search client initialized successfully.")
except Exception as e:
    print(f" [Init ERROR] Failed to initialize SearchClient: {e}")

try:
    openai_client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
        api_version="2024-02-15-preview"
    )
    print("Azure OpenAI client initialized successfully.")
except Exception as e:
    print(f"[Init ERROR] Failed to initialize OpenAI client: {e}")

#semantic implementation
def semantic_search(query):
    """
    Performs semantic search using Azure Cognitive Search.
    Returns content and score or none on failure.
    """
    try:
        results = search_client.search(
            search_text=query,
            query_type="semantic", 
            semantic_configuration_name="default",
            top=3
        )

        for result in results:
            content = result.get("content") or result.get("text") or json.dumps(result)
            score = result.get("@search.score", 0)
            return content, score

        return None, None

    except Exception as e:
        print(f"[semantic_search ERROR]: {e}")
        return None, None

@app.route("/chat", methods=["POST"])
def route_chat():
    """
    Handles chat requests from frontend and returns an AI-generated answer.
    """
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        search_context, search_score = semantic_search(user_message)

        if search_context:
            system_prompt = (
                "You are a helpful AI assistant. Use the context below to answer the user's question:\n\n"
                f"Context: {search_context}\n\n"
                "If the context is not sufficient, respond naturally based on your general knowledge."
            )
        else:
            system_prompt = (
                "You are a helpful AI assistant. Answer the user's question based on your general knowledge."
            )

        response = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=400
        )

        ai_reply = response.choices[0].message.content.strip()
        return jsonify({"reply": ai_reply})

    except Exception as e:
        logging.exception("Error in /chat endpoint")
        return jsonify({"error": str(e)}), 500


@app.route("/")
def index():
    """Serves the main frontend file."""
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    from waitress import serve
    print("🚀 Running on http://0.0.0.0:8000")
    serve(app, host="0.0.0.0", port=8000)
