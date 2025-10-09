## Overview
This document describes the initial architecture for the Azure AI Chatbot (Lab 1). The system provides a minimal conversational flow:
**User → Python Application → Azure OpenAI (gpt-4o) → Response → User**.

To include later on RAG, semantic search, CI/CD, insights ....

- **User**
  - Interaction: CLI 
- **Python Chatbot Application** (`chatbot.py`)
  - input parsing, OpenAI client initialization, request/response handling, basic error handling, logging.
- **GitHub Repository** (`azure-ai-chatbot`)
  - Source control and documentation.
- **Azure Resource Group** (`rg-ai-chatbot`)
  - Logical container for cloud resources.
- **Azure OpenAI Service** (`openai-chatbot-service`)
  - Model deployment: **gpt-4o**. Endpoint: `https://openai-chatbot-service.openai.azure.com/`
- **Azure Key Vault**
  - Store API keys and secrets.

## Data Flow
1. User enters a message and submits it.
2. Python app constructs the request payload.
3. App retrieves the OpenAI API key from Key Vault (not implemented) or environment variable(implemented).
4. App sends `POST` to Azure OpenAI endpoint: `/chat/completions` (API version `2024-05-01-preview`).
5. Azure OpenAI returns a JSON response.
6. App parses the response and returns the message to the user.


## how it works (sequence)

User -> App: "Hello"
App -> KeyVault: GET OPENAI_KEY
App -> AzureOpenAI: POST {model:gpt-4o, messages:[...]}
AzureOpenAI -> App: {choices:[{message:{content:"Hi, how can I help?"}}]}
App -> User: "Hi, how can I help?"


## Decisions
- **Python chosen** for SDK simplicity.
- **Secrets** handled through Key Vault. (To be implemented)
- **GPT-4o** used for high-quality conversation.
- **MVP scope:** basic chatbot logic only.


## Future Work
- Add conversation memory
- Add RAG and embeddings
- Containerize app
- Implement CI/CD via GitHub Actions
- Implement insights on azure 


## Files Included
- `ai-architecture-model.drawio.png`
- `architecture.md`
