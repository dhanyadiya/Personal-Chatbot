import os
import sqlite3
from datetime import datetime
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "diya_memory.db"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB request limit


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            )
        """)


def now_text():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def save_message(role, content):
    with get_db() as db:
        db.execute(
            "INSERT INTO messages (role, content, created_at) VALUES (?, ?, ?)",
            (role, content, now_text())
        )


def get_recent_messages(limit=16):
    with get_db() as db:
        rows = db.execute(
            "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return list(reversed(rows))


def get_memories():
    with get_db() as db:
        return db.execute(
            "SELECT id, content, created_at FROM memories ORDER BY id DESC"
        ).fetchall()


def build_system_prompt():
    memories = get_memories()
    memory_text = "\n".join(f"- {item['content']}" for item in memories)
    if not memory_text:
        memory_text = "- No saved memories yet."
    return f"""You are Diya, a friendly, supportive personal AI companion.
Speak in clear, natural English. Be warm, respectful, encouraging, and honest.
Give practical answers and explain technical topics step by step when asked.
Do not claim to be human or claim to remember things that are not in the saved memories or conversation.
Use these user-approved saved memories only when relevant:
{memory_text}
"""


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/history")
def history():
    with get_db() as db:
        rows = db.execute(
            "SELECT id, role, content, created_at FROM messages ORDER BY id ASC"
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    if not message:
        return jsonify({"error": "Please type a message first."}), 400
    if len(message) > 4000:
        return jsonify({"error": "Please keep each message under 4,000 characters."}), 400

    # A simple, explicit memory command: "remember: I prefer short explanations"
    lowered = message.lower()
    if lowered.startswith("remember:"):
        memory = message[len("remember:"):].strip()
        if not memory:
            return jsonify({"error": "After 'remember:', write what you'd like Diya to remember."}), 400
        if len(memory) > 500:
            return jsonify({"error": "Please keep a saved memory under 500 characters."}), 400
        try:
            with get_db() as db:
                db.execute(
                    "INSERT INTO memories (content, created_at) VALUES (?, ?)",
                    (memory, now_text())
                )
            reply = f"I've saved that to my local memory: “{memory}” 💚"
        except sqlite3.IntegrityError:
            reply = "I already have that saved in my local memory. 💚"
        save_message("user", message)
        save_message("assistant", reply)
        return jsonify({"reply": reply})

    save_message("user", message)

    conversation = get_recent_messages(limit=16)
    ollama_messages = [{"role": "system", "content": build_system_prompt()}]
    ollama_messages.extend(
        {"role": row["role"], "content": row["content"]} for row in conversation
    )

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": ollama_messages,
                "stream": False,
                "options": {"temperature": 0.7}
            },
            timeout=(5, 180)
        )
        response.raise_for_status()
        reply = response.json().get("message", {}).get("content", "").strip()
        if not reply:
            raise RuntimeError("Ollama returned an empty reply.")
    except requests.exceptions.ConnectionError:
        reply = (
            "I can't reach Ollama yet. Please make sure Ollama is installed and running, "
            f"then download the model with `ollama pull {OLLAMA_MODEL}`. 💚"
        )
    except requests.exceptions.Timeout:
        reply = "That took too long for the local model. Please try again, or use a smaller model. 💚"
    except (requests.RequestException, ValueError, RuntimeError) as exc:
        app.logger.warning("Local model request failed: %s", exc)
        reply = (
            "I couldn't get a response from the local model. Check that Ollama is running "
            f"and that the model `{OLLAMA_MODEL}` is installed. 💚"
        )

    save_message("assistant", reply)
    return jsonify({"reply": reply})


@app.get("/api/memories")
def memories():
    return jsonify([dict(row) for row in get_memories()])


@app.delete("/api/memories/<int:memory_id>")
def delete_memory(memory_id):
    with get_db() as db:
        cursor = db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    if cursor.rowcount == 0:
        return jsonify({"error": "Memory not found."}), 404
    return jsonify({"ok": True})


@app.delete("/api/history")
def clear_history():
    with get_db() as db:
        db.execute("DELETE FROM messages")
    return jsonify({"ok": True})


init_db()

if __name__ == "__main__":
    # Local-only development server. Do not expose this debug server to the internet.
    app.run(host="127.0.0.1", port=5000, debug=False)
