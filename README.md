🧠 Azure RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot built with Flask, Azure OpenAI, Azure Cognitive Search, and Cosmos DB.
It retrieves relevant information from documents, maintains conversation memory, and responds in a clear, structured way.

📂 Repository Structure
File	Description
app.py	Main Flask application (entry point). Handles routes, chat logic, and session flow.
search_utils.py	Connects to Azure Cognitive Search and retrieves context for RAG responses.
cosmos_store.py	Manages chat sessions and message history using Cosmos DB.
templates/index.html	Frontend for user interaction with the chatbot.
.env	Environment variables (API keys, endpoints, configuration).
architecture.md	Detailed explanation of system design and data flow.
ai-architecture-model.drawio.png	Visual architecture diagram.
⚙️ Prerequisites

Make sure you have:

Python 3.10+

An Azure subscription with:

Azure OpenAI resource

Azure Cognitive Search resource

Azure Cosmos DB (Mongo or SQL API) resource

.env file created from .env.sample

🚀 Run Locally
1. Clone and set up the project
git clone https://github.com/<your-username>/azure-ai-chatbot.git
cd azure-ai-chatbot

2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # macOS/Linux

3. Install dependencies
pip install -r requirements.txt

4. Create a .env file

Use .env.sample as a guide and fill in your credentials:

AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview

AZURE_SEARCH_ENDPOINT=https://<your-search>.search.windows.net
AZURE_SEARCH_KEY=<your-key>
AZURE_SEARCH_INDEX=kb-index

COSMOS_CONNECTION_STRING=<your-cosmos-connection-string>
COSMOS_DB_NAME=chatbot-db
COSMOS_CONTAINER=sessions

5. Start the chatbot
python app.py


or, for production-style serving:

waitress-serve --listen=0.0.0.0:8000 app:app


Then open your browser to:
👉 http://localhost:8000

🧩 System Overview

Data Flow:

User sends a message from the frontend.

Flask app receives it and stores it in Cosmos DB.

The app queries Azure Cognitive Search for relevant context.

Both user history and context are sent to Azure OpenAI.

Azure OpenAI returns a structured response.

The chatbot displays the formatted reply to the user.

🧱 Architecture Diagram

See:

ai-architecture-model.drawio.png

architecture.md

These show the data flow and system components:

User → Flask App → Azure Cognitive Search → Azure OpenAI → Response → User
             ↳ Cosmos DB (for chat history)

🧭 Design Notes

Framework: Flask for simplicity and flexibility.

LLM: Azure OpenAI GPT-4o for high-quality responses.

Search: Azure Cognitive Search for document grounding (RAG).

Storage: Cosmos DB for persistent conversation memory.

Serving: Waitress for lightweight production hosting.

🔮 Future Enhancements

Add Azure Key Vault for secret storage

Implement embedding generation pipeline

Add monitoring and insights via Azure Monitor

Add containerization (Docker + Azure Container Apps)

Set up CI/CD with GitHub Actions