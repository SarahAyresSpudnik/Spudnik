import sqlite3
import os
from datetime import datetime, timezone

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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            detail TEXT,
            timestamp TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            pinned INTEGER NOT NULL DEFAULT 0,
            hidden INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Migration for DBs created before pinned/hidden existed -- CREATE TABLE
    # IF NOT EXISTS above is a no-op on an already-existing table, so the
    # new columns need adding by hand for anyone upgrading in place.
    cursor.execute("PRAGMA table_info(sessions)")
    existing_columns = {row["name"] for row in cursor.fetchall()}
    if "pinned" not in existing_columns:
        cursor.execute("ALTER TABLE sessions ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0")
    if "hidden" not in existing_columns:
        cursor.execute("ALTER TABLE sessions ADD COLUMN hidden INTEGER NOT NULL DEFAULT 0")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS protocols (
            filename TEXT PRIMARY KEY,
            enabled INTEGER NOT NULL DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            spec TEXT,
            role TEXT,
            aside TEXT,
            status TEXT NOT NULL DEFAULT 'standby',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_cache (
            source TEXT PRIMARY KEY,
            fetched_at TEXT NOT NULL,
            items_json TEXT NOT NULL
        )
    """)

    conn.commit()

    # Seed the three known machines the first time the devices table is
    # ever empty -- same insert path Add Device uses, not special-cased
    # in the frontend. Only fires once; deleting them afterward is final.
    cursor.execute("SELECT COUNT(*) AS c FROM devices")
    if cursor.fetchone()["c"] == 0:
        seed_now = datetime.now(timezone.utc).isoformat()
        seed_devices = [
            ("Lazarus", "DESKTOP", "i9-12900KF · RTX 3090", "Primary dev / Ollama machine · Claude Code installed", "where the thinking actually happens", "link_active"),
            ("OmniBook X Flip 16", "LAPTOP", "Intel Core Ultra · CPU-only", "Demo / presentation device", "", "standby"),
            ("The Brick", "HANDHELD", "Ayn Thor Pro", "Handheld", "", "standby"),
        ]
        for name, category, spec, role, aside, status in seed_devices:
            cursor.execute(
                "INSERT INTO devices (name, category, spec, role, aside, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (name, category, spec, role, aside, status, seed_now, seed_now)
            )
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

def write_memory_entry(category, summary, related_project=None):
    # Inserts a single memory_entries row. related_project stays
    # NULL unless explicitly passed in -- no auto-parsing of project
    # names for now, keeps this deterministic.
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    cursor.execute(
        "INSERT INTO memory_entries (category, summary, related_project, date) VALUES (?, ?, ?, ?)",
        (category, summary, related_project, now)
    )
    conn.commit()
    conn.close()


def find_memory_entry(keyword):
    # Simple LIKE match against summary -- case-insensitive since
    # SQLite's LIKE is case-insensitive by default for ASCII text.
    # Returns the single most recent match, or None if nothing hits.
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT summary FROM memory_entries
        WHERE summary LIKE ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (f"%{keyword}%",)
    )
    row = cursor.fetchone()
    conn.close()

    return row["summary"] if row else None


def write_activity(event_type, detail=None):
    # Logs one meaningful sidebar-visible event -- provider switches, key
    # changes, reboots, messages sent. Kept separate from advice_log, which
    # tracks project decisions, not runtime events.
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    cursor.execute(
        "INSERT INTO activity_log (event_type, detail, timestamp) VALUES (?, ?, ?)",
        (event_type, detail, now)
    )
    conn.commit()
    conn.close()


def get_recent_activity(limit=10):
    # Most recent activity first, for the Recent Activity sidebar card.
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT event_type, detail, timestamp
        FROM activity_log
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {"event_type": row["event_type"], "detail": row["detail"], "timestamp": row["timestamp"]}
        for row in rows
    ]


def get_sessions():
    # One row per session_id, pinned sessions first, then most-recent-first
    # within each group. "Most recent" is judged by the highest message id
    # in that session, not by timestamp -- paired user/assistant rows share
    # identical timestamps by design, so id is the only reliable ordering
    # signal. Hidden (soft-deleted) sessions are excluded entirely.
    # LEFT JOIN sessions for the real name -- falls back to a short label
    # built from the session_id for any legacy session that predates the
    # sessions table (shouldn't happen going forward, since ensure_session
    # is called on every first message of a session).
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT m.session_id AS session_id,
               MAX(m.id) AS last_id,
               COUNT(*) AS message_count,
               MIN(m.timestamp) AS started_at,
               s.name AS name,
               COALESCE(s.pinned, 0) AS pinned
        FROM messages m
        LEFT JOIN sessions s ON s.session_id = m.session_id
        WHERE COALESCE(s.hidden, 0) = 0
        GROUP BY m.session_id
        ORDER BY pinned DESC, last_id DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "session_id": row["session_id"],
            "name": row["name"] or f"Session {row['session_id'][:8]}",
            "message_count": row["message_count"],
            "started_at": row["started_at"],
            "pinned": bool(row["pinned"]),
        }
        for row in rows
    ]


def ensure_session(session_id, first_message=None):
    # Called once per session, right before its first exchange gets logged.
    # INSERT OR IGNORE -- a session that already has a row (renamed or not)
    # is left completely alone.
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM sessions WHERE session_id = ?", (session_id,))
    if cursor.fetchone():
        conn.close()
        return

    now = datetime.now(timezone.utc).isoformat()
    if first_message:
        name = first_message.strip().replace("\n", " ")[:48]
        if len(first_message.strip()) > 48:
            name += "…"
    else:
        name = f"Session {now[:16].replace('T', ' ')}"

    cursor.execute(
        "INSERT INTO sessions (session_id, name, created_at) VALUES (?, ?, ?)",
        (session_id, name, now)
    )
    conn.commit()
    conn.close()


def rename_session(session_id, name):
    # UPSERT, not a plain UPDATE -- a session that has messages but predates
    # the sessions table (or somehow never got an ensure_session call) still
    # needs to be renameable, not silently rejected because no row exists yet.
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        """
        INSERT INTO sessions (session_id, name, created_at) VALUES (?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET name = excluded.name
        """,
        (session_id, name, now)
    )
    conn.commit()
    conn.close()
    return True


def set_session_pinned(session_id, pinned, default_name=None):
    # Same upsert pattern as rename_session -- pinning a legacy session
    # (no sessions row yet) shouldn't silently fail either. Falls back to
    # the exact same short-id label get_sessions() would already be
    # displaying, so pinning never causes a surprise rename.
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    name = default_name or f"Session {session_id[:8]}"
    cursor.execute(
        """
        INSERT INTO sessions (session_id, name, created_at, pinned) VALUES (?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET pinned = excluded.pinned
        """,
        (session_id, name, now, 1 if pinned else 0)
    )
    conn.commit()
    conn.close()
    return True


def hide_session(session_id):
    # Soft delete -- marks the session hidden so it drops out of
    # get_sessions() (and therefore Logs/Recent Activity/Continue)
    # entirely, without touching the underlying messages rows.
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        """
        INSERT INTO sessions (session_id, name, created_at, hidden) VALUES (?, ?, ?, 1)
        ON CONFLICT(session_id) DO UPDATE SET hidden = 1
        """,
        (session_id, f"Session {session_id[:8]}", now)
    )
    conn.commit()
    conn.close()
    return True


def get_session_meta(session_id):
    # name + pinned for a single session, used by /api/session/current.
    # Falls back to a short label when no sessions row exists yet (a
    # session with zero messages so far, or a legacy one).
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, pinned FROM sessions WHERE session_id = ?",
        (session_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"name": row["name"], "pinned": bool(row["pinned"])}
    return {"name": f"Session {session_id[:8]}", "pinned": False}


def get_messages_by_session(session_id):
    # ORDER BY id, not timestamp -- paired user/assistant messages share
    # identical timestamps by design, so id is the only stable chronological key.
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT role, content, timestamp
        FROM messages
        WHERE session_id = ?
        ORDER BY id
        """,
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {"role": row["role"], "content": row["content"], "timestamp": row["timestamp"]}
        for row in rows
    ]


def get_memory_entries(limit=50):
    # Most recent first, for the Memory tab's log/list view.
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT summary, date FROM memory_entries
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()

    # Mapped to content/timestamp -- the shape the Memory tab already
    # expects (matches the Claude Design export's mock entry shape).
    return [{"content": row["summary"], "timestamp": row["date"]} for row in rows]


def get_memory_stats():
    # Live count + most recent write time for the Memory Stats sidebar card.
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS c FROM memory_entries")
    total = cursor.fetchone()["c"]

    cursor.execute("SELECT date FROM memory_entries ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    return {"total_entries": total, "last_write": row["date"] if row else None}


def get_protocols_enabled_map():
    # filename -> enabled(bool), for whatever protocols already have a
    # stored toggle state. A protocol found on disk but missing here
    # defaults to enabled -- see app.py's list-building logic.
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT filename, enabled FROM protocols")
    rows = cursor.fetchall()
    conn.close()
    return {row["filename"]: bool(row["enabled"]) for row in rows}


def set_protocol_enabled(filename, enabled):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO protocols (filename, enabled) VALUES (?, ?)
        ON CONFLICT(filename) DO UPDATE SET enabled = excluded.enabled
        """,
        (filename, 1 if enabled else 0)
    )
    conn.commit()
    conn.close()


def set_all_protocols_enabled(filenames, enabled):
    # Master slider on the Settings page -- bulk-sets every known protocol
    # (by filename, as currently found on disk) to the same on/off state.
    conn = get_connection()
    cursor = conn.cursor()
    value = 1 if enabled else 0
    for filename in filenames:
        cursor.execute(
            """
            INSERT INTO protocols (filename, enabled) VALUES (?, ?)
            ON CONFLICT(filename) DO UPDATE SET enabled = excluded.enabled
            """,
            (filename, value)
        )
    conn.commit()
    conn.close()


def get_devices():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM devices ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_device(name, category, spec, role, aside, status):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO devices (name, category, spec, role, aside, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (name, category, spec, role, aside, status, now, now)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def update_device(device_id, fields):
    # fields is a dict of column -> new value, already limited to the
    # editable columns by the caller (app.py) -- keeps this a thin update,
    # not a place that needs to know about the HTTP layer.
    if not fields:
        return False
    conn = get_connection()
    cursor = conn.cursor()
    columns = list(fields.keys())
    set_clause = ", ".join(f"{col} = ?" for col in columns)
    values = [fields[col] for col in columns]
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        f"UPDATE devices SET {set_clause}, updated_at = ? WHERE id = ?",
        (*values, now, device_id)
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


def delete_device(device_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def get_news_cache(source):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT fetched_at, items_json FROM news_cache WHERE source = ?",
        (source,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {"fetched_at": row["fetched_at"], "items_json": row["items_json"]}


def set_news_cache(source, items_json):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        """
        INSERT INTO news_cache (source, fetched_at, items_json) VALUES (?, ?, ?)
        ON CONFLICT(source) DO UPDATE SET fetched_at = excluded.fetched_at, items_json = excluded.items_json
        """,
        (source, now, items_json)
    )
    conn.commit()
    conn.close()