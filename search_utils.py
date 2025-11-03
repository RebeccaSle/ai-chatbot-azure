"""
search_utils.py
----------------
This module connects to **Azure Cognitive Search** and retrieves relevant text
chunks (context) based on a user query. It is used in the chatbot to provide
document-based grounding for responses (RAG — Retrieval-Augmented Generation).

Main Function:
    get_relevant_context(query, top_k=3)
        → Runs a semantic search and returns the top matching text chunks combined
          into a single string for use in the AI system prompt.

Environment Variables (loaded from .env):
    - AZURE_SEARCH_ENDPOINT : Endpoint URL of your Azure Search service
    - AZURE_SEARCH_KEY      : Admin or query key for authentication
    - AZURE_SEARCH_INDEX    : Target index name (default: 'kb-index')
"""

import os
import json
import logging
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential


load_dotenv()

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "kb-index")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Azure Cognitive Search client
search_client = None
try:
    if AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_KEY:
        search_client = SearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            index_name=AZURE_SEARCH_INDEX,
            credential=AzureKeyCredential(AZURE_SEARCH_KEY)
        )
        logger.info("✅ Azure Cognitive Search client initialized successfully.")
    else:
        logger.warning("⚠️ Missing Azure Search credentials in .env.")
except Exception as e:
    logger.error(f"[Init ERROR] Failed to initialize SearchClient: {e}")

# Function: get_relevant_context
def get_relevant_context(query: str, top_k: int = 3) -> str:
    """
    Perform a **semantic search** using Azure Cognitive Search.

    Args:
        query (str): The user's message or search term.
        top_k (int, optional): Number of top results to retrieve. Default is 3.

    Returns:
        str: A combined string of the most relevant text chunks found.
             Returns an empty string if the search fails or no client is initialized.

    Notes:
        - The function uses the 'semantic' query type.
        - Each result includes its relevance score for transparency.
    """
    if not search_client:
        logger.warning("Search client not initialized — returning empty context.")
        return ""

    try:
        # Perform semantic search
        results = search_client.search(
            search_text=query,
            query_type="semantic",
            semantic_configuration_name="default",
            top=top_k
        )

        # Collect relevant chunks
        retrieved_chunks = []
        for result in results:
            content = result.get("content") or result.get("text") or json.dumps(result)
            score = result.get("@search.score", 0)
            retrieved_chunks.append(f"(score={score:.2f}) {content}")

        # Combine chunks into one string
        combined_context = "\n\n".join(retrieved_chunks)
        logger.info(f"Retrieved {len(retrieved_chunks)} relevant chunks.")
        return combined_context

    except Exception as e:
        logger.warning(f"[Semantic Search ERROR]: {e}")
        return ""
