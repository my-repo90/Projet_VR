"""
tests/test_anomaly.py
Tests unitaires pour anomaly_detection et merge_results.
"""

import pytest
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from preprocess import select_feature_columns, preprocess
from anomaly_detection import (
    run_isolation_forest,
    compute_combined_score,
    enrich_with_fraud_labels,
)
from merge_results import merge_all_results, add_display_metadata


@pytest.fixture
def sample_features():
    np.random.seed(0)
    n = 80
    return pd.DataFrame({
        "node_id": [f"C{i:04d}" for i in range(n)],
        "account_type": np.random.choice(["client", "merchant"], n),
        "is_fraud_node": np.random.choice([0, 1], n, p=[0.9, 0.1]),
        "is_fraud_sender": np.zeros(n, dtype=int),
        "is_fraud_receiver": np.zeros(n, dtype=int),
        "tx_sent_count": np.random.randint(1, 100, n).astype(float),
        "tx_sent_total_amount": np.random.uniform(100, 100000, n),
        "tx_sent_mean_amount": np.random.uniform(100, 10000, n),
        "tx_sent_max_amount": np.random.uniform(1000, 50000, n),
        "tx_sent_std_amount": np.random.uniform(0, 5000, n),
        "tx_recv_count": np.random.randint(0, 50, n).astype(float),
        "tx_recv_total_amount": np.random.uniform(0, 50000, n),
        "total_tx_count": np.random.randint(1, 150, n).astype(float),
        "total_amount": np.random.uniform(100, 150000, n),
        "tx_sent_recv_ratio": np.random.uniform(0, 10, n),
        "balance_diff_mean": np.random.uniform(-10000, 0, n),
        "orig_emptied_count": np.random.randint(0, 10, n).astype(float),
        "tx_sent_step_range": np.random.randint(0, 100, n).astype(float),
        "tx_sent_unique_receivers": np.random.randint(1, 30, n).astype(float),
    })


@pytest.fixture
def X_scaled(sample_features):
    X, _, _ = preprocess(sample_features, fit=True)
    return X


# ─── Tests Isolation Forest ──────────────────────────────────────

def test_isolation_forest_shape(sample_features, X_scaled):
    df_if, model = run_isolation_forest(X_scaled, sample_features["node_id"])
    assert len(df_if) == len(sample_features)
    assert "if_label" in df_if.columns
    assert "if_raw_score" in df_if.columns


def test_isolation_forest_labels(sample_features, X_scaled):
    df_if, _ = run_isolation_forest(X_scaled, sample_features["node_id"])
    # Labels doivent être -1 ou 1 uniquement
    assert set(df_if["if_label"].unique()).issubset({-1, 1})


def test_isolation_forest_detects_something(sample_features, X_scaled):
    df_if, _ = run_isolation_forest(X_scaled, sample_features["node_id"])
    # Doit détecter au moins quelques anomalies
    assert (df_if["if_label"] == -1).sum() > 0


# ─── Tests combined score ─────────────────────────────────────────

def test_combined_score_range(sample_features, X_scaled):
    df_if, _ = run_isolation_forest(X_scaled, sample_features["node_id"])
    # Créer un df_lof simulé pour le test
    df_lof = pd.DataFrame({
        "node_id": sample_features["node_id"].values,
        "lof_score": np.random.uniform(1, 3, len(sample_features)),
        "lof_label": np.random.choice([-1, 1], len(sample_features)),
    })
    df_combined = compute_combined_score(df_if, df_lof)
    assert "anomaly_score" in df_combined.columns
    assert df_combined["anomaly_score"].between(0, 1).all()


