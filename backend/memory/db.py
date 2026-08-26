import sqlite3
import uuid
from datetime import datetime
from loguru import logger
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "jarvis_memory.db")

def init_db():
    """Initializes the database and creates the memories table if it doesn't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                label TEXT NOT NULL,
                value TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                UNIQUE(category, label)
            )
        ''')
    logger.info(f"💾 Memory database initialized at {DB_PATH}")

def add_memory(category: str, label: str, value: str) -> dict:
    """
    Inserts a new memory or updates an existing one if (category, label) matches.
    Returns the inserted/updated entry.
    """
    entry = {
        "id": str(uuid.uuid4()),
        "category": category.lower(),
        "label": label.lower(),
        "value": value,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            INSERT INTO memories (id, category, label, value, timestamp)
            VALUES (:id, :category, :label, :value, :timestamp)
            ON CONFLICT(category, label) DO UPDATE SET
                value=excluded.value,
                timestamp=excluded.timestamp
        ''', entry)
    
    logger.success(f"💾 Saved memory [{category}] {label}: {value}")
    return entry

def remove_memory(label: str) -> bool:
    """Removes a memory by label. Returns True if deleted, False otherwise."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute('DELETE FROM memories WHERE label = ?', (label.lower(),))
        deleted = cursor.rowcount > 0
    if deleted:
        logger.success(f"💾 Forgot memory with label: {label}")
    else:
        logger.warning(f"⚠️ Could not find memory to forget with label: {label}")
    return deleted

def get_all_memories() -> list[dict]:
    """Returns all memories ordered by timestamp (newest first)."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute('SELECT * FROM memories ORDER BY timestamp DESC').fetchall()
        return [dict(r) for r in rows]
