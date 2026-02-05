import sqlite3
import chromadb
from datetime import datetime
import uuid

# -------------------------
# SQLite (Authoritative Memory)
# -------------------------
SQLITE_DB = "memory.db"

def get_sqlite_conn():
    return sqlite3.connect(SQLITE_DB)

def init_sqlite():
    conn = get_sqlite_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# -------------------------
# ChromaDB (Semantic Memory)
# -------------------------
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="task_memory")

# -------------------------
# PUBLIC FUNCTIONS
# -------------------------

def store_note(text: str):
    """
    Stores raw text in SQLite and embedding in ChromaDB
    """
    note_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1️⃣ Store raw text
    conn = get_sqlite_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO notes (id, content, timestamp) VALUES (?, ?, ?)",
        (note_id, text, timestamp)
    )
    conn.commit()
    conn.close()

    # 2️⃣ Generate embedding (YOUR FUNCTION)
    embedding = ConnectEmbed(text)

    # 3️⃣ Store vector
    collection.add(
        ids=[note_id],
        embeddings=[embedding],
        metadatas=[{"timestamp": timestamp}]
    )

    return note_id


def query_notes(user_query: str, top_k: int = 5):
    """
    Semantic search + grounded retrieval + LLM summarization
    """

    # 1️⃣ Embed query
    query_embedding = ConnectEmbed(user_query)

    # 2️⃣ Semantic search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    note_ids = results.get("ids", [[]])[0]
    if not note_ids:
        return "I couldn't find anything relevant."

    # 3️⃣ Fetch raw notes from SQLite
    conn = get_sqlite_conn()
    cur = conn.cursor()

    placeholders = ",".join("?" for _ in note_ids)
    cur.execute(
        f"SELECT content, timestamp FROM notes WHERE id IN ({placeholders})",
        note_ids
    )

    rows = cur.fetchall()
    conn.close()

    # 4️⃣ Build context
    context = ""
    for content, timestamp in rows:
        context += f"[{timestamp}]\n{content}\n\n"

    # 5️⃣ LLM summarization (YOUR FUNCTION)
    prompt = f"""
You are my personal work memory assistant.

Based on the following past notes, answer the user query clearly and concisely.

PAST NOTES:
{context}

USER QUERY:
{user_query}
"""

    return ConnectLLM(prompt)
