import sqlite3
import logging
from contextlib import contextmanager

DB_PATH = "truck_forwarder.db"
logger = logging.getLogger(__name__)


def init_db():
    """Create tables if they don't exist."""
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS processed_groups (
                media_group_id  TEXT PRIMARY KEY,
                processed_at    DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS processed_messages (
                message_id      INTEGER PRIMARY KEY,
                processed_at    DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    logger.info("Database initialised.")


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def is_group_processed(media_group_id: str) -> bool:
    with _conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM processed_groups WHERE media_group_id = ?",
            (media_group_id,)
        ).fetchone()
    return row is not None


def mark_group_processed(media_group_id: str):
    with _conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO processed_groups (media_group_id) VALUES (?)",
            (media_group_id,)
        )
        conn.commit()


def is_message_processed(message_id: int) -> bool:
    with _conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM processed_messages WHERE message_id = ?",
            (message_id,)
        ).fetchone()
    return row is not None


def mark_message_processed(message_id: int):
    with _conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO processed_messages (message_id) VALUES (?)",
            (message_id,)
        )
        conn.commit()
