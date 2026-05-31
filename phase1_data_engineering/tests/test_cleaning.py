"""
tests/test_cleaning.py
Tests unitaires pour le module clean_data.
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from clean_data import (
    remove_duplicates,
    remove_negative_amounts,
    filter_transfer_types,
    handle_missing_values,
    add_derived_columns,
    rename_columns,
    clean_data,
)


@pytest.fixture
def sample_df():
    """DataFrame de test simulant PaySim."""
    return pd.DataFrame({
        "step": [1, 1, 2, 3, 4, 5],
        "type": ["TRANSFER", "TRANSFER", "CASH_OUT", "PAYMENT", "DEBIT", "TRANSFER"],
        "amount": [1000.0, 1000.0, 500.0, 200.0, -50.0, 3000.0],
        "nameOrig": ["C001", "C001", "C002", "C003", "C004", "C005"],
        "oldbalanceOrg": [1000.0, 1000.0, 500.0, 200.0, 100.0, 3000.0],
        "newbalanceOrig": [0.0, 0.0, 0.0, 0.0, 150.0, 0.0],
        "nameDest": ["M001", "M001", "M002", "M003", "M004", "M005"],
        "oldbalanceDest": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "newbalanceDest": [1000.0, 1000.0, 500.0, 200.0, 0.0, 3000.0],
        "isFraud": [1, 1, 0, 0, 0, 1],
    })


def test_remove_duplicates(sample_df):
    df = remove_duplicates(sample_df)
    # Les 2 premières lignes sont dupliquées
    assert len(df) == len(sample_df) - 1


def test_remove_negative_amounts(sample_df):
    df = remove_negative_amounts(sample_df)
    assert (df["amount"] > 0).all()
    # La ligne avec -50 doit être supprimée
    assert len(df) == len(sample_df) - 1


def test_filter_transfer_types(sample_df):
    df = filter_transfer_types(sample_df, types=["TRANSFER", "CASH_OUT"])
    assert set(df["type"].unique()).issubset({"TRANSFER", "CASH_OUT"})
    assert len(df) < len(sample_df)


def test_handle_missing_values():
    df = pd.DataFrame({
        "step": [1, 2, None],
        "type": ["TRANSFER", None, "CASH_OUT"],
        "amount": [100.0, 200.0, 300.0],
        "nameOrig": ["C001", "C002", "C003"],
        "oldbalanceOrg": [100.0, 200.0, 300.0],
        "newbalanceOrig": [0.0, 0.0, 0.0],
        "nameDest": ["M001", "M002", "M003"],
        "oldbalanceDest": [0.0, 0.0, 0.0],
        "newbalanceDest": [100.0, 200.0, 300.0],
        "isFraud": [0, 0, 1],
    })
    result = handle_missing_values(df)
    assert result.isnull().sum().sum() == 0


def test_add_derived_columns(sample_df):
    df = rename_columns(sample_df.copy())
    df = add_derived_columns(df)
    assert "balance_diff_orig" in df.columns
    assert "balance_diff_dest" in df.columns
    assert "orig_account_emptied" in df.columns
    assert "log_amount" in df.columns
    # log_amount doit être >= 0
    assert (df["log_amount"] >= 0).all()


def test_rename_columns(sample_df):
    df = rename_columns(sample_df)
    assert "sender" in df.columns
    assert "receiver" in df.columns
    assert "is_fraud" in df.columns
    assert "nameOrig" not in df.columns
    assert "nameDest" not in df.columns


def test_clean_data_pipeline(sample_df):
    df = clean_data(sample_df, filter_types=True)
    # Doit retourner uniquement TRANSFER et CASH_OUT
    assert set(df["type"].unique()).issubset({"TRANSFER", "CASH_OUT"})
    # Pas de doublons
    assert df.duplicated().sum() == 0
    # Pas de montants négatifs
    assert (df["amount"] > 0).all()
    # Colonnes dérivées présentes
    assert "log_amount" in df.columns
    assert "orig_account_emptied" in df.columns


def test_clean_data_no_filter(sample_df):
    df = clean_data(sample_df, filter_types=False)
    # Doit garder tous les types (sauf négatifs et doublons)
    types = set(df["type"].unique())
    assert len(types) >= 2


def test_fraud_preserved(sample_df):
    """Vérifie que les transactions frauduleuses sont préservées après nettoyage."""
    df = clean_data(sample_df, filter_types=True)
    assert df["is_fraud"].sum() > 0
