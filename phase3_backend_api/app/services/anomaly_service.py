from __future__ import annotations

from typing import Any

from app.services.data_store import filter_records, paginate, resolve_data_file, store


ANOMALIES_FILE = "anomalies.json"


def _sorted_anomalies() -> list[dict[str, Any]]:
    records = store.load(resolve_data_file(ANOMALIES_FILE))
    return sorted(records, key=lambda record: float(record.get("anomaly_score") or 0), reverse=True)


def list_anomalies(
    limit: int = 1000,
    offset: int = 0,
    min_score: float | None = None,
    risk_level: str | None = None,
) -> dict[str, Any]:
    records = filter_records(_sorted_anomalies(), risk_level=risk_level)
    if min_score is not None:
        records = [
            record
            for record in records
            if float(record.get("anomaly_score") or 0) >= min_score
        ]
    return paginate(records, limit, offset)


def top_anomalies(limit: int = 50) -> dict[str, Any]:
    return paginate(_sorted_anomalies(), limit, 0)


def get_anomaly(node_id: str) -> dict[str, Any] | None:
    records = _sorted_anomalies()
    return next((record for record in records if record.get("node_id") == node_id), None)


def anomalies_summary() -> dict[str, Any]:
    records = _sorted_anomalies()
    risk_distribution: dict[str, int] = {}
    for record in records:
        risk = str(record.get("risk_level", "unknown"))
        risk_distribution[risk] = risk_distribution.get(risk, 0) + 1

    max_score = float(records[0].get("anomaly_score") or 0) if records else 0
    return {
        "total_anomalies": len(records),
        "max_score": max_score,
        "risk_distribution": risk_distribution,
    }
