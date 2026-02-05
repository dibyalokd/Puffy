from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/record", methods=["GET", "POST"])
def record_task():
    if request.method == "POST":
        task_text = request.form.get("task")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 🚧 PHASE-2 WILL GO HERE
        # store(task_text, timestamp)

        print(f"[RECORDED @ {timestamp}] {task_text}")

        return redirect(url_for("record_task"))

    return render_template("recorder.html")

@app.route("/query")
def query_task():
    return render_template("query.html")

if __name__ == "__main__":
    app.run(debug=True)
