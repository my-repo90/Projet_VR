from __future__ import annotations

from typing import Any

from app.services.data_store import paginate, resolve_data_file, store


CLUSTERS_FILE = "clusters.json"
NODES_FILE = "nodes_3d.json"


def list_clusters() -> list[dict[str, Any]]:
    records = store.load(resolve_data_file(CLUSTERS_FILE))
    if not records:
        return build_cluster_summary_from_nodes()
    if "node_id" in records[0]:
        return build_cluster_summary_from_nodes()
    return records


def build_cluster_summary_from_nodes() -> list[dict[str, Any]]:
    nodes = store.load(resolve_data_file(NODES_FILE))
    grouped: dict[int, dict[str, Any]] = {}

    for node in nodes:
        label = node.get("cluster_label")
        if label is None:
            continue
        label = int(label)
        item = grouped.setdefault(
            label,
            {
                "cluster_label": label,
                "node_count": 0,
                "fraud_count": 0,
                "avg_anomaly_score": 0.0,
                "center_x": 0.0,
                "center_y": 0.0,
                "center_z": 0.0,
            },
        )
        item["node_count"] += 1
        item["fraud_count"] += int(node.get("is_fraud_node") or 0)
        item["avg_anomaly_score"] += float(node.get("anomaly_score") or 0)
        item["center_x"] += float(node.get("x") or 0)
        item["center_y"] += float(node.get("y") or 0)
        item["center_z"] += float(node.get("z") or 0)

    for item in grouped.values():
        count = max(item["node_count"], 1)
        item["avg_anomaly_score"] /= count
        item["center_x"] /= count
        item["center_y"] /= count
        item["center_z"] /= count

    return sorted(grouped.values(), key=lambda item: item["cluster_label"])


def get_cluster(cluster_label: int) -> dict[str, Any] | None:
    return next(
        (cluster for cluster in list_clusters() if cluster.get("cluster_label") == cluster_label),
        None,
    )


def list_cluster_nodes(cluster_label: int, limit: int, offset: int) -> dict[str, Any]:
    nodes = store.load(resolve_data_file(NODES_FILE))
    records = [node for node in nodes if node.get("cluster_label") == cluster_label]
    return paginate(records, limit, offset)
