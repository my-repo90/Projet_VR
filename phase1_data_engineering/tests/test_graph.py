"""
tests/test_graph.py
Tests unitaires pour build_graph et compute_features.
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from build_graph import build_edges, build_nodes, build_networkx_graph
from compute_features import (
    compute_sender_features,
    compute_receiver_features,
    compute_balance_features,
    merge_features,
    compute_all_features,
)


@pytest.fixture
def clean_df():
    """DataFrame nettoyé simulé."""
    return pd.DataFrame({
        "step": [1, 2, 3, 4, 5],
        "type": ["TRANSFER", "CASH_OUT", "TRANSFER", "CASH_OUT", "TRANSFER"],
        "amount": [1000.0, 500.0, 2000.0, 300.0, 1500.0],
        "log_amount": [6.9, 6.2, 7.6, 5.7, 7.3],
        "sender": ["C001", "C002", "C001", "C003", "C004"],
        "receiver": ["M001", "M002", "M003", "M001", "C001"],
        "oldbalanceOrg": [1000.0, 500.0, 2000.0, 300.0, 1500.0],
        "newbalanceOrig": [0.0, 0.0, 0.0, 0.0, 0.0],
        "oldbalanceDest": [0.0, 0.0, 0.0, 0.0, 0.0],
        "newbalanceDest": [1000.0, 500.0, 2000.0, 300.0, 1500.0],
        "is_fraud": [1, 0, 1, 0, 0],
        "balance_diff_orig": [-1000.0, -500.0, -2000.0, -300.0, -1500.0],
        "balance_diff_dest": [1000.0, 500.0, 2000.0, 300.0, 1500.0],
        "orig_account_emptied": [1, 1, 1, 1, 1],
    })


# ─── Tests build_graph ───────────────────────────────────────────

def test_build_edges_columns(clean_df):
    edges = build_edges(clean_df)
    assert "source" in edges.columns
    assert "target" in edges.columns
    assert "amount" in edges.columns
    assert "is_fraud" in edges.columns
    assert "edge_id" in edges.columns


def test_build_edges_count(clean_df):
    edges = build_edges(clean_df)
    assert len(edges) == len(clean_df)


def test_build_nodes_unique(clean_df):
    nodes = build_nodes(clean_df)
    # Pas de doublons dans node_id
    assert nodes["node_id"].nunique() == len(nodes)


def test_build_nodes_fraud_flags(clean_df):
    nodes = build_nodes(clean_df)
    # C001 a envoyé des fraudes → is_fraud_sender = 1
    c001 = nodes[nodes["node_id"] == "C001"].iloc[0]
    assert c001["is_fraud_sender"] == 1


def test_build_nodes_account_type(clean_df):
    nodes = build_nodes(clean_df)
    merchants = nodes[nodes["account_type"] == "merchant"]
    clients = nodes[nodes["account_type"] == "client"]
    # M001, M002, M003 sont des marchands
    assert len(merchants) >= 3
    assert len(clients) >= 2


def test_build_networkx_graph(clean_df):
    nodes = build_nodes(clean_df)
    edges = build_edges(clean_df)
    G = build_networkx_graph(nodes, edges)

    assert G.number_of_nodes() == len(nodes)
    assert G.number_of_edges() == len(edges)
    # Graphe orienté
    assert G.is_directed()


def test_graph_has_node_attributes(clean_df):
    nodes = build_nodes(clean_df)
    edges = build_edges(clean_df)
    G = build_networkx_graph(nodes, edges)
    # Chaque nœud doit avoir l'attribut account_type
    for n, data in G.nodes(data=True):
        assert "account_type" in data


# ─── Tests compute_features ──────────────────────────────────────

def test_sender_features_columns(clean_df):
    feats = compute_sender_features(clean_df)
    assert "node_id" in feats.columns
    assert "tx_sent_count" in feats.columns
    assert "tx_sent_fraud_count" in feats.columns
    assert "tx_sent_unique_receivers" in feats.columns


def test_receiver_features_columns(clean_df):
    feats = compute_receiver_features(clean_df)
    assert "node_id" in feats.columns
    assert "tx_recv_count" in feats.columns
    assert "tx_recv_unique_senders" in feats.columns


def test_merge_features_no_nan(clean_df):
    nodes = build_nodes(clean_df)
    sender_feats = compute_sender_features(clean_df)
    receiver_feats = compute_receiver_features(clean_df)
    balance_feats = compute_balance_features(clean_df)
    features = merge_features(nodes, sender_feats, receiver_feats, balance_feats)

    # Pas de NaN dans les colonnes numériques
    numeric_cols = features.select_dtypes(include=[np.number]).columns
    assert features[numeric_cols].isnull().sum().sum() == 0


def test_compute_all_features_shape(clean_df):
    nodes = build_nodes(clean_df)
    features = compute_all_features(clean_df, nodes)

    # Autant de lignes que de nœuds
    assert len(features) == len(nodes)
    # Au moins 10 features
    assert features.shape[1] >= 10


def test_features_fraud_node_consistent(clean_df):
    nodes = build_nodes(clean_df)
    features = compute_all_features(clean_df, nodes)
    # C001 a des fraudes envoyées → tx_sent_fraud_count > 0
    c001 = features[features["node_id"] == "C001"]
    assert c001["tx_sent_fraud_count"].values[0] > 0
