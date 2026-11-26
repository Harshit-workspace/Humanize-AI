import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).with_name("humantext.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_text TEXT NOT NULL,
                ai_probability REAL NOT NULL,
                prediction TEXT NOT NULL,
                rewritten_text TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


def save_analysis(original_text, ai_probability, prediction,
                  rewritten_text=""):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO analyses
            (original_text, ai_probability, prediction,
             rewritten_text, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            original_text,
            float(ai_probability),
            prediction,
            rewritten_text,
            datetime.now().isoformat(timespec="seconds")
        ))
        conn.commit()


def get_history(limit=100):
    with get_connection() as conn:
        return conn.execute("""
            SELECT id, created_at, prediction, ai_probability,
                   substr(original_text, 1, 100)
            FROM analyses
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()


def delete_history_item(record_id):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM analyses WHERE id = ?",
            (record_id,)
        )
        conn.commit()
