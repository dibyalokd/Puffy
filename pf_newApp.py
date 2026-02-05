from flask import Flask, render_template, request, redirect, url_for
from memory_store import store_note, query_notes, init_sqlite

app = Flask(__name__)

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
    response = None
    if request.method == "POST":
        user_query = request.form.get("query")
        response = query_notes(user_query)
    return render_template("query.html", response=response)

if __name__ == "__main__":
    app.run(debug=True)
