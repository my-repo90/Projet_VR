from __future__ import annotations

from typing import Any

from app.services.data_store import filter_records, paginate, resolve_data_file, store


NODES_FILE = "nodes_3d.json"
EDGES_FILE = "edges.json"


def list_nodes(
    limit: int = 1000,
    offset: int = 0,
    cluster_label: int | None = None,
    risk_level: str | None = None,
    anomaly_only: bool = False,
) -> dict[str, Any]:
    records = store.load(resolve_data_file(NODES_FILE))
    records = filter_records(records, cluster_label=cluster_label, risk_level=risk_level)
    if anomaly_only:
        records = [
            record
            for record in records
            if record.get("anomaly_label") == 1 or float(record.get("anomaly_score") or 0) > 0
        ]
    return paginate(records, limit, offset)


def get_node(node_id: str) -> dict[str, Any] | None:
    records = store.load(resolve_data_file(NODES_FILE))
    return next((record for record in records if record.get("node_id") == node_id), None)


def nodes_summary() -> dict[str, Any]:
    records = store.load(resolve_data_file(NODES_FILE))
    risk_distribution: dict[str, int] = {}
    cluster_distribution: dict[str, int] = {}
    anomalies = 0

    for record in records:
        risk = str(record.get("risk_level", "unknown"))
        cluster = str(record.get("cluster_label", "unknown"))
        risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
        cluster_distribution[cluster] = cluster_distribution.get(cluster, 0) + 1
        if record.get("anomaly_label") == 1:
            anomalies += 1

    return {
        "total_nodes": len(records),
        "total_anomalies": anomalies,
        "risk_distribution": risk_distribution,
        "cluster_distribution": cluster_distribution,
    }


def list_edges(
    limit: int = 1000,
    offset: int = 0,
    source: str | None = None,
    target: str | None = None,
    fraud_only: bool = False,
    transaction_type: str | None = None,
) -> dict[str, Any]:
    records = store.load(resolve_data_file(EDGES_FILE))
    records = filter_records(records, source=source, target=target, type=transaction_type)
    if fraud_only:
        records = [record for record in records if record.get("is_fraud") in (1, True)]
    return paginate(records, limit, offset)


def get_edge(edge_id: str) -> dict[str, Any] | None:
    records = store.load(resolve_data_file(EDGES_FILE))
    return next((record for record in records if str(record.get("edge_id")) == edge_id), None)
