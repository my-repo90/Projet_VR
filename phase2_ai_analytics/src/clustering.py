"""
clustering.py — Phase 2
KMeans optimisé RAM (MiniBatchKMeans pour gros datasets).
"""

import pandas as pd
import numpy as np
import joblib, os, logging

logger     = logging.getLogger(__name__)
MODEL_PATH  = os.path.join(os.path.dirname(__file__), "..", "models", "clustering_model.pkl")
CLUSTERS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "output", "clusters.parquet")


def run_minibatch_kmeans(X_scaled, node_ids, n_clusters=8):
    """
    MiniBatchKMeans : beaucoup plus rapide et moins gourmand en RAM
    que KMeans classique sur gros dataset.
    """
    from sklearn.cluster import MiniBatchKMeans

    logger.info(f"MiniBatchKMeans (k={n_clusters}) sur {X_scaled.shape[0]:,} nœuds")
    km = MiniBatchKMeans(
        n_clusters=n_clusters,
        random_state=42,
        batch_size=10_000,   # batch RAM-safe
        n_init=5,
        max_iter=100,
    )
    labels = km.fit_predict(X_scaled)

    df_clusters = pd.DataFrame({
        "node_id":      node_ids.values,
        "cluster_label": labels.astype(int),
        "cluster_prob":  np.ones(len(labels)),
    })
    logger.info(f"Clusters : {df_clusters['cluster_label'].nunique()}")
    return df_clusters, km


def enrich_cluster_stats(df_clusters, df_features):
    cols = ["node_id", "is_fraud_node", "total_amount",
            "tx_sent_count", "tx_recv_count"]
    cols = [c for c in cols if c in df_features.columns]
    merged = df_clusters.merge(df_features[cols], on="node_id", how="left")

    stats = merged.groupby("cluster_label").agg(
        cluster_size     =("node_id", "count"),
        fraud_node_count =("is_fraud_node", "sum"),
        fraud_node_rate  =("is_fraud_node", "mean"),
        avg_total_amount =("total_amount", "mean"),
        avg_tx_sent      =("tx_sent_count", "mean"),
        avg_tx_recv      =("tx_recv_count", "mean"),
    ).reset_index()

    return df_clusters.merge(stats, on="cluster_label", how="left")


def save_clustering_model(model):
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    logger.info(f"Modèle clustering sauvegardé : {MODEL_PATH}")


def save_clusters(df, path=CLUSTERS_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_parquet(path, index=False)
    logger.info(f"Clusters sauvegardés : {path}")


def run_clustering(X_scaled, node_ids, df_features, n_clusters=8):
    logger.info("=== Clustering ===")
    df_clusters, model = run_minibatch_kmeans(X_scaled, node_ids, n_clusters)
    df_clusters = enrich_cluster_stats(df_clusters, df_features)
    save_clustering_model(model)
    save_clusters(df_clusters)
    logger.info("=== Clustering terminé ===")
    return df_clusters