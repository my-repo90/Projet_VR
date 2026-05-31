from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Position3D(BaseModel):
    x: float
    y: float
    z: float


class Node(BaseModel):
    node_id: str
    x: float
    y: float
    z: float
    cluster_label: Optional[int] = None
    cluster_prob: Optional[float] = None
    anomaly_score: Optional[float] = None
    anomaly_label: Optional[int] = None
    risk_level: Optional[str] = None
    display_color: Optional[str] = None
    display_size: Optional[float] = None
    display_shape: Optional[str] = None
    account_type: Optional[str] = None
    is_fraud_node: Optional[int] = None
    total_tx_count: Optional[float] = None
    total_amount: Optional[float] = None


class NodeQuery(BaseModel):
    limit: int = Field(default=1000, ge=1, le=50000)
    offset: int = Field(default=0, ge=0)
    cluster_label: Optional[int] = None
    risk_level: Optional[str] = None
    anomaly_only: bool = False
