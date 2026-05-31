from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services import graph_service

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.get("")
def list_nodes(
    limit: int = Query(1000, ge=1, le=50000),
    offset: int = Query(0, ge=0),
    cluster_label: int | None = None,
    risk_level: str | None = None,
    anomaly_only: bool = False,
) -> dict:
    return graph_service.list_nodes(
        limit=limit,
        offset=offset,
        cluster_label=cluster_label,
        risk_level=risk_level,
        anomaly_only=anomaly_only,
    )


@router.get("/summary")
def nodes_summary() -> dict:
    return graph_service.nodes_summary()


@router.get("/{node_id}")
def get_node(node_id: str) -> dict:
    node = graph_service.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return node
