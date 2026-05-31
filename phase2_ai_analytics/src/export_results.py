"""
export_results.py — Phase 2
Export JSON pour Phase 3 backend.
"""
'''
import pandas as pd
import numpy as np
import json, os, logging

logger     = logging.getLogger(__name__)
EXPORT_DIR  = os.path.join(os.path.dirname(__file__), "..", "data", "export")


def _to_python(obj):
    if isinstance(obj, (np.integer,)):  return int(obj)
    if isinstance(obj, (np.floating,)): return float(obj)
    if isinstance(obj, (np.ndarray,)):  return obj.tolist()
    if isinstance(obj, (np.bool_,)):    return bool(obj)
    raise TypeError(f"Non sérialisable : {type(obj)}")


def export_nodes_3d_json(df_final, path=None):
    if path is None:
        path = os.path.join(EXPORT_DIR, "nodes_3d.json")
    cols = ["node_id","x","y","z","cluster_label","cluster_prob",
            "anomaly_score","anomaly_label","risk_level",
            "display_color","display_size","display_shape",
            "account_type","is_fraud_node","total_tx_count","total_amount"]
    cols    = [c for c in cols if c in df_final.columns]
    records = df_final[cols].to_dict(orient="records")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, default=_to_python, ensure_ascii=False)
    logger.info(f"nodes_3d.json → {path} ({len(records):,})")
    return path


def export_anomalies_json(df_final, min_score=0.5, path=None):
    if path is None:
        path = os.path.join(EXPORT_DIR, "anomalies.json")
    df   = df_final[df_final["anomaly_score"] >= min_score].copy()
    df   = df.sort_values("anomaly_score", ascending=False)
    cols = ["node_id","x","y","z","anomaly_score","risk_level",
            "cluster_label","is_fraud_node","display_color","total_amount"]
    cols    = [c for c in cols if c in df.columns]
    records = df[cols].to_dict(orient="records")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, default=_to_python, ensure_ascii=False)
    logger.info(f"anomalies.json → {path} ({len(records):,})")
    return path


def export_clusters_json(df_final, path=None):
    if path is None:
        path = os.path.join(EXPORT_DIR, "clusters_summary.json")
    if "cluster_label" not in df_final.columns:
        return None
    stats = df_final.groupby("cluster_label").agg(
        node_count        =("node_id","count"),
        fraud_count       =("is_fraud_node","sum"),
        avg_anomaly_score =("anomaly_score","mean"),
        center_x          =("x","mean"),
        center_y          =("y","mean"),
        center_z          =("z","mean"),
    ).reset_index()
    records = stats.to_dict(orient="records")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, default=_to_python, ensure_ascii=False)
    logger.info(f"clusters_summary.json → {path}")
    return path


def export_summary_json(df_final, path=None):
    if path is None:
        path = os.path.join(EXPORT_DIR, "summary_phase2.json")
    summary = {
        "pipeline":         "phase2_ai_analytics",
        "n_nodes":          int(len(df_final)),
        "n_clusters":       int(df_final["cluster_label"].nunique()) if "cluster_label" in df_final else 0,
        "n_anomalies":      int(df_final["anomaly_label"].sum()) if "anomaly_label" in df_final else 0,
        "risk_distribution": df_final["risk_level"].value_counts().to_dict() if "risk_level" in df_final else {},
        "columns":          list(df_final.columns),
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, default=_to_python, indent=2, ensure_ascii=False)
    logger.info(f"summary_phase2.json → {path}")
    return path


def export_all_results(df_final):
    logger.info("=== Export Phase 2 ===")
    paths = {
        "nodes_3d_json":         export_nodes_3d_json(df_final),
        "anomalies_json":        export_anomalies_json(df_final),
        "clusters_summary_json": export_clusters_json(df_final),
        "summary_json":          export_summary_json(df_final),
    }
    logger.info("=== Export terminé ===")
    return paths
'''
"""
export_results.py — Phase 2
Export des résultats IA vers JSON pour backend + Unity VR + dashboard.
"""

import pandas as pd
import numpy as np
import json, os, logging

logger = logging.getLogger(__name__)

EXPORT_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "export"
)

# =========================
# UTILITAIRE SERIALIZATION
# =========================
def _to_python(obj):
    """Convertit numpy → JSON serializable"""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    raise TypeError(f"Non sérialisable : {type(obj)}")


