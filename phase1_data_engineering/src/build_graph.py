"""
build_graph.py
Construction du graphe de transactions.
"""

import pandas as pd
import numpy as np
import networkx as nx
import os
import logging

logger = logging.getLogger(__name__)

NODES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "nodes.csv")
EDGES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "edges.csv")


def build_edges(df: pd.DataFrame) -> pd.DataFrame:
    edges = df[[
        "sender", "receiver", "step", "type", "amount",
        "log_amount", "is_fraud", "balance_diff_orig",
        "balance_diff_dest", "orig_account_emptied"
    ]].copy()
    edges = edges.rename(columns={"sender": "source", "receiver": "target"})
    edges["edge_id"] = edges.index
    logger.info(f"Arêtes : {len(edges):,}")
    return edges


def build_nodes(df: pd.DataFrame) -> pd.DataFrame:
    senders   = df[["sender"]].rename(columns={"sender": "node_id"})
    receivers = df[["receiver"]].rename(columns={"receiver": "node_id"})
    all_nodes = pd.concat([senders, receivers]).drop_duplicates().reset_index(drop=True)

    fraud_senders   = set(df[df["is_fraud"] == 1]["sender"].unique())
    fraud_receivers = set(df[df["is_fraud"] == 1]["receiver"].unique())

    all_nodes["is_fraud_sender"]   = all_nodes["node_id"].isin(fraud_senders).astype(int)
    all_nodes["is_fraud_receiver"] = all_nodes["node_id"].isin(fraud_receivers).astype(int)
    all_nodes["is_fraud_node"]     = (
        (all_nodes["is_fraud_sender"] == 1) | (all_nodes["is_fraud_receiver"] == 1)
    ).astype(int)
    all_nodes["account_type"] = all_nodes["node_id"].apply(
        lambda x: "merchant" if str(x).startswith("M") else "client"
    )

    logger.info(f"Nœuds : {len(all_nodes):,} (frauduleux : {all_nodes['is_fraud_node'].sum():,})")
    return all_nodes


def build_networkx_graph(nodes: pd.DataFrame, edges: pd.DataFrame) -> nx.DiGraph:
    G = nx.DiGraph()
    for _, row in nodes.iterrows():
        G.add_node(row["node_id"], **row.to_dict())
    for _, row in edges.iterrows():
        G.add_edge(row["source"], row["target"],
                   **row.drop(["source", "target"]).to_dict())
    logger.info(f"Graphe : {G.number_of_nodes():,} nœuds, {G.number_of_edges():,} arêtes")
    return G


def save_nodes_edges(nodes, edges,
                     nodes_path=NODES_PATH, edges_path=EDGES_PATH):
    os.makedirs(os.path.dirname(nodes_path), exist_ok=True)
    nodes.to_csv(nodes_path, index=False)
    edges.to_csv(edges_path, index=False)
    logger.info(f"Nœuds → {nodes_path}")
    logger.info(f"Arêtes → {edges_path}")