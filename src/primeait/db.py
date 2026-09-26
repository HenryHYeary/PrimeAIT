import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
import aiosqlite

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "primeait.db"

async def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL REFERENCES threads(id),
                question TEXT NOT NULL,
                answers TEXT NOT NULL,
                winner TEXT NOT NULL,
                feedback TEXT,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()


async def create_thread(title: str | None = None) -> dict:
    thread_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO threads (id, title, created_at) VALUES (?, ?, ?)",
            (thread_id, title or "New conversation", created_at),
        )
        await db.commit()
    return {"id": thread_id, "title": title or "New conversation", "created_at": created_at}


async def list_threads() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT id, title, created_at FROM threads ORDER BY created_at DESC")
        return [dict(r) for r in await cursor.fetchall()]


async def get_rounds(thread_id: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT question, answers, winner, feedback, created_at FROM rounds "
            "WHERE thread_id = ? ORDER BY id ASC",
            (thread_id,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "question": r["question"],
                "answers": json.loads(r["answers"]),
                "winner": r["winner"],
                "feedback": r["feedback"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]


async def insert_round(thread_id: str, question: str, answers: dict, winner: str, feedback: str):
    created_at = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO rounds (thread_id, question, answers, winner, feedback, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (thread_id, question, json.dumps(answers), winner, feedback, created_at),
        )
        db.commit()