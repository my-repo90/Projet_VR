"""
preprocess.py — Phase 2
Normalisation RobustScaler.
"""

import pandas as pd
import numpy as np
import joblib, os, logging
from sklearn.preprocessing import RobustScaler

logger      = logging.getLogger(__name__)
SCALER_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "scaler.pkl")


def select_feature_columns(df):
    exclude = {
        "node_id", "account_type",
        "is_fraud_sender", "is_fraud_receiver", "is_fraud_node",
        "tx_sent_fraud_count", "tx_sent_fraud_rate",
        "tx_recv_fraud_count", "tx_recv_fraud_rate",
    }
    return [c for c in df.select_dtypes(include=["number"]).columns
            if c not in exclude]


def clean_infinite_values(X):
    X = X.copy().astype(float)
    X[~np.isfinite(X)] = np.nan
    medians = np.nanmedian(X, axis=0)
    mask    = np.isnan(X)
    X[mask] = np.take(medians, np.where(mask)[1])
    return X


def preprocess(df, feature_cols=None, fit=True):
    logger.info("=== Prétraitement ===")

    if feature_cols is None:
        feature_cols = select_feature_columns(df)

    X = df[feature_cols].values.astype(float)
    logger.info(f"Matrice features : {X.shape}")

    X = clean_infinite_values(X)
    logger.info("Valeurs infinies/NaN nettoyées")

    if fit:
        scaler = RobustScaler()
        scaler.fit(X)
        os.makedirs(os.path.dirname(SCALER_PATH), exist_ok=True)
        joblib.dump(scaler, SCALER_PATH)
        logger.info(f"Scaler sauvegardé : {SCALER_PATH}")
    else:
        scaler = joblib.load(SCALER_PATH)

    X_scaled = scaler.transform(X)
    logger.info("Normalisation RobustScaler appliquée")
    return X_scaled, feature_cols, scaler