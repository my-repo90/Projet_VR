"""
compute_features.py
Calcul des features par nœud.
"""

import pandas as pd
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

FEATURES_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "processed", "nodes_features.parquet"
)


def compute_sender_features(df):
    grp = df.groupby("sender")
    return pd.DataFrame({
        "tx_sent_count":           grp["amount"].count(),
        "tx_sent_total_amount":    grp["amount"].sum(),
        "tx_sent_mean_amount":     grp["amount"].mean(),
        "tx_sent_max_amount":      grp["amount"].max(),
        "tx_sent_std_amount":      grp["amount"].std().fillna(0),
        "tx_sent_fraud_count":     grp["is_fraud"].sum(),
        "tx_sent_fraud_rate":      grp["is_fraud"].mean(),
        "tx_sent_step_min":        grp["step"].min(),
        "tx_sent_step_max":        grp["step"].max(),
        "tx_sent_step_range":      grp["step"].max() - grp["step"].min(),
        "tx_sent_unique_receivers":grp["receiver"].nunique(),
        "orig_emptied_count":      grp["orig_account_emptied"].sum(),
    }).reset_index().rename(columns={"sender": "node_id"})


def compute_receiver_features(df):
    grp = df.groupby("receiver")
    return pd.DataFrame({
        "tx_recv_count":          grp["amount"].count(),
        "tx_recv_total_amount":   grp["amount"].sum(),
        "tx_recv_mean_amount":    grp["amount"].mean(),
        "tx_recv_max_amount":     grp["amount"].max(),
        "tx_recv_std_amount":     grp["amount"].std().fillna(0),
        "tx_recv_fraud_count":    grp["is_fraud"].sum(),
        "tx_recv_fraud_rate":     grp["is_fraud"].mean(),
        "tx_recv_unique_senders": grp["sender"].nunique(),
    }).reset_index().rename(columns={"receiver": "node_id"})


def compute_balance_features(df):
    grp = df.groupby("sender")
    return pd.DataFrame({
        "balance_diff_mean": grp["balance_diff_orig"].mean(),
        "balance_diff_min":  grp["balance_diff_orig"].min(),
        "old_balance_mean":  grp["oldbalanceOrg"].mean(),
    }).reset_index().rename(columns={"sender": "node_id"})


def merge_features(nodes, sender_feats, receiver_feats, balance_feats):
    df = nodes.copy()
    df = df.merge(sender_feats,   on="node_id", how="left")
    df = df.merge(receiver_feats, on="node_id", how="left")
    df = df.merge(balance_feats,  on="node_id", how="left")

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    df["tx_sent_recv_ratio"] = df["tx_sent_count"] / (df["tx_recv_count"] + 1)
    df["total_tx_count"]     = df["tx_sent_count"] + df["tx_recv_count"]
    df["total_amount"]       = df["tx_sent_total_amount"] + df["tx_recv_total_amount"]

    logger.info(f"Features : {df.shape[0]:,} nœuds × {df.shape[1]} colonnes")
    return df


def save_features(df, path=FEATURES_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_parquet(path, index=False)
    logger.info(f"Features sauvegardées : {path}")


def compute_all_features(df_clean, nodes):
    logger.info("=== Calcul des features ===")
    sf = compute_sender_features(df_clean)
    rf = compute_receiver_features(df_clean)
    bf = compute_balance_features(df_clean)
    features = merge_features(nodes, sf, rf, bf)
    logger.info("=== Features terminées ===")
    return features