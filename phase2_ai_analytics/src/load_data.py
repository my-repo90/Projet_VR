"""
load_data.py — Phase 2
Chargement depuis Phase 1 (auto-détection).
"""

import pandas as pd
import os, logging, shutil

logger   = logging.getLogger(__name__)
INPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "input")

PHASE1_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "phase1_data_engineering", "data", "processed"
)


def _resolve(local, phase1, label):
    if os.path.exists(local):
        logger.info(f"[{label}] local : {local}")
        return local
    if os.path.exists(phase1):
        logger.info(f"[{label}] copie depuis Phase 1...")
        os.makedirs(INPUT_DIR, exist_ok=True)
        shutil.copy2(phase1, local)
        return local
    raise FileNotFoundError(
        f"[{label}] introuvable.\n"
        f"  → {local}\n"
        f"  → {phase1}\n"
        "Lancez d'abord la Phase 1."
    )


def load_features(path=None):
    if path is None:
        path = _resolve(
            os.path.join(INPUT_DIR, "nodes_features.parquet"),
            os.path.join(PHASE1_DIR, "nodes_features.parquet"),
            "nodes_features"
        )
    df = pd.read_parquet(path)
    logger.info(f"Features : {df.shape[0]:,} nœuds × {df.shape[1]} colonnes")
    return df


def load_edges(path=None):
    if path is None:
        path = _resolve(
            os.path.join(INPUT_DIR, "edges.csv"),
            os.path.join(PHASE1_DIR, "edges.csv"),
            "edges"
        )
    df = pd.read_csv(path)
    logger.info(f"Arêtes : {len(df):,}")
    return df


def get_feature_columns(df):
    exclude = {
        "node_id", "account_type",
        "is_fraud_sender", "is_fraud_receiver", "is_fraud_node"
    }
    return [c for c in df.select_dtypes(include=["number"]).columns
            if c not in exclude]