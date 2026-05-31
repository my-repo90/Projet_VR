from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services import graph_service

router = APIRouter(prefix="/edges", tags=["edges"])


@router.get("")
def list_edges(
    limit: int = Query(1000, ge=1, le=50000),
    offset: int = Query(0, ge=0),
    source: str | None = None,
    target: str | None = None,
    fraud_only: bool = False,
    transaction_type: str | None = None,
) -> dict:
    return graph_service.list_edges(
        limit=limit,
        offset=offset,
        source=source,
        target=target,
        fraud_only=fraud_only,
        transaction_type=transaction_type,
    )


@router.get("/{edge_id}")
def get_edge(edge_id: str) -> dict:
    edge = graph_service.get_edge(edge_id)
    if edge is None:
        raise HTTPException(status_code=404, detail="Edge not found")
    return edge
