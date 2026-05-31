"""
tests/test_clustering.py
Tests unitaires pour preprocess, reduce_dimension et clustering.
"""

import pytest
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from preprocess import (
    select_feature_columns, clean_infinite_values,
    fit_scaler, preprocess
)
from reduce_dimension import reduce_pca_fallback
from clustering import (
    run_kmeans_fallback, enrich_cluster_stats
)


@pytest.fixture
def sample_features():
    """DataFrame de features simulées (100 nœuds)."""
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        "node_id": [f"C{i:04d}" for i in range(n)],
        "account_type": np.random.choice(["client", "merchant"], n),
        "is_fraud_node": np.random.choice([0, 1], n, p=[0.95, 0.05]),
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


# ─── Tests preprocess ────────────────────────────────────────────

def test_select_feature_columns(sample_features):
    cols = select_feature_columns(sample_features)
    # Les colonnes exclues ne doivent pas être présentes
    assert "node_id" not in cols
    assert "account_type" not in cols
    assert "is_fraud_node" not in cols
    # Des features numériques doivent être présentes
    assert len(cols) > 5


def test_clean_infinite_values():
    X = np.array([[1.0, np.inf, 3.0],
                  [4.0, 5.0, -np.inf],
                  [7.0, np.nan, 9.0]])
    X_clean = clean_infinite_values(X)
    assert np.isfinite(X_clean).all()
    assert X_clean.shape == X.shape


def test_fit_scaler_output(sample_features, tmp_path):
    cols = select_feature_columns(sample_features)
    X = sample_features[cols].values.astype(float)
    scaler_path = str(tmp_path / "scaler.pkl")
    scaler = fit_scaler(X, save_path=scaler_path)
    X_scaled = scaler.transform(X)
    assert X_scaled.shape == X.shape
    assert os.path.exists(scaler_path)


def test_preprocess_full(sample_features, tmp_path):
    import sys
    # Patch scaler path
    os.environ["TEST_SCALER_PATH"] = str(tmp_path / "scaler.pkl")
    X_scaled, cols, scaler = preprocess(sample_features, fit=True)
    assert X_scaled.shape[0] == len(sample_features)
    assert X_scaled.shape[1] == len(cols)
    assert np.isfinite(X_scaled).all()


def test_preprocess_no_nan(sample_features):
    X_scaled, cols, _ = preprocess(sample_features, fit=True)
    assert not np.isnan(X_scaled).any()


# ─── Tests reduce_dimension ──────────────────────────────────────

def test_pca_fallback_shape(sample_features):
    cols = select_feature_columns(sample_features)
    X = sample_features[cols].values.astype(float)
    df_3d = reduce_pca_fallback(X, sample_features["node_id"])
    assert len(df_3d) == len(sample_features)
    assert "x" in df_3d.columns
    assert "y" in df_3d.columns
    assert "z" in df_3d.columns


def test_pca_fallback_node_ids(sample_features):
    cols = select_feature_columns(sample_features)
    X = sample_features[cols].values.astype(float)
    df_3d = reduce_pca_fallback(X, sample_features["node_id"])
    assert set(df_3d["node_id"]) == set(sample_features["node_id"])


def test_pca_no_nan(sample_features):
    cols = select_feature_columns(sample_features)
    X = sample_features[cols].values.astype(float)
    df_3d = reduce_pca_fallback(X, sample_features["node_id"])
    assert df_3d[["x", "y", "z"]].isnull().sum().sum() == 0


# ─── Tests clustering ────────────────────────────────────────────

def test_kmeans_fallback_shape(sample_features):
    cols = select_feature_columns(sample_features)
    X = sample_features[cols].values.astype(float)
    df_clusters, model = run_kmeans_fallback(X, sample_features["node_id"], n_clusters=5)
    assert len(df_clusters) == len(sample_features)
    assert "cluster_label" in df_clusters.columns
    assert "cluster_prob" in df_clusters.columns


def test_kmeans_n_clusters(sample_features):
    cols = select_feature_columns(sample_features)
    X = sample_features[cols].values.astype(float)
    df_clusters, _ = run_kmeans_fallback(X, sample_features["node_id"], n_clusters=4)
    assert df_clusters["cluster_label"].nunique() == 4


def test_enrich_cluster_stats(sample_features):
    cols = select_feature_columns(sample_features)
    X = sample_features[cols].values.astype(float)
    df_clusters, _ = run_kmeans_fallback(X, sample_features["node_id"], n_clusters=5)
    df_enriched = enrich_cluster_stats(df_clusters, sample_features)
    assert "cluster_size" in df_enriched.columns
    assert "fraud_node_rate" in df_enriched.columns
