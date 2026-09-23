from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel


ModelT = TypeVar("ModelT", bound=BaseModel)


class SQLiteStore:
    """Small SQLite persistence layer for the workbench domain objects."""

    TABLES = {
        "requirements": "requirements",
        "use_cases": "use_cases",
        "actors": "actors",
        "trace_links": "trace_links",
    }

    def __init__(self, database_path: str | Path = "data/requirements.db") -> None:
        self.database_path = Path(database_path)
        if str(self.database_path) != ":memory:":
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            for table in self.TABLES.values():
                connection.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                        id TEXT PRIMARY KEY,
                        payload TEXT NOT NULL
                    )
                    """
                )

    def list(self, table: str, model: type[ModelT]) -> list[ModelT]:
        self._validate_table(table)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT payload FROM {table} ORDER BY rowid"
            ).fetchall()
        return [model.model_validate(json.loads(row["payload"])) for row in rows]

    def get(self, table: str, model: type[ModelT], item_id: str) -> ModelT | None:
        self._validate_table(table)
        with self._connect() as connection:
            row = connection.execute(
                f"SELECT payload FROM {table} WHERE id = ?",
                (item_id,),
            ).fetchone()
        if row is None:
            return None
        return model.model_validate(json.loads(row["payload"]))

    def next_id(self, table: str, model: type[ModelT]) -> int:
        self._validate_table(table)
        with self._connect() as connection:
            rows = connection.execute(f"SELECT id FROM {table}").fetchall()
        return model.nextID(
            [model.model_validate({"id": row["id"]}) for row in rows]
        )

    def insert(self, table: str, item: ModelT) -> None:
        self._validate_table(table)
        payload = json.dumps(item.model_dump(mode="json"), ensure_ascii=False)
        with self._connect() as connection:
            connection.execute(
                f"INSERT INTO {table} (id, payload) VALUES (?, ?)",
                (item.id, payload),
            )

    def _validate_table(self, table: str) -> None:
        if table not in self.TABLES.values():
            raise ValueError(f"Unknown persistence table: {table}")
