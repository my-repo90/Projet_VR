from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from threading import RLock
from typing import Any, Iterable

from app.config import settings

logger = logging.getLogger(__name__)


class DataStore:
    """Small data cache keyed by resolved file path and modification time."""

    def __init__(self) -> None:
        self._cache: dict[Path, tuple[float, list[dict[str, Any]]]] = {}
        self._lock = RLock()

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def load(self, path: Path | None) -> list[dict[str, Any]]:
        if path is None or not path.exists():
            return []

        resolved = path.resolve()
        mtime = resolved.stat().st_mtime

        with self._lock:
            cached = self._cache.get(resolved)
            if cached and cached[0] == mtime:
                return cached[1]

            logger.info("Loading data: %s", resolved)
            if resolved.suffix.lower() == ".csv":
                records = self._load_csv(resolved)
            else:
                records = self._load_json(resolved)

            if not isinstance(records, list):
                records = []

            self._cache[resolved] = (mtime, records)
            return records

    def _load_json(self, path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        if isinstance(payload, dict):
            records = payload.get("data", [])
        else:
            records = payload

        return records if isinstance(records, list) else []

    def _load_csv(self, path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8", newline="") as file:
            return [
                {key: _coerce_csv_value(value) for key, value in row.items()}
                for row in csv.DictReader(file)
            ]


def _coerce_csv_value(value: str | None) -> Any:
    if value is None or value == "":
        return None
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


store = DataStore()


def resolve_data_file(filename: str) -> Path | None:
    if filename == "clusters.json":
        candidates = [
            settings.data_dir / "clusters.json",
            settings.data_dir / "clusters_summary.json",
            settings.phase2_export_dir / "clusters_summary.json",
            settings.phase1_export_dir / "clusters_summary.json",
            settings.phase2_export_dir / "clusters.json",
            settings.phase1_export_dir / "clusters.json",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve()
        return None

    candidates = [
        settings.data_dir / filename,
        settings.phase2_export_dir / filename,
        settings.phase1_export_dir / filename,
        settings.project_data_dir / filename,
    ]

    fallback_names = {
        "edges.json": ["edges.json", "edges.csv"],
    }
    for alt_name in fallback_names.get(filename, []):
        candidates.extend(
            [
                settings.data_dir / alt_name,
                settings.phase2_export_dir / alt_name,
                settings.phase1_export_dir / alt_name,
                settings.project_data_dir / alt_name,
            ]
        )

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return None


def paginate(records: list[dict[str, Any]], limit: int, offset: int) -> dict[str, Any]:
    return {
        "total": len(records),
        "limit": limit,
        "offset": offset,
        "items": records[offset : offset + limit],
    }


def filter_records(
    records: Iterable[dict[str, Any]],
    **filters: Any,
) -> list[dict[str, Any]]:
    filtered = list(records)
    for key, expected in filters.items():
        if expected is None:
            continue
        filtered = [record for record in filtered if record.get(key) == expected]
    return filtered
