"""
clean_data.py
Nettoyage et filtrage des transactions PaySim.
"""

import pandas as pd
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

PROCESSED_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "processed", "cleaned_transactions.csv"
)

TRANSFER_TYPES = ["TRANSFER", "CASH_OUT"]


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    logger.info(f"Doublons supprimés : {before - len(df)}")
    return df


def remove_negative_amounts(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df[df["amount"] > 0]
    logger.info(f"Montants <= 0 supprimés : {before - len(df)}")
    return df


def filter_transfer_types(df: pd.DataFrame, types: list = None) -> pd.DataFrame:
    if types is None:
        types = TRANSFER_TYPES
    before = len(df)
    df = df[df["type"].isin(types)].copy()
    logger.info(f"Filtrage types {types} : {before} → {len(df)} lignes")
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    missing = df.isnull().sum()
    if missing.any():
        df = df.dropna()
        logger.info("Lignes NaN supprimées")
    return df


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["balance_diff_orig"]    = df["newbalanceOrig"] - df["oldbalanceOrg"]
    df["balance_diff_dest"]    = df["newbalanceDest"] - df["oldbalanceDest"]
    df["orig_account_emptied"] = (
        (df["oldbalanceOrg"] > 0) & (df["newbalanceOrig"] == 0)
    ).astype(int)
    df["log_amount"] = np.log1p(df["amount"])
    return df


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={
        "nameOrig":       "sender",
        "nameDest":       "receiver",
        "isFraud":        "is_fraud",
        "isFlaggedFraud": "is_flagged_fraud",
    })


def clean_data(df: pd.DataFrame, filter_types: bool = True) -> pd.DataFrame:
    logger.info("=== Nettoyage ===")
    df = remove_duplicates(df)
    df = remove_negative_amounts(df)
    df = handle_missing_values(df)
    if filter_types:
        df = filter_transfer_types(df)
    df = rename_columns(df)
    df = add_derived_columns(df)
    df = df.reset_index(drop=True)
    logger.info(f"=== Nettoyage terminé : {len(df):,} transactions ===")
    return df


def save_cleaned(df: pd.DataFrame, path: str = PROCESSED_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Sauvegardé : {path}")