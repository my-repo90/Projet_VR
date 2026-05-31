from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Edge(BaseModel):
    source: str
    target: str
    amount: Optional[float] = None
    log_amount: Optional[float] = None
    is_fraud: Optional[int] = None
    step: Optional[int] = None
    type: Optional[str] = None
    edge_id: Optional[str] = None


class EdgeQuery(BaseModel):
    limit: int = Field(default=1000, ge=1, le=50000)
    offset: int = Field(default=0, ge=0)
    source: Optional[str] = None
    target: Optional[str] = None
    fraud_only: bool = False
    transaction_type: Optional[str] = None
