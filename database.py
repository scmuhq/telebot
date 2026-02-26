import sqlite3
from config import DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create all required tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Users who started the bot (for announcements)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_users (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT,
            first_name  TEXT,
            joined_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Certified members list
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS certified_members (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT,
            first_name  TEXT,
            role        TEXT DEFAULT 'Membre certifié',
            added_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Warnings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warnings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            warned_by   INTEGER NOT NULL,
            reason      TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Pending CAPTCHA
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_captcha (
            user_id     INTEGER PRIMARY KEY,
            answer      INTEGER NOT NULL,
            message_id  INTEGER,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ─── Bot Users (for announcements) ───────────────────────────────────────────

def add_bot_user(user_id: int, username: str | None, first_name: str | None) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO bot_users (user_id, username, first_name) VALUES (?, ?, ?)",
        (user_id, username, first_name),
    )
    conn.commit()
    conn.close()


def get_all_bot_users() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT user_id, username, first_name FROM bot_users").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Certified Members ───────────────────────────────────────────────────────

def add_certified_member(user_id: int, username: str | None, first_name: str | None, role: str = "Membre certifié") -> None:
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO certified_members (user_id, username, first_name, role) VALUES (?, ?, ?, ?)",
        (user_id, username, first_name, role),
    )
    conn.commit()
    conn.close()


def remove_certified_member(user_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM certified_members WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_certified_members() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT user_id, username, first_name, role FROM certified_members").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Warnings ────────────────────────────────────────────────────────────────

def add_warning(user_id: int, warned_by: int, reason: str | None = None) -> int:
    conn = get_connection()
    conn.execute(
        "INSERT INTO warnings (user_id, warned_by, reason) VALUES (?, ?, ?)",
        (user_id, warned_by, reason),
    )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM warnings WHERE user_id = ?", (user_id,)).fetchone()[0]
    conn.close()
    return count


def get_warning_count(user_id: int) -> int:
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM warnings WHERE user_id = ?", (user_id,)).fetchone()[0]
    conn.close()
    return count


# ─── Pending CAPTCHA ─────────────────────────────────────────────────────────

def add_pending_captcha(user_id: int, answer: int, message_id: int | None = None) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO pending_captcha (user_id, answer, message_id) VALUES (?, ?, ?)",
        (user_id, answer, message_id),
    )
    conn.commit()
    conn.close()


def get_pending_captcha(user_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT user_id, answer, message_id FROM pending_captcha WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def remove_pending_captcha(user_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM pending_captcha WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
