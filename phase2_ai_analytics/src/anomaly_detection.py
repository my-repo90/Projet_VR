"""
anomaly_detection.py — Phase 2
Isolation Forest uniquement (LOF désactivé = trop lourd sur gros dataset).
Traitement par batch pour limiter la RAM.
"""

import pandas as pd
import numpy as np
import joblib, os, logging
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler

logger     = logging.getLogger(__name__)
MODEL_PATH  = os.path.join(os.path.dirname(__file__), "..", "models", "anomaly_model.pkl")
ANOMALY_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "output", "anomalies.parquet")

IF_PARAMS = {
    "n_estimators":  100,       # réduit de 200 → 100 pour RAM
    "contamination": 0.05,
    "max_features":  1.0,
    "max_samples":   "auto",
    "random_state":  42,
    "n_jobs":        -1,
}


def run_isolation_forest(X_scaled, node_ids):
    """
    Isolation Forest — fit sur un échantillon de 200k max,
    puis score_samples() par batch sur tout le dataset.
    """
    n = X_scaled.shape[0]
    logger.info(f"Isolation Forest sur {n:,} nœuds")

    # Fit sur échantillon si trop grand
    if n > 200_000:
        idx      = np.random.choice(n, 200_000, replace=False)
        X_fit    = X_scaled[idx]
        logger.info(f"  Fit sur échantillon : 200,000 nœuds")
    else:
        X_fit = X_scaled

    clf = IsolationForest(**IF_PARAMS)
    clf.fit(X_fit)

    # Score par batch (RAM safe)
    batch_size = 50_000
    labels = np.zeros(n, dtype=int)
    scores = np.zeros(n, dtype=float)

    for start in range(0, n, batch_size):
        end              = min(start + batch_size, n)
        batch            = X_scaled[start:end]
        labels[start:end] = clf.predict(batch)
        scores[start:end] = clf.score_samples(batch)
        logger.info(f"  Scoring batch {start:,}–{end:,}")

    df = pd.DataFrame({
        "node_id":      node_ids.values,
        "if_raw_score": scores.astype(float),
        "if_label":     labels.astype(int),
    })

    n_anom = int((labels == -1).sum())
    logger.info(f"Anomalies IF : {n_anom:,} ({n_anom/n*100:.2f}%)")
    return df, clf


def compute_anomaly_score(df_if):
    """Normalise le score IF en [0, 1]. 1 = très anormal."""
    scaler = MinMaxScaler()
    df_if  = df_if.copy()

    df_if["anomaly_score"] = scaler.fit_transform(-df_if[["if_raw_score"]])
    df_if["anomaly_label"] = (df_if["if_label"] == -1).astype(int)

    df_if["risk_level"] = pd.cut(
        df_if["anomaly_score"],
        bins=[0, 0.4, 0.7, 1.0],
        labels=["normal", "suspect", "critique"],
        include_lowest=True
    )

    logger.info(f"Distribution risk_level :\n{df_if['risk_level'].value_counts().to_string()}")
    return df_if


def enrich_with_fraud_labels(df_anomalies, df_features):
    cols = ["node_id", "is_fraud_node", "is_fraud_sender", "is_fraud_receiver"]
    cols = [c for c in cols if c in df_features.columns]
    df   = df_anomalies.merge(df_features[cols], on="node_id", how="left")

    if "is_fraud_node" in df.columns:
        tp = int(((df["anomaly_label"] == 1) & (df["is_fraud_node"] == 1)).sum())
        fp = int(((df["anomaly_label"] == 1) & (df["is_fraud_node"] == 0)).sum())
        fn = int(((df["anomaly_label"] == 0) & (df["is_fraud_node"] == 1)).sum())
        p  = tp / (tp + fp + 1e-9)
        r  = tp / (tp + fn + 1e-9)
        f1 = 2*p*r / (p+r+1e-9)
        logger.info(f"Évaluation → Précision={p:.3f} Rappel={r:.3f} F1={f1:.3f}")

    return df


def save_anomaly_model(model):
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    logger.info(f"Modèle anomalie : {MODEL_PATH}")


def save_anomalies(df, path=ANOMALY_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_parquet(path, index=False)
    logger.info(f"Anomalies : {path}")


def run_anomaly_detection(X_scaled, node_ids, df_features):
    logger.info("=== Détection d'anomalies (Isolation Forest) ===")
    df_if, model = run_isolation_forest(X_scaled, node_ids)
    df_anomalies = compute_anomaly_score(df_if)
    df_anomalies = enrich_with_fraud_labels(df_anomalies, df_features)
    save_anomaly_model(model)
    save_anomalies(df_anomalies)
    logger.info("=== Détection terminée ===")
    return df_anomalies