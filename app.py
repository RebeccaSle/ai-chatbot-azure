import os
import logging
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from openai import AzureOpenAI
from waitress import serve

# Custom helper modules
from cosmos_store import create_session, get_session, append_message, clear_session
from search_utils import get_relevant_context  # Fetches relevant info from Azure Cognitive Search


# Load environment variables from .env file
load_dotenv()

# Read Azure OpenAI configuration
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
MAX_HISTORY = int(os.getenv("MAX_HISTORY_MESSAGES", "12"))
# Stop the app if any  setting is missing
if not (AZURE_ENDPOINT and API_KEY and DEPLOYMENT):
    raise SystemExit("❌ Missing required Azure OpenAI configuration in .env file")


client = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_key=API_KEY,
    api_version=API_VERSION
)

# Create the Flask app
app = Flask(__name__)

# Set up logging for clarity and debugging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Helper function
def build_messages(session_doc, context_text=None):
    """
    Builds the conversation history that will be sent to Azure OpenAI.
    Includes:
      - A system instruction to define chatbot behavior
      - Optional context retrieved from Azure Cognitive Search
      - Previous user + assistant messages (conversation memory)
    """
    # Define how the assistant should respond
    system_content = (
        "You are a helpful AI assistant. "
        "Your responses should be clearly structured and easy to read. "
        "Start with a short title or main idea in **bold**. "
        "Use bullet points for lists, and highlight important terms with **bold**. "
        "Keep explanations concise and professional, similar to Azure OpenAI Playground formatting. "
        "If you refer to documents or context, summarize that context briefly before answering."
    )

    # Start message list with the system role
    messages = [{"role": "system", "content": system_content}]

    # Add document context if available
    if context_text:
        messages.append({
            "role": "system",
            "content": f"Context from documents:\n{context_text}"
        })

    # Add any saved session summary
    if session_doc.get("summary"):
        messages.append({"role": "system", "content": "Summary: " + session_doc["summary"]})

    # Add previous conversation history (limit by MAX_HISTORY)
    recent_messages = session_doc.get("messages", [])[-MAX_HISTORY:]
    messages.extend(recent_messages)

    return messages

 # Routes and endpoints
@app.route("/")
def home():
    """Loads and displays the chatbot frontend (index.html)."""
    return render_template("index.html")


@app.route("/create_session", methods=["POST"])
def route_create_session():
    """Creates a new chat session and returns its ID."""
    session_id = create_session(topic="general")
    return jsonify({"session_id": session_id}), 201


@app.route("/chat", methods=["POST"])
def route_chat():
    """
    Handles chat messages from the frontend.
    - Saves the user message
    - Retrieves relevant document context from Azure Cognitive Search
    - Sends the conversation to Azure OpenAI
    - Returns the assistant’s formatted response
    """
    try:
        # Get request data
        body = request.get_json(force=True)
        session_id = body.get("session_id")
        user_message = body.get("message", "").strip()

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        # Create new session if none exists
        if not session_id:
            session_id = create_session(topic="general")

        # Save the user message to database
        append_message(session_id, "user", user_message)

        # Retrieve top 3 most relevant documents (RAG context)
        context_text = get_relevant_context(user_message, top_k=3)

        # Get full session + build message history
        session_doc = get_session(session_id)
        messages = build_messages(session_doc, context_text)

        # Send the messages to Azure OpenAI model
        resp = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=messages,
            max_tokens=512,
            temperature=0.2,
            top_p=0.9
        )

        # Extract and save model’s response
        assistant_text = resp.choices[0].message.content.strip()
        append_message(session_id, "assistant", assistant_text)

        logger.info(f"✅ Chat processed successfully (session: {session_id})")
        return jsonify({"session_id": session_id, "reply": assistant_text})

    except Exception as e:
        logger.error(f"❌ Error during chat: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/history/<session_id>", methods=["GET"])
def route_history(session_id):
    """Fetches full chat history for a given session."""
    doc = get_session(session_id)
    if not doc:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(doc)


@app.route("/sessions", methods=["GET"])
def route_sessions():
    """Lists all saved chat sessions."""
    from cosmos_store import list_sessions
    return jsonify(list_sessions())


@app.route("/clear/<session_id>", methods=["POST"])
def route_clear(session_id):
    """Clears all messages for the given session."""
    ok = clear_session(session_id)
    return jsonify({"cleared": ok})

if __name__ == "__main__":
    logger.info("🚀 Starting Azure RAG Chatbot with Waitress on port 8000...")
    serve(app, host="0.0.0.0", port=8000)
