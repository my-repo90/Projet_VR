from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class Cluster(BaseModel):
    cluster_label: int
    node_count: Optional[int] = None
    fraud_count: Optional[int] = None
    avg_anomaly_score: Optional[float] = None
    center_x: Optional[float] = None
    center_y: Optional[float] = None
    center_z: Optional[float] = None


class ClusterMembership(BaseModel):
    node_id: str
    cluster_label: int
    cluster_prob: Optional[float] = None
