import os
import sqlite3
from datetime import date
from pathlib import Path
from typing import Optional

from models import Goal

_data_dir = Path(os.environ.get("DATA_DIR", str(Path(__file__).parent)))
DB_PATH = _data_dir / "goals.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                description TEXT DEFAULT '',
                category    TEXT DEFAULT 'general',
                due_date    TEXT,
                status      TEXT DEFAULT 'pending',
                created_at  TEXT DEFAULT (date('now'))
            )
        """)


def _row_to_goal(row) -> Goal:
    return Goal(
        id=row[0],
        title=row[1],
        description=row[2],
        category=row[3],
        due_date=date.fromisoformat(row[4]) if row[4] else None,
        status=row[5],
        created_at=row[6],
    )


def add_goal(title: str, description: str, category: str, due_date: Optional[date]) -> Goal:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO goals (title, description, category, due_date) VALUES (?, ?, ?, ?)",
            (title, description, category, due_date.isoformat() if due_date else None),
        )
        row = conn.execute(
            "SELECT * FROM goals WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
    return _row_to_goal(row)


def list_goals(status: Optional[str] = None, category: Optional[str] = None) -> list[Goal]:
    query = "SELECT * FROM goals WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if category:
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY due_date IS NULL, due_date ASC, id ASC"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_goal(r) for r in rows]


def get_goal(goal_id: int) -> Optional[Goal]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
    return _row_to_goal(row) if row else None


def mark_done(goal_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE goals SET status = 'done' WHERE id = ? AND status = 'pending'",
            (goal_id,),
        )
    return cur.rowcount > 0


def update_goal(goal_id: int, title: str, description: str, category: str, due_date: Optional[date]) -> Optional[Goal]:
    with get_connection() as conn:
        conn.execute(
            "UPDATE goals SET title=?, description=?, category=?, due_date=? WHERE id=?",
            (title, description, category, due_date.isoformat() if due_date else None, goal_id),
        )
        row = conn.execute("SELECT * FROM goals WHERE id=?", (goal_id,)).fetchone()
    return _row_to_goal(row) if row else None


def mark_pending(goal_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE goals SET status = 'pending' WHERE id = ? AND status = 'done'",
            (goal_id,),
        )
    return cur.rowcount > 0


def delete_goal(goal_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    return cur.rowcount > 0


def get_due_today() -> list[Goal]:
    today = date.today().isoformat()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM goals WHERE status = 'pending' AND due_date = ?", (today,)
        ).fetchall()
    return [_row_to_goal(r) for r in rows]



def get_overdue() -> list[Goal]:
    today = date.today().isoformat()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM goals WHERE status = 'pending' AND due_date < ?", (today,)
        ).fetchall()
    return [_row_to_goal(r) for r in rows]
