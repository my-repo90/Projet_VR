"""
load_data.py
Chargement des données brutes PaySim — limité à 300k transactions.
"""

import pandas as pd
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

RAW_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "paysim.csv")

EXPECTED_COLUMNS = [
    "step", "type", "amount", "nameOrig", "oldbalanceOrg",
    "newbalanceOrig", "nameDest", "oldbalanceDest", "newbalanceDest", "isFraud"
]

# ── Taille max du dataset ──────────────────────────────────────
MAX_ROWS = 300_000


def load_paysim(path: str = RAW_PATH,
                max_rows: int = MAX_ROWS,
                seed: int = 42) -> pd.DataFrame:
    """
    Charge paysim.csv et échantillonne à max_rows lignes.
    Stratégie : garde TOUTES les fraudes + échantillon aléatoire du reste.
    → Préserve le taux de fraude représentatif.
    """
    logger.info(f"Chargement depuis : {path}")

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Fichier introuvable : {path}\n"
            "Placez paysim.csv dans data/raw/"
        )

    df = pd.read_csv(path)

    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")

    logger.info(f"Dataset brut : {len(df):,} lignes")

    # ── Sampling intelligent ───────────────────────────────────
    if len(df) > max_rows:
        # 1. Garder toutes les fraudes (minoritaires)
        df_fraud  = df[df["isFraud"] == 1]
        df_normal = df[df["isFraud"] == 0]

        # 2. Compléter avec des normales jusqu'à max_rows
        n_normal_needed = max_rows - len(df_fraud)

        if n_normal_needed > len(df_normal):
            df_sample = df
        else:
            df_normal_sample = df_normal.sample(
                n=n_normal_needed, random_state=seed
            )
            df_sample = pd.concat([df_fraud, df_normal_sample])

        df_sample = df_sample.sample(frac=1, random_state=seed).reset_index(drop=True)
        logger.info(
            f"Sampling : {len(df):,} → {len(df_sample):,} lignes "
            f"({len(df_fraud):,} fraudes conservées)"
        )
        df = df_sample
    else:
        logger.info(f"Dataset sous {max_rows:,} lignes, pas de sampling nécessaire")

    logger.info(f"Dataset final : {len(df):,} lignes")
    logger.info(f"Fraudes : {df['isFraud'].sum():,} ({df['isFraud'].mean()*100:.2f}%)")
    logger.info(f"Types : {df['type'].value_counts().to_dict()}")

    return df


def get_basic_stats(df: pd.DataFrame) -> dict:
    return {
        "n_rows":           len(df),
        "n_columns":        len(df.columns),
        "transaction_types": df["type"].value_counts().to_dict(),
        "fraud_count":      int(df["isFraud"].sum()),
        "fraud_rate":       float(df["isFraud"].mean()),
        "amount_mean":      float(df["amount"].mean()),
        "amount_max":       float(df["amount"].max()),
        "unique_orig":      int(df["nameOrig"].nunique()),
        "unique_dest":      int(df["nameDest"].nunique()),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df = load_paysim()
    stats = get_basic_stats(df)
    for k, v in stats.items():
        print(f"  {k}: {v}")