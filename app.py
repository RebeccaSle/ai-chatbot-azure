import os
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from openai import AzureOpenAI
from cosmos_store import create_session, get_session, append_message, clear_session

load_dotenv()

AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
MAX_HISTORY = int(os.getenv("MAX_HISTORY_MESSAGES", "12"))

if not (AZURE_ENDPOINT and API_KEY and DEPLOYMENT):
    raise SystemExit("Missing required Azure OpenAI configuration.")

client = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_key=API_KEY,
    api_version=API_VERSION
)

app = Flask(__name__)

# topics passed here, for now one
FIXED_TOPIC = "cooking"

def build_messages(session_doc):
    """
    Build the message history with a system prompt restricted to the fixed topic.
    """
    system_content = (
        f"You are a helpful assistant that ONLY answers questions about {FIXED_TOPIC}. "
        f"If a question is outside this topic, reply: 'Sorry, I only answer questions about {FIXED_TOPIC}.' "
        "Provide concise, clear, and friendly responses."
    )

    messages = [{"role": "system", "content": system_content}]

    if session_doc.get("summary"):
        messages.append({"role": "system", "content": "Summary: " + session_doc["summary"]})

    # append max history which is 21 chats
    recent_messages = session_doc.get("messages", [])[-MAX_HISTORY:]
    messages.extend(recent_messages)

    return messages


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/create_session", methods=["POST"])
def route_create_session():
    """
    Creates a new chat session. one topic is fixed
    """
    session_id = create_session(topic=FIXED_TOPIC)
    return jsonify({"session_id": session_id}), 201


@app.route("/chat", methods=["POST"])
def route_chat():
    """
    Handles chat interactions. 
    JSON body: {"session_id": <id or null>, "message": "text"}
    """
    body = request.get_json(force=True)
    session_id = body.get("session_id")
    user_message = body.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    # create a new session if not present
    if not session_id:
        session_id = create_session(topic=FIXED_TOPIC)

    # save the user message
    append_message(session_id, "user", user_message)

    # session retrieval and building message
    session_doc = get_session(session_id)
    messages = build_messages(session_doc)

    # generate assistant reply
    resp = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=messages,
        max_tokens=512,
        temperature=0.2,
        top_p=0.9
    )
    assistant_text = resp.choices[0].message.content

    # save it
    append_message(session_id, "assistant", assistant_text)

    return jsonify({"session_id": session_id, "reply": assistant_text})


@app.route("/history/<session_id>", methods=["GET"])
def route_history(session_id):
    """
    Returns the full chat history for a given session.
    """
    doc = get_session(session_id)
    if not doc:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(doc)


@app.route("/sessions", methods=["GET"])
def route_sessions():
    """
    Lists all chat sessions stored in Cosmos DB.
    """
    from cosmos_store import list_sessions
    sessions = list_sessions()
    return jsonify(sessions)


@app.route("/clear/<session_id>", methods=["POST"])
def route_clear(session_id):
    """
    Clears all messages in a session.
    """
    ok = clear_session(session_id)
    return jsonify({"cleared": ok})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