def test_combined_risk_levels(sample_features, X_scaled):
    df_if, _ = run_isolation_forest(X_scaled, sample_features["node_id"])
    df_lof = pd.DataFrame({
        "node_id": sample_features["node_id"].values,
        "lof_score": np.random.uniform(1, 3, len(sample_features)),
        "lof_label": np.random.choice([-1, 1], len(sample_features)),
    })
    df_combined = compute_combined_score(df_if, df_lof)
    valid_levels = {"normal", "suspect", "critique"}
    assert set(df_combined["risk_level"].astype(str).unique()).issubset(valid_levels)


def test_enrich_with_fraud_labels(sample_features, X_scaled):
    df_if, _ = run_isolation_forest(X_scaled, sample_features["node_id"])
    df_lof = pd.DataFrame({
        "node_id": sample_features["node_id"].values,
        "lof_score": np.random.uniform(1, 3, len(sample_features)),
        "lof_label": np.random.choice([-1, 1], len(sample_features)),
    })
    df_combined = compute_combined_score(df_if, df_lof)
    df_enriched = enrich_with_fraud_labels(df_combined, sample_features)
    assert "is_fraud_node" in df_enriched.columns


# ─── Tests merge_results ─────────────────────────────────────────

@pytest.fixture
def mock_results(sample_features):
    n = len(sample_features)
    df_3d = pd.DataFrame({
        "node_id": sample_features["node_id"].values,
        "x": np.random.uniform(-25, 25, n),
        "y": np.random.uniform(-25, 25, n),
        "z": np.random.uniform(-25, 25, n),
    })
    df_clusters = pd.DataFrame({
        "node_id": sample_features["node_id"].values,
        "cluster_label": np.random.randint(-1, 5, n),
        "cluster_prob": np.random.uniform(0, 1, n),
        "cluster_size": np.random.randint(5, 50, n),
        "fraud_node_rate": np.random.uniform(0, 0.2, n),
        "avg_total_amount": np.random.uniform(1000, 50000, n),
    })
    df_anomalies = pd.DataFrame({
        "node_id": sample_features["node_id"].values,
        "anomaly_score": np.random.uniform(0, 1, n),
        "anomaly_label": np.random.choice([0, 1], n),
        "risk_level": np.random.choice(["normal", "suspect", "critique"], n),
        "if_raw_score": np.random.uniform(-0.5, 0.5, n),
        "if_label": np.random.choice([-1, 1], n),
        "lof_score": np.random.uniform(1, 3, n),
        "lof_label": np.random.choice([-1, 1], n),
        "if_score_norm": np.random.uniform(0, 1, n),
        "lof_score_norm": np.random.uniform(0, 1, n),
    })
    return df_3d, df_clusters, df_anomalies


def test_merge_all_shape(sample_features, mock_results):
    df_3d, df_clusters, df_anomalies = mock_results
    df_final = merge_all_results(sample_features, df_3d, df_clusters, df_anomalies)
    assert len(df_final) == len(sample_features)


def test_merge_has_3d(sample_features, mock_results):
    df_3d, df_clusters, df_anomalies = mock_results
    df_final = merge_all_results(sample_features, df_3d, df_clusters, df_anomalies)
    for col in ["x", "y", "z"]:
        assert col in df_final.columns


def test_merge_no_nan_numeric(sample_features, mock_results):
    df_3d, df_clusters, df_anomalies = mock_results
    df_final = merge_all_results(sample_features, df_3d, df_clusters, df_anomalies)
    numeric = df_final.select_dtypes(include=[np.number])
    assert numeric.isnull().sum().sum() == 0


def test_display_metadata(sample_features, mock_results):
    df_3d, df_clusters, df_anomalies = mock_results
    df_final = merge_all_results(sample_features, df_3d, df_clusters, df_anomalies)
    df_display = add_display_metadata(df_final)
    assert "display_color" in df_display.columns
    assert "display_size" in df_display.columns
    assert "display_shape" in df_display.columns
    # Couleurs valides
    valid_colors = {"#3A86FF", "#FF9F1C", "#E63946"}
    assert set(df_display["display_color"].unique()).issubset(valid_colors)
