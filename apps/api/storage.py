from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any

from apps.api.domain import Assignment, Candidate, Dataset


def _json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), default=str)


class Storage:
    """Small persistence adapter with SQLite by default and optional PostgreSQL."""

    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL")
        self.sqlite_path = os.getenv("CRONOS_SQLITE_PATH", "apps/cronos.db")
        self._connection: Any = None
        self._postgres = False
        self._connect()

    def _connect(self) -> None:
        if self.database_url:
            try:
                import psycopg

                self._connection = psycopg.connect(self.database_url, autocommit=True)
                self._postgres = True
                self._execute(
                    """
                    CREATE TABLE IF NOT EXISTS cronos_state (
                        key TEXT PRIMARY KEY,
                        value JSONB NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
                return
            except ImportError as exc:
                raise RuntimeError("DATABASE_URL is configured but psycopg is not installed.") from exc
        os.makedirs(os.path.dirname(self.sqlite_path) or ".", exist_ok=True)
        self._connection = sqlite3.connect(self.sqlite_path, check_same_thread=False)
        self._execute(
            """
            CREATE TABLE IF NOT EXISTS cronos_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

    def _execute(self, query: str, params: tuple[Any, ...] = ()) -> Any:
        if self._postgres:
            with self._connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor
        cursor = self._connection.execute(query, params)
        self._connection.commit()
        return cursor

    def _read(self, key: str) -> Any | None:
        placeholder = "%s" if self._postgres else "?"
        if self._postgres:
            with self._connection.cursor() as cursor:
                cursor.execute(f"SELECT value FROM cronos_state WHERE key={placeholder}", (key,))
                row = cursor.fetchone()
        else:
            row = self._execute(f"SELECT value FROM cronos_state WHERE key={placeholder}", (key,)).fetchone()
        if not row:
            return None
        value = row[0]
        return value if isinstance(value, dict) else json.loads(value)

    def _write(self, key: str, value: Any) -> None:
        placeholder = "%s" if self._postgres else "?"
        encoded = value if self._postgres else _json(value)
        query = (
            f"INSERT INTO cronos_state(key, value, updated_at) VALUES ({placeholder}, {placeholder}, {placeholder}) "
            f"ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at"
        )
        self._execute(query, (key, encoded, datetime.now(timezone.utc).isoformat()))

    def load_dataset(self) -> Dataset:
        value = self._read("dataset")
        return Dataset.model_validate(value) if value else Dataset()

    def save_dataset(self, dataset: Dataset) -> None:
        self._write("dataset", dataset.model_dump(mode="json"))

    def save_run(self, run_id: str, record: dict[str, Any]) -> None:
        self._write(f"run:{run_id}", record)

    def load_run(self, run_id: str) -> dict[str, Any] | None:
        return self._read(f"run:{run_id}")

    def list_runs(self) -> list[dict[str, Any]]:
        placeholder = "%s" if self._postgres else "?"
        if self._postgres:
            with self._connection.cursor() as cursor:
                cursor.execute(f"SELECT key, value FROM cronos_state WHERE key LIKE {placeholder}", ("run:%",))
                rows = cursor.fetchall()
        else:
            rows = self._execute(f"SELECT key, value FROM cronos_state WHERE key LIKE {placeholder}", ("run:%",)).fetchall()
        values = []
        for key, value in rows:
            values.append(value if isinstance(value, dict) else json.loads(value))
        return sorted(values, key=lambda item: item.get("created_at", ""), reverse=True)

    def load_candidate(self, run_id: str) -> Candidate | None:
        value = self._read(f"candidate:{run_id}")
        if not value:
            return None
        return Candidate(
            assignments=[Assignment(**item) for item in value["assignments"]],
            hard_violations=value["hard_violations"],
            soft_penalty=value["soft_penalty"],
            violations=value["violations"],
        )

    def save_candidate(self, run_id: str, candidate: Candidate) -> None:
        self._write(
            f"candidate:{run_id}",
            {
                "assignments": [item.__dict__ for item in candidate.assignments],
                "hard_violations": candidate.hard_violations,
                "soft_penalty": candidate.soft_penalty,
                "violations": candidate.violations,
            },
        )
