"""Pure-Python CSV and JSONL dataset inspection."""
import csv
import io
import json
import math
from collections import Counter
from statistics import mean, median


def _rows(filename: str, content: str) -> list[dict]:
    suffix = filename.lower().rsplit(".", 1)[-1]
    if suffix == "csv":
        return list(csv.DictReader(io.StringIO(content)))
    if suffix in ("jsonl", "ndjson"):
        parsed = [json.loads(line) for line in content.splitlines() if line.strip()]
        if not all(isinstance(row, dict) for row in parsed):
            raise ValueError("JSONL must contain objects")
        return parsed
    raise ValueError("Supported formats: .csv, .jsonl, .ndjson")


def profile(filename: str, content: str) -> dict:
    rows = _rows(filename, content)
    if len(rows) > 100000:
        raise ValueError("Dataset exceeds 100,000 rows")
    columns = list(dict.fromkeys(key for row in rows for key in row))
    result = []
    for column in columns:
        values = [row.get(column) for row in rows]
        present = [v for v in values if v is not None and str(v).strip() != ""]
        nums = []
        for value in present:
            try:
                num = float(value)
                if math.isfinite(num):
                    nums.append(num)
            except (ValueError, TypeError):
                pass
        numeric = bool(present) and len(nums) == len(present)
        counts = Counter(str(v) for v in present)
        item = {"name": column, "type": "number" if numeric else "text",
                "missing": len(rows) - len(present), "unique": len(counts),
                "examples": [v for v, _ in counts.most_common(3)]}
        if numeric:
            item["statistics"] = {"min": min(nums), "max": max(nums),
                                  "mean": mean(nums), "median": median(nums)}
        result.append(item)
    return {"filename": filename, "rows": len(rows), "columns": result,
            "column_count": len(columns)}
