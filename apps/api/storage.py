from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any

from apps.api.domain import Assignment, Candidate, Dataset


class StorageError(RuntimeError):
    """Raised when the configured persistence backend cannot be used."""


def _json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), default=str)


class Storage:
    """Persistence adapter with SQLite for local development and PostgreSQL on Vercel."""

    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL")
        self.sqlite_path = os.getenv("CRONOS_SQLITE_PATH", "apps/cronos.db")
        self._connection: Any = None
        self._postgres = False
        self._postgres_errors: tuple[type[BaseException], ...] = ()
        self._initialization_error: StorageError | None = None
        self._lock = threading.RLock()
        try:
            self._connect()
        except StorageError as exc:
            # Keep the ASGI application importable so non-storage endpoints
            # (for example model discovery) remain available. Storage-backed
            # requests fail explicitly through the exception handler.
            self._initialization_error = exc

    def _ensure_available(self) -> None:
        if self._initialization_error is not None:
            raise self._initialization_error

    def _connect(self) -> None:
        if os.getenv("VERCEL") and not self.database_url:
            raise StorageError("DATABASE_URL must be configured when running on Vercel.")
        if self.database_url:
            try:
                import psycopg
                from psycopg import InterfaceError, OperationalError
            except ImportError as exc:
                raise StorageError("DATABASE_URL is configured but psycopg is not installed.") from exc
            self._postgres_errors = (OperationalError, InterfaceError)
            try:
                connection = psycopg.connect(
                    self.database_url,
                    autocommit=True,
                    connect_timeout=10,
                    prepare_threshold=None,
                )
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS cronos_state (
                            key TEXT PRIMARY KEY,
                            value JSONB NOT NULL,
                            updated_at TIMESTAMPTZ NOT NULL
                        )
                        """
                    )
                self._connection = connection
                self._postgres = True
                return
            except self._postgres_errors as exc:
                self._connection = None
                self._postgres = False
                raise StorageError(
                    "The configured PostgreSQL database could not be reached or initialized."
                ) from exc
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
        self._ensure_available()
        with self._lock:
            if self._postgres:
                try:
                    with self._connection.cursor() as cursor:
                        cursor.execute(query, params)
                        return cursor
                except self._postgres_errors as exc:
                    self._connect()
                    try:
                        with self._connection.cursor() as cursor:
                            cursor.execute(query, params)
                            return cursor
                    except self._postgres_errors as retry_error:
                        raise StorageError("The PostgreSQL database is temporarily unavailable.") from retry_error
            cursor = self._connection.execute(query, params)
            self._connection.commit()
            return cursor

    def _read(self, key: str) -> Any | None:
        self._ensure_available()
        placeholder = "%s" if self._postgres else "?"
        with self._lock:
            if self._postgres:
                try:
                    with self._connection.cursor() as cursor:
                        cursor.execute(f"SELECT value FROM cronos_state WHERE key={placeholder}", (key,))
                        row = cursor.fetchone()
                except self._postgres_errors:
                    self._connect()
                    try:
                        with self._connection.cursor() as cursor:
                            cursor.execute(f"SELECT value FROM cronos_state WHERE key={placeholder}", (key,))
                            row = cursor.fetchone()
                    except self._postgres_errors as retry_error:
                        raise StorageError("The PostgreSQL database is temporarily unavailable.") from retry_error
            else:
                row = self._execute(f"SELECT value FROM cronos_state WHERE key={placeholder}", (key,)).fetchone()
        if not row:
            return None
        value = row[0]
        return value if isinstance(value, dict) else json.loads(value)

    def health(self) -> None:
        """Run a cheap read so health checks detect database failures."""
        self._read("dataset")

    def _write(self, key: str, value: Any) -> None:
        placeholder = "%s" if self._postgres else "?"
        if self._postgres:
            from psycopg.types.json import Jsonb

            encoded = Jsonb(value)
        else:
            encoded = _json(value)
        query = (
            f"INSERT INTO cronos_state(key, value, updated_at) VALUES ({placeholder}, {placeholder}, {placeholder}) "
            f"ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at"
        )
        self._execute(query, (key, encoded, datetime.now(timezone.utc).isoformat()))

    def load_dataset(self) -> Dataset:
        value = self._read("dataset")
        return Dataset.model_validate(value) if value else Dataset()

    def dataset_exists(self) -> bool:
        return self._read("dataset") is not None

    def save_dataset(self, dataset: Dataset) -> None:
        self._write("dataset", dataset.model_dump(mode="json"))

    def replace_dataset(self, dataset: Dataset) -> None:
        """Clear runs and replace the dataset under one process/database lock."""
        with self._lock:
            self._execute("DELETE FROM cronos_state")
            self._write("dataset", dataset.model_dump(mode="json"))

    def clear_all(self) -> None:
        self._execute("DELETE FROM cronos_state")

    def save_run(self, run_id: str, record: dict[str, Any]) -> None:
        self._write(f"run:{run_id}", record)

    def load_run(self, run_id: str) -> dict[str, Any] | None:
        return self._read(f"run:{run_id}")

    def list_runs(self) -> list[dict[str, Any]]:
        placeholder = "%s" if self._postgres else "?"
        with self._lock:
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
