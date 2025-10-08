## Overview
This document describes the initial architecture for the Azure AI Chatbot (Lab 1). The system provides a minimal conversational flow:
**User → Python Application → Azure OpenAI (gpt-4o) → Response → User**.

This is the foundational version: later labs will extend this design with persistence, RAG, semantic search, CI/CD, and more.

---

## Components
- **User**
  - Interaction surface: CLI or simple web UI.
- **Python Chatbot Application** (`chatbot.py`)
  - Responsibilities: input parsing, OpenAI client initialization, request/response handling, basic error handling, logging.
- **GitHub Repository** (`azure-ai-chatbot`)
  - Source control and documentation.
- **Azure Resource Group** (`rg-ai-chatbot`)
  - Logical container for cloud resources.
- **Azure OpenAI Service** (`openai-chatbot-service`)
  - Model deployment: **gpt-4o**. Endpoint: `https://openai-chatbot-service.openai.azure.com/`
- **Azure Key Vault**
  - Store API keys and secrets.
- **Application Insights (Optional)**
  - Telemetry and logging.

---

## Data Flow
1. User enters a message and submits it.
2. Python app constructs the request payload.
3. App retrieves the OpenAI API key from Key Vault (recommended) or environment variable.
4. App sends `POST` to Azure OpenAI endpoint: `/chat/completions` (API version `2024-05-01-preview`).
5. Azure OpenAI (gpt-4o) returns a JSON response.
6. App parses the response and returns the message to the user.

---

## Sequence (pseudo)

User -> App: "Hello"
App -> KeyVault: GET OPENAI_KEY
App -> AzureOpenAI: POST {model:gpt-4o, messages:[...]}
AzureOpenAI -> App: {choices:[{message:{content:"Hi, how can I help?"}}]}
App -> User: "Hi, how can I help?"


---

## Design Decisions
- **Python chosen** for SDK simplicity.
- **Secrets** handled through Key Vault.
- **GPT-4o** used for high-quality conversation.
- **MVP scope:** basic chatbot logic only.

---

## Future Roadmap
- Add conversation memory
- Add RAG and embeddings
- Containerize app
- Implement CI/CD via GitHub Actions

---

## Files Included
- `ai-architecture-model.drawio.png`
- `architecture.md`

---

## Change Log
| Version | Date | Change |
|----------|------|--------|
| 1.0 | 2025-10-08 | Initial architecture draft |
