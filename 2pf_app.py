import sqlite3
import datetime
import requests
import chromadb
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION ---
LM_STUDIO_URL = "http://192.168.1.6:1234/v1"
CHROMA_PATH = "./chroma_db"

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(name="user_records")


# Initialize SQLite
def init_sqlite():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id TEXT PRIMARY KEY,
            content TEXT,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()


init_sqlite()


# --- HELPER FUNCTIONS ---
def get_embedding(text):
    response = requests.post(
        f"{LM_STUDIO_URL}/embeddings",
        json={"input": text, "model": "local-model"}  # Model name usually ignored by LM Studio
    )
    return response.json()['data'][0]['embedding']


# Updated function in app.py
# def get_llm_summary(query, results):
#     # 'results' now includes documents and metadatas from Chroma
#     context_entries = []
#     for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
#         context_entries.append(f"[{meta['timestamp']}] {doc}")
#
#     context_text = "\n".join(context_entries)
#     current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#
#     prompt = f"""
#     Current Date/Time: {current_time}
#
#     Below are the user's recorded tasks from their vault:
#     {context_text}
#
#     User Query: {query}
#
#     Instruction: Based on the timestamps and content provided, generate a summarized report.
#     If the user asks for 'today' or 'this week', prioritize the relevant timestamps.
#     """
#
#     response = requests.post(
#         f"{LM_STUDIO_URL}/chat/completions",
#         json={
#             "messages": [{"role": "user", "content": prompt}],
#             "temperature": 0.3  # Lower temperature for more factual reports
#         }
#     )
#     return response.json()['choices'][0]['message']['content']
def get_llm_summary(query, context_list):
    context_text = "\n".join(context_list)
    prompt = f"Based on these records:\n{context_text}\n\nUser Query: {query}\n\nSummarize the answer properly."

    response = requests.post(
        f"{LM_STUDIO_URL}/chat/completions",
        json={
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "model":"liquid/lfm2-1.2b"
        }
    )
    return response.json()['choices'][0]['message']['content']


# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/record', methods=['GET', 'POST'])
def record():
    if request.method == 'POST':
        content = request.form['content']
        record_id = str(datetime.datetime.now().timestamp())
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Store in SQLite
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO logs (id, content, timestamp) VALUES (?, ?, ?)", (record_id, content, timestamp))
        conn.commit()
        conn.close()

        # 2. Store in ChromaDB
        embedding = get_embedding(content)
        collection.add(
            ids=[record_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[{"timestamp": timestamp}]
        )
        return render_template('record.html', success=True)
    return render_template('record.html')


@app.route('/query', methods=['GET', 'POST'])
def query():
    summary = ""
    sources = []
    if request.method == 'POST':
        user_query = request.form['query']
        query_embedding = get_embedding(user_query)

        # Search ChromaDB
        results = collection.query(query_embeddings=[query_embedding], n_results=5)
        sources = results['documents'][0]

        # Get Summary from LM Studio
        summary = get_llm_summary(user_query, sources)

    return render_template('query.html', summary=summary, sources=sources)


if __name__ == '__main__':
    app.run(debug=True, port=5050)
