"""OREiLO data intelligence: filtering, grouping and safe read-only SQL."""
import csv
import io
import json
import math
import sqlite3
from collections import defaultdict
from statistics import mean


def parse_data(filename: str, content: str) -> list[dict]:
    ext = filename.lower().split(".")[-1]
    if ext == "csv":
        records = list(csv.DictReader(io.StringIO(content)))
    elif ext in {"jsonl", "ndjson"}:
        records = [json.loads(line) for line in content.splitlines() if line.strip()]
    elif ext == "json":
        records = json.loads(content)
        if isinstance(records, dict):
            records = records.get("data", [records])
    else:
        raise ValueError("Supported formats: CSV, JSON, JSONL, NDJSON")
    if not isinstance(records, list) or not all(isinstance(r, dict) for r in records):
        raise ValueError("Expected a list of records")
    if len(records) > 100000:
        raise ValueError("Maximum 100,000 records")
    return records


def summarize(filename: str, content: str, group_by: str, metric: str) -> dict:
    rows = parse_data(filename, content)
    if not rows or group_by not in rows[0] or metric not in rows[0]:
        raise ValueError("Group and metric columns must exist")
    buckets = defaultdict(list)
    for row in rows:
        try:
            value = float(row.get(metric, ""))
            if math.isfinite(value):
                buckets[str(row.get(group_by, ""))].append(value)
        except (TypeError, ValueError):
            continue
    return {"group_by": group_by, "metric": metric, "groups": [
        {"label": label, "count": len(values), "sum": round(sum(values), 6),
         "mean": round(mean(values), 6), "min": min(values), "max": max(values)}
        for label, values in sorted(buckets.items())]}


def query_data(filename: str, content: str, sql: str) -> dict:
    statement = sql.strip().rstrip(";").strip()
    if not statement.lower().startswith("select ") or ";" in statement:
        raise ValueError("Only one SELECT statement is allowed")
    rows = parse_data(filename, content)
    columns = list(dict.fromkeys(k for row in rows for k in row))
    if not columns:
        return {"columns": [], "rows": []}
    with sqlite3.connect(":memory:") as db:
        db.set_authorizer(lambda action, arg1, arg2, dbname, source: sqlite3.SQLITE_OK if action in {
            sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE} else sqlite3.SQLITE_DENY)
        # Authorizer must be set AFTER creating the in-memory table.
        db.set_authorizer(None)
        quoted = ["\"" + c.replace("\"", "\"\"") + "\"" for c in columns]
        db.execute("CREATE TABLE dataset (" + ",".join(c + " TEXT" for c in quoted) + ")")
        db.executemany("INSERT INTO dataset VALUES (" + ",".join("?" for _ in columns) + ")",
                       [[row.get(c) for c in columns] for row in rows])
        db.set_authorizer(lambda action, a, b, c, d: sqlite3.SQLITE_OK if action in {
            sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE} else sqlite3.SQLITE_DENY)
        cursor = db.execute("SELECT * FROM (" + statement + ") LIMIT 501")
        result = cursor.fetchmany(501)
        if len(result) > 500:
            raise ValueError("Query exceeds 500 output rows")
        db.set_authorizer(None)
        return {"columns": [d[0] for d in cursor.description], "rows": [list(r) for r in result]}
