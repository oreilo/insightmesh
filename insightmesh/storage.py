"""SQLite persistence with scoped project resources."""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path: str):
        self.path = path
        if path != ":memory:":
            Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self):
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS research (
                id TEXT PRIMARY KEY, project_id TEXT NOT NULL, question TEXT NOT NULL,
                result TEXT NOT NULL, created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS evidence (
                id TEXT PRIMARY KEY, project_id TEXT NOT NULL, title TEXT NOT NULL,
                content TEXT NOT NULL, source TEXT NOT NULL, sha256 TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS datasets (
                id TEXT PRIMARY KEY, project_id TEXT NOT NULL, filename TEXT NOT NULL,
                profile TEXT NOT NULL, created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
            """)

    def create_project(self, name: str, description: str) -> dict:
        item = {"id": uuid.uuid4().hex, "name": name, "description": description,
                "created_at": timestamp()}
        with self.connect() as db:
            db.execute("INSERT INTO projects VALUES (:id,:name,:description,:created_at)", item)
        return item

    def list_projects(self) -> list[dict]:
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM projects ORDER BY created_at DESC")]

    def get_project(self, project_id: str) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        return dict(row) if row else None

    def save(self, table: str, project_id: str, payload: dict) -> dict:
        if table not in {"research", "evidence", "datasets"}:
            raise ValueError("Unknown resource")
        item = {"id": uuid.uuid4().hex, "project_id": project_id,
                "created_at": timestamp(), **payload}
        with self.connect() as db:
            columns = list(item)
            placeholders = ",".join("?" for _ in columns)
            db.execute(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
                       tuple(item[c] for c in columns))
        return item

    def list_items(self, table: str, project_id: str) -> list[dict]:
        if table not in {"research", "evidence", "datasets"}:
            raise ValueError("Unknown resource")
        with self.connect() as db:
            rows = db.execute(f"SELECT * FROM {table} WHERE project_id=? ORDER BY created_at DESC",
                              (project_id,)).fetchall()
        items = [dict(row) for row in rows]
        for item in items:
            for key in ("result", "profile"):
                if key in item:
                    item[key] = json.loads(item[key])
        return items
