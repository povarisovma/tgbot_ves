import sqlite3
from datetime import datetime

DB_PATH = "weight.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS weights (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                weight  REAL    NOT NULL,
                date    TEXT    NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS deletions (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date    TEXT    NOT NULL
            )
        """)
        conn.commit()


def already_recorded_today(user_id: int) -> bool:
    today = datetime.now().strftime("%Y-%m-%d")
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM weights WHERE user_id = ? AND date LIKE ? LIMIT 1",
            (user_id, f"{today}%"),
        ).fetchone()
    return row is not None


def add_weight(user_id: int, weight: float):
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO weights (user_id, weight, date) VALUES (?, ?, ?)",
            (user_id, weight, date),
        )
        conn.commit()


def get_stats() -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    with get_conn() as conn:
        total_users = conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM weights"
        ).fetchone()[0]
        total_records = conn.execute(
            "SELECT COUNT(*) FROM weights"
        ).fetchone()[0]
        today_records = conn.execute(
            "SELECT COUNT(*) FROM weights WHERE date LIKE ?",
            (f"{today}%",),
        ).fetchone()[0]
    return {
        "total_users": total_users,
        "total_records": total_records,
        "today_records": today_records,
    }


def deletions_today(user_id: int) -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM deletions WHERE user_id = ? AND date LIKE ?",
            (user_id, f"{today}%"),
        ).fetchone()
    return row[0]


def delete_last_weight(user_id: int) -> float | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, weight FROM weights WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        if row is None:
            return None
        conn.execute("DELETE FROM weights WHERE id = ?", (row["id"],))
        conn.execute(
            "INSERT INTO deletions (user_id, date) VALUES (?, ?)",
            (user_id, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        conn.commit()
    return row["weight"]


def get_history(user_id: int) -> list[sqlite3.Row]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT weight, date FROM weights WHERE user_id = ? ORDER BY id ASC",
            (user_id,),
        ).fetchall()
    return rows
