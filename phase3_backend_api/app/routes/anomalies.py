from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services import anomaly_service

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("")
def list_anomalies(
    limit: int = Query(1000, ge=1, le=50000),
    offset: int = Query(0, ge=0),
    min_score: float | None = Query(None, ge=0.0, le=1.0),
    risk_level: str | None = None,
) -> dict:
    return anomaly_service.list_anomalies(
        limit=limit,
        offset=offset,
        min_score=min_score,
        risk_level=risk_level,
    )


@router.get("/summary")
def anomalies_summary() -> dict:
    return anomaly_service.anomalies_summary()


@router.get("/top")
def top_anomalies(limit: int = Query(50, ge=1, le=1000)) -> dict:
    return anomaly_service.top_anomalies(limit)


@router.get("/{node_id}")
def get_anomaly(node_id: str) -> dict:
    anomaly = anomaly_service.get_anomaly(node_id)
    if anomaly is None:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return anomaly
