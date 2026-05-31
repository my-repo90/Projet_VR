from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Anomaly(BaseModel):
    node_id: str
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    anomaly_score: float
    risk_level: Optional[str] = None
    cluster_label: Optional[int] = None
    is_fraud_node: Optional[int] = None
    display_color: Optional[str] = None
    total_amount: Optional[float] = None


class AnomalyQuery(BaseModel):
    limit: int = Field(default=1000, ge=1, le=50000)
    offset: int = Field(default=0, ge=0)
    min_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    risk_level: Optional[str] = None