# =========================
# NODES 3D (UNITY INPUT)
# =========================
def export_nodes_3d_json(df_final, path=None):
    if path is None:
        path = os.path.join(EXPORT_DIR, "nodes_3d.json")

    cols = [
        "node_id","x","y","z",
        "cluster_label","cluster_prob",
        "anomaly_score","anomaly_label",
        "risk_level","display_color",
        "display_size","display_shape",
        "account_type","is_fraud_node",
        "total_tx_count","total_amount"
    ]

    cols = [c for c in cols if c in df_final.columns]
    records = df_final[cols].to_dict(orient="records")

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, default=_to_python, ensure_ascii=False)

    logger.info(f"nodes_3d.json → {path} ({len(records):,})")
    return path


# =========================
# ANOMALIES
# =========================
def export_anomalies_json(df_final, min_score=0.5, path=None):
    if path is None:
        path = os.path.join(EXPORT_DIR, "anomalies.json")

    df = df_final[df_final["anomaly_score"] >= min_score].copy()
    df = df.sort_values("anomaly_score", ascending=False)

    cols = [
        "node_id","x","y","z",
        "anomaly_score","risk_level",
        "cluster_label","is_fraud_node",
        "display_color","total_amount"
    ]

    cols = [c for c in cols if c in df.columns]
    records = df[cols].to_dict(orient="records")

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, default=_to_python, ensure_ascii=False)

    logger.info(f"anomalies.json → {path} ({len(records):,})")
    return path


# =========================
# CLUSTERS SUMMARY (GLOBAL STATS)
# =========================
def export_clusters_summary_json(df_final, path=None):
    if path is None:
        path = os.path.join(EXPORT_DIR, "clusters_summary.json")

    if "cluster_label" not in df_final.columns:
        return None

    stats = df_final.groupby("cluster_label").agg(
        node_count        =("node_id", "count"),
        fraud_count       =("is_fraud_node", "sum"),
        avg_anomaly_score =("anomaly_score", "mean"),
        center_x          =("x", "mean"),
        center_y          =("y", "mean"),
        center_z          =("z", "mean"),
    ).reset_index()

    records = stats.to_dict(orient="records")

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, default=_to_python, ensure_ascii=False)

    logger.info(f"clusters_summary.json → {path}")
    return path


# =========================
# CLUSTERS (NODE-LEVEL MAPPING) ⭐ IMPORTANT
# =========================
def export_clusters_json(df_final, path=None):
    if path is None:
        path = os.path.join(EXPORT_DIR, "clusters.json")

    if "cluster_label" not in df_final.columns:
        return None

    cols = ["node_id", "cluster_label", "cluster_prob"]
    cols = [c for c in cols if c in df_final.columns]

    records = df_final[cols].to_dict(orient="records")

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, default=_to_python, ensure_ascii=False)

    logger.info(f"clusters.json → {path} ({len(records):,})")
    return path


# =========================
# SUMMARY GLOBAL PHASE 2
# =========================
def export_summary_json(df_final, path=None):
    if path is None:
        path = os.path.join(EXPORT_DIR, "summary_phase2.json")

    summary = {
        "pipeline":    "phase2_ai_analytics",
        "n_nodes":     int(len(df_final)),
        "n_clusters":   int(df_final["cluster_label"].nunique()) if "cluster_label" in df_final else 0,
        "n_anomalies":  int(df_final["anomaly_label"].sum()) if "anomaly_label" in df_final else 0,
        "risk_distribution": df_final["risk_level"].value_counts().to_dict()
            if "risk_level" in df_final else {},
        "columns": list(df_final.columns)
    }

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, default=_to_python, indent=2, ensure_ascii=False)

    logger.info(f"summary_phase2.json → {path}")
    return path


# =========================
# MAIN EXPORT PIPELINE
# =========================
def export_all_results(df_final):
    logger.info("=== Export Phase 2 START ===")

    paths = {
        "nodes_3d_json":         export_nodes_3d_json(df_final),
        "anomalies_json":        export_anomalies_json(df_final),
        "clusters_json":         export_clusters_json(df_final),        # ⭐ IMPORTANT
        "clusters_summary_json": export_clusters_summary_json(df_final),
        "summary_json":          export_summary_json(df_final),
    }

    logger.info("=== Export Phase 2 DONE ===")
    return paths