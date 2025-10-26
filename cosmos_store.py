import os
from datetime import datetime
from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv

load_dotenv()

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DB = os.getenv("COSMOS_DB", "chatbot-db")
COSMOS_CONTAINER = os.getenv("COSMOS_CONTAINER", "sessions")

if not (COSMOS_ENDPOINT and COSMOS_KEY):
    raise SystemExit("Missing COSMOS_ENDPOINT or COSMOS_KEY in environment.")

client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
db = client.create_database_if_not_exists(id=COSMOS_DB)
container = db.create_container_if_not_exists(
    id=COSMOS_CONTAINER,
    partition_key=PartitionKey(path="/id"),
    offer_throughput=400
)


#new chat session is created 
# new chat session is created 
def create_session(session_id=None, topic="general"): 
    import uuid
    if not session_id:
        session_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    doc = {
        "id": session_id,
        "createdAt": now,
        "lastUpdated": now,
        "messages": [],
        "summary": "",
        "topic": topic  
    }
    container.create_item(body=doc)
    return session_id

def list_sessions():
    query = "SELECT c.id, c.createdAt, c.lastUpdated, c.topic FROM c ORDER BY c.lastUpdated DESC"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    return items

#get the specific document for the session from the database
def get_session(session_id):
    try:
        doc = container.read_item(item=session_id, partition_key=session_id)
        return doc
    except Exception:
        return None

#add new content to the document sessino
def append_message(session_id, role, content):
    doc = get_session(session_id)
    if not doc:
        create_session(session_id)
        doc = get_session(session_id)
    messages = doc.get("messages", [])
    messages.append({"role": role, "content": content, "ts": datetime.utcnow().isoformat() + "Z"})
    doc["messages"] = messages
    doc["lastUpdated"] = datetime.utcnow().isoformat() + "Z"
    container.replace_item(item=session_id, body=doc)
    return doc

def clear_session(session_id):
    doc = get_session(session_id)
    if not doc:
        return False
    doc["messages"] = []
    doc["summary"] = ""
    doc["lastUpdated"] = datetime.utcnow().isoformat() + "Z"
    container.replace_item(item=session_id, body=doc)
    return True

def list_sessions():
    query = "SELECT c.id, c.createdAt, c.lastUpdated FROM c ORDER BY c.lastUpdated DESC"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    return items
