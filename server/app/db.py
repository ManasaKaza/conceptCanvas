import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "conceptcanvas.db"


def get_now() -> str:
    return datetime.utcnow().isoformat()


def create_id() -> str:
    return str(uuid.uuid4())


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                first_question TEXT NOT NULL,
                last_question TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_turns (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                question TEXT NOT NULL,
                mode TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.commit()


def create_title(question: str) -> str:
    cleaned_question = question.strip()

    if len(cleaned_question) <= 60:
        return cleaned_question

    return f"{cleaned_question[:60]}..."


def list_conversations() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                c.id,
                c.title,
                c.first_question,
                c.last_question,
                c.created_at,
                c.updated_at,
                COUNT(t.id) AS question_count
            FROM conversations c
            LEFT JOIN conversation_turns t
                ON c.id = t.conversation_id
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def get_conversation(conversation_id: str) -> dict | None:
    with get_connection() as connection:
        conversation_row = connection.execute(
            """
            SELECT
                id,
                title,
                first_question,
                last_question,
                created_at,
                updated_at
            FROM conversations
            WHERE id = ?
            """,
            (conversation_id,),
        ).fetchone()

        if not conversation_row:
            return None

        turn_rows = connection.execute(
            """
            SELECT
                id,
                question,
                mode,
                result_json,
                created_at
            FROM conversation_turns
            WHERE conversation_id = ?
            ORDER BY created_at ASC
            """,
            (conversation_id,),
        ).fetchall()

    turns = []

    for row in turn_rows:
        turn = dict(row)
        turn["result"] = json.loads(turn.pop("result_json"))
        turns.append(turn)

    conversation = dict(conversation_row)
    conversation["turns"] = turns

    return conversation


def save_turn(
    conversation_id: str | None,
    question: str,
    mode: str,
    result: dict,
) -> dict:
    now = get_now()

    with get_connection() as connection:
        if conversation_id:
            existing_conversation = connection.execute(
                """
                SELECT id
                FROM conversations
                WHERE id = ?
                """,
                (conversation_id,),
            ).fetchone()
        else:
            existing_conversation = None

        if not existing_conversation:
            conversation_id = create_id()

            connection.execute(
                """
                INSERT INTO conversations (
                    id,
                    title,
                    first_question,
                    last_question,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    conversation_id,
                    create_title(question),
                    question,
                    question,
                    now,
                    now,
                ),
            )
        else:
            connection.execute(
                """
                UPDATE conversations
                SET
                    last_question = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (question, now, conversation_id),
            )

        turn_id = create_id()

        connection.execute(
            """
            INSERT INTO conversation_turns (
                id,
                conversation_id,
                question,
                mode,
                result_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                turn_id,
                conversation_id,
                question,
                mode,
                json.dumps(result),
                now,
            ),
        )

        connection.commit()

    return {
        "conversationId": conversation_id,
        "turnId": turn_id,
    }


def delete_conversation(conversation_id: str) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM conversations
            WHERE id = ?
            """,
            (conversation_id,),
        )

        connection.commit()

    return cursor.rowcount > 0


def clear_conversation_turns(conversation_id: str) -> bool:
    now = get_now()

    with get_connection() as connection:
        existing_conversation = connection.execute(
            """
            SELECT id
            FROM conversations
            WHERE id = ?
            """,
            (conversation_id,),
        ).fetchone()

        if not existing_conversation:
            return False

        connection.execute(
            """
            DELETE FROM conversation_turns
            WHERE conversation_id = ?
            """,
            (conversation_id,),
        )

        connection.execute(
            """
            UPDATE conversations
            SET
                last_question = '',
                updated_at = ?
            WHERE id = ?
            """,
            (now, conversation_id),
        )

        connection.commit()

    return True