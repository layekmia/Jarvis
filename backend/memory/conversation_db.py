"""
Persistent Conversation History — Jarvis

Keeps a full raw transcript of every user/assistant exchange in
``jarvis_memory.db``.  Completely separate from the long-term
``memories`` table (remember/forget tools).

Usage by AIBrain
----------------
- On every turn  : append_turn(session_id, role, content)
- On every LLM call: get_window_messages(n=20)  →  last N turns as dicts
- Periodically   : compress_old_turns(threshold=30) compresses turns older
  than the sliding window into a 2-3 sentence summary and removes raw rows.
"""

import sqlite3
import uuid
from datetime import datetime
from typing import Optional
from loguru import logger

from backend.memory.db import DB_PATH   # reuse same jarvis_memory.db file


# ── Schema ────────────────────────────────────────────────────────────────────

_CREATE_CONVERSATIONS = """
CREATE TABLE IF NOT EXISTS conversations (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT    NOT NULL,
    role       TEXT    NOT NULL,   -- 'user' | 'assistant'
    content    TEXT    NOT NULL,
    timestamp  TEXT    NOT NULL
)
"""

_CREATE_SUMMARIES = """
CREATE TABLE IF NOT EXISTS conv_summaries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    summary         TEXT NOT NULL,
    covers_up_to_id INTEGER NOT NULL,   -- highest conversations.id included
    timestamp       TEXT    NOT NULL
)
"""

_CREATE_BROWSER_STATE = """
CREATE TABLE IF NOT EXISTS browser_state (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated TEXT NOT NULL
)
"""


def init_conversation_db() -> None:
    """Create conversation tables if they don't exist yet."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(_CREATE_CONVERSATIONS)
        conn.execute(_CREATE_SUMMARIES)
        conn.execute(_CREATE_BROWSER_STATE)
    logger.info("💬 Conversation DB tables initialised.")


# ── Write ─────────────────────────────────────────────────────────────────────

def append_turn(session_id: str, role: str, content: str) -> int:
    """Insert a single turn.  Returns the new row id."""
    ts = datetime.utcnow().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "INSERT INTO conversations (session_id, role, content, timestamp) "
            "VALUES (?, ?, ?, ?)",
            (session_id, role, content, ts),
        )
        return cur.lastrowid


# ── Read ──────────────────────────────────────────────────────────────────────

def get_recent_turns(n: int = 40) -> list[dict]:
    """Return the last *n* raw turns (oldest first) as list of dicts."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM conversations ORDER BY id DESC LIMIT ?", (n,)
        ).fetchall()
    # Reverse so oldest is first (correct chronological order for LLM)
    return [dict(r) for r in reversed(rows)]


def get_latest_summary() -> Optional[str]:
    """Return the most recent summary text, or None if none exists."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT summary FROM conv_summaries ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return row["summary"] if row else None


def get_turn_count() -> int:
    """Total number of raw turns stored (for deciding when to compress)."""
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()
    return row[0]


# ── Compression ───────────────────────────────────────────────────────────────

def save_summary(summary_text: str, covers_up_to_id: int) -> None:
    """Persist a newly created summary and delete the compressed raw rows."""
    ts = datetime.utcnow().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        # Save the summary
        conn.execute(
            "INSERT INTO conv_summaries (summary, covers_up_to_id, timestamp) "
            "VALUES (?, ?, ?)",
            (summary_text, covers_up_to_id, ts),
        )
        # Delete old rows that are now covered by the summary
        conn.execute(
            "DELETE FROM conversations WHERE id <= ?",
            (covers_up_to_id,),
        )
    logger.info(
        f"💬 Compressed conversation history up to turn id={covers_up_to_id}. "
        f"Summary saved ({len(summary_text)} chars)."
    )


# ── Browser State (lightweight KV store for browser context) ──────────────────

def set_browser_state(key: str, value: str) -> None:
    """Persist a browser-related state value (e.g. current_url, open_tabs)."""
    ts = datetime.utcnow().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO browser_state (key, value, updated) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated=excluded.updated",
            (key, value, ts),
        )


def get_browser_state(key: str) -> Optional[str]:
    """Read a browser state value, or None if not set."""
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT value FROM browser_state WHERE key = ?", (key,)
        ).fetchone()
    return row[0] if row else None
