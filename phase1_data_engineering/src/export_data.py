"""
export_data.py
Export JSON + Parquet pour Phase 2.
"""

import pandas as pd
import numpy as np
import json
import os
import logging

logger = logging.getLogger(__name__)

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "export")


def _convert(obj):
    if isinstance(obj, (np.integer,)):  return int(obj)
    if isinstance(obj, (np.floating,)): return float(obj)
    if isinstance(obj, (np.ndarray,)):  return obj.tolist()
    if isinstance(obj, (np.bool_,)):    return bool(obj)
    raise TypeError(f"Non sérialisable : {type(obj)}")


def export_nodes_json(nodes, path=None):
    if path is None:
        path = os.path.join(EXPORT_DIR, "nodes.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    records = nodes.to_dict(orient="records")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, default=_convert, ensure_ascii=False)
    logger.info(f"nodes.json → {path} ({len(records):,})")
    return path


def export_edges_json(edges, path=None):
    if path is None:
        path = os.path.join(EXPORT_DIR, "edges.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cols = ["source", "target", "amount", "log_amount", "is_fraud", "step", "type", "edge_id"]
    cols = [c for c in cols if c in edges.columns]
    records = edges[cols].to_dict(orient="records")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, default=_convert, ensure_ascii=False)
    logger.info(f"edges.json → {path} ({len(records):,})")
    return path


def export_summary(nodes, edges, features, path=None):
    if path is None:
        path = os.path.join(EXPORT_DIR, "summary.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    summary = {
        "pipeline":            "phase1_data_engineering",
        "n_nodes":             int(len(nodes)),
        "n_edges":             int(len(edges)),
        "n_features_per_node": int(len(features.columns)),
        "fraud_nodes":         int(nodes["is_fraud_node"].sum()),
        "fraud_edges":         int(edges["is_fraud"].sum()),
        "account_types":       nodes["account_type"].value_counts().to_dict(),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, default=_convert, indent=2, ensure_ascii=False)
    logger.info(f"summary.json → {path}")
    return path


def export_all(nodes, edges, features):
    logger.info("=== Export ===")
    paths = {
        "nodes_json":   export_nodes_json(nodes),
        "edges_json":   export_edges_json(edges),
        "summary_json": export_summary(nodes, edges, features),
    }
    logger.info("=== Export terminé ===")
    return paths