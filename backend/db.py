import sqlite3
import os

# Resolves to backend/spudnik.db, same directory-independent pattern
# persona_loader.py uses for the persona folder.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spudnik.db")

def get_connection():
    # Each call gets its own connection -- simplest safe pattern for a
    # small Flask app, avoids sharing one connection across requests.
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name, not just index
    return conn

def init_db():
    # IF NOT EXISTS makes this safe to call every time the app starts --
    # won't error out or wipe data if the tables already exist.
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            summary TEXT NOT NULL,
            related_project TEXT,
            date TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            status TEXT,
            current_phase TEXT,
            current_focus TEXT,
            last_updated TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            issue TEXT NOT NULL,
            resolved INTEGER DEFAULT 0,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS advice_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            decision TEXT NOT NULL,
            taters_stance TEXT NOT NULL,
            outcome TEXT,
            date TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """)

    conn.commit()
    conn.close()
    
def get_recent_messages(session_id, limit=10):
    # PULL the most recent messages for this session, oldest-first once
    # returned, so they read in chronological order when handed to Claude.
    # ORDER BY id DESC + LIMIT grabs the newest rows first, then we
    # reverse them in Python so the final list is chronological.
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT role, content
        FROM messages
        WHERE session_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (session_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()

    # rows come back newest-first -- reverse so oldest is first,
    # matching the order a real conversation actually happened in
    rows.reverse()

    # convert sqlite3.Row objects into plain dicts shaped like what
    # the Anthropic API expects: {"role": ..., "content": ...}
    return [{"role": row["role"], "content": row["content"]} for row in rows]