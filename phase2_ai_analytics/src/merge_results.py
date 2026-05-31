"""
merge_results.py — Phase 2
Fusion de tous les résultats → final_nodes.parquet
"""

import pandas as pd
import numpy as np
import os, logging

logger     = logging.getLogger(__name__)
FINAL_PATH  = os.path.join(os.path.dirname(__file__), "..", "data", "output", "final_nodes.parquet")


def merge_all_results(df_features, df_3d, df_clusters, df_anomalies):
    logger.info("=== Fusion ===")
    df   = df_features.copy()
    n    = len(df)

    df = df.merge(df_3d[["node_id","x","y","z"]], on="node_id", how="left")

    cluster_cols = ["node_id","cluster_label","cluster_prob",
                    "cluster_size","fraud_node_rate","avg_total_amount"]
    cluster_cols = [c for c in cluster_cols if c in df_clusters.columns]
    df = df.merge(df_clusters[cluster_cols], on="node_id", how="left")

    anomaly_cols = ["node_id","anomaly_score","anomaly_label","risk_level",
                    "if_raw_score","if_label"]
    anomaly_cols = [c for c in anomaly_cols if c in df_anomalies.columns]
    df = df.merge(df_anomalies[anomaly_cols], on="node_id", how="left")

    assert len(df) == n, f"Perte de nœuds ! {n} → {len(df)}"

    df["cluster_label"] = df["cluster_label"].fillna(-1).astype(int)
    df["anomaly_label"] = df["anomaly_label"].fillna(0).astype(int)
    df["risk_level"]    = df["risk_level"].fillna("normal").astype(str)
    for col in ["x","y","z"]:
        df[col] = df[col].fillna(0.0)

    logger.info(f"=== Fusion terminée : {len(df):,} nœuds × {df.shape[1]} colonnes ===")
    return df


def add_display_metadata(df):
    df = df.copy()
    color_map = {"normal":"#3A86FF", "suspect":"#FF9F1C", "critique":"#E63946"}
    df["display_color"] = df["risk_level"].map(color_map).fillna("#3A86FF")

    if "total_tx_count" in df.columns:
        df["display_size"] = np.clip(
            1.0 + np.log1p(df["total_tx_count"]) * 0.3, 0.5, 5.0
        )
    else:
        df["display_size"] = 1.0

    if "account_type" in df.columns:
        df["display_shape"] = df["account_type"].map(
            {"merchant":"cube","client":"sphere"}
        ).fillna("sphere")
    else:
        df["display_shape"] = "sphere"

    return df


def save_final(df, path=FINAL_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_parquet(path, index=False)
    logger.info(f"final_nodes.parquet → {path}")


def run_merge(df_features, df_3d, df_clusters, df_anomalies):
    df = merge_all_results(df_features, df_3d, df_clusters, df_anomalies)
    df = add_display_metadata(df)
    save_final(df)
    return df