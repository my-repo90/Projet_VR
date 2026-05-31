from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services import cluster_service

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.get("")
def list_clusters() -> list[dict]:
    return cluster_service.list_clusters()


@router.get("/{cluster_label}")
def get_cluster(cluster_label: int) -> dict:
    cluster = cluster_service.get_cluster(cluster_label)
    if cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return cluster


@router.get("/{cluster_label}/nodes")
def list_cluster_nodes(
    cluster_label: int,
    limit: int = Query(1000, ge=1, le=50000),
    offset: int = Query(0, ge=0),
) -> dict:
    return cluster_service.list_cluster_nodes(cluster_label, limit, offset)
