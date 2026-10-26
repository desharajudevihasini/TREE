"""Simple, local demo-session persistence. No production authentication or PII protections."""
import json
import os
import sqlite3
from contextlib import contextmanager
from backend.schemas import Property
from backend.demo import get_demo

DB_FILE = os.getenv("GREENTWIN_DB", os.path.join(os.path.dirname(__file__), "..", "greentwin.sqlite"))


@contextmanager
def connect():
    db = sqlite3.connect(DB_FILE)
    db.row_factory = sqlite3.Row
    try:
        db.execute("CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, property_json TEXT NOT NULL, pending TEXT, asked_json TEXT NOT NULL, messages_json TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS customer_memory (id TEXT PRIMARY KEY, memory_json TEXT NOT NULL)")
        db.commit()
        yield db
        db.commit()
    finally:
        db.close()


def load_session(session_id: str, property_id: str):
    with connect() as db:
        row = db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    if row:
        return {"id": session_id, "property": Property.model_validate_json(row["property_json"]),
                "pending": row["pending"], "asked": json.loads(row["asked_json"]),
                "messages": json.loads(row["messages_json"])}
    return {"id": session_id, "property": get_demo(property_id), "pending": None, "asked": [], "messages": []}


def save_session(s):
    with connect() as db:
        db.execute("INSERT OR REPLACE INTO sessions VALUES (?, ?, ?, ?, ?)",
                   (s["id"], s["property"].model_dump_json(), s["pending"],
                    json.dumps(s["asked"]), json.dumps(s["messages"][-30:])))
