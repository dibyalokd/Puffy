from flask import Flask, render_template, request, redirect, url_for, session
from memory_store import store_note, query_notes, init_sqlite

app = Flask(__name__)
app.secret_key = "task-memory-secret"  # required for session

init_sqlite()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/record", methods=["GET", "POST"])
def record_task():
    if request.method == "POST":
        task_text = request.form.get("task")
        if task_text.strip():
            store_note(task_text)
        return redirect(url_for("record_task"))
    return render_template("recorder.html")

@app.route("/query", methods=["GET", "POST"])
def query_task():

    # Initialize chat history once
    if "chat_history" not in session:
        session["chat_history"] = []

    if request.method == "POST":
        user_query = request.form.get("query")

        # 1️⃣ Add user message
        session["chat_history"].append({
            "role": "user",
            "content": user_query
        })

        # 2️⃣ Get AI response (semantic + memory)
        ai_response = query_notes(user_query)

        # 3️⃣ Add AI response
        session["chat_history"].append({
            "role": "ai",
            "content": ai_response
        })

        session.modified = True

    return render_template(
        "query.html",
        chat_history=session["chat_history"]
    )

if __name__ == "__main__":
    app.run(debug=True)
