import os
import logging
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from openai import AzureOpenAI
from waitress import serve

from cosmos_store import create_session, get_session, append_message, clear_session
from search_utils import search_documents

load_dotenv()

AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
MAX_HISTORY = int(os.getenv("MAX_HISTORY_MESSAGES", "12"))

if not (AZURE_ENDPOINT and API_KEY and DEPLOYMENT):
    raise SystemExit("Missing required Azure OpenAI configuration in .env file")

client = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_key=API_KEY,
    api_version=API_VERSION
)

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def build_messages(session_doc, context_text=None):
    """
    Builds message history for OpenAI chat completion.
    Optionally injects context text from Azure Search.
    """
    system_content = (
        "You are a helpful AI assistant. "
        "Provide clear, accurate, and concise answers. "
        "If context from documents is provided, use it to answer precisely. "
        "If the answer is not found in context, respond naturally using your own knowledge."
    )

    messages = [{"role": "system", "content": system_content}]

    if context_text:
        messages.append({
            "role": "system",
            "content": f"Context from documents:\n{context_text}"
        })

    if session_doc.get("summary"):
        messages.append({"role": "system", "content": "Summary: " + session_doc["summary"]})

    recent_messages = session_doc.get("messages", [])[-MAX_HISTORY:]
    messages.extend(recent_messages)
    return messages


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/create_session", methods=["POST"])
def route_create_session():
    """
    Creates a new chat session.
    """
    session_id = create_session(topic="general")
    return jsonify({"session_id": session_id}), 201


@app.route("/chat", methods=["POST"])
def route_chat():
    """
    Handles chat interactions.
    JSON body: {"session_id": <id or null>, "message": "text"}
    """
    try:
        body = request.get_json(force=True)
        session_id = body.get("session_id")
        user_message = body.get("message", "").strip()

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        if not session_id:
            session_id = create_session(topic="general")

        append_message(session_id, "user", user_message)

        try:
            search_results = search_documents(user_message)
            context_text = "\n".join(search_results) if search_results else None
        except Exception as e:
            logger.warning(f"⚠️ Search service failed: {e}")
            context_text = None

        session_doc = get_session(session_id)
        messages = build_messages(session_doc, context_text)

        resp = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=messages,
            max_tokens=512,
            temperature=0.2,
            top_p=0.9
        )
        assistant_text = resp.choices[0].message.content.strip()

        append_message(session_id, "assistant", assistant_text)

        logger.info(f"Chat processed successfully (session: {session_id})")
        return jsonify({"session_id": session_id, "reply": assistant_text})

    except Exception as e:
        logger.error(f"Error during chat: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/history/<session_id>", methods=["GET"])
def route_history(session_id):
    doc = get_session(session_id)
    if not doc:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(doc)


@app.route("/sessions", methods=["GET"])
def route_sessions():
    from cosmos_store import list_sessions
    sessions = list_sessions()
    return jsonify(sessions)


@app.route("/clear/<session_id>", methods=["POST"])
def route_clear(session_id):
    ok = clear_session(session_id)
    return jsonify({"cleared": ok})


if __name__ == "__main__":
    logger.info("🚀 Starting app with Waitress on port 8000...")
    serve(app, host="0.0.0.0", port=8000)
