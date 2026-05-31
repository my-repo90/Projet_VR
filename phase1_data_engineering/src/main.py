"""
main.py — Phase 1 Data Engineering
Dataset limité à 300k transactions.
"""

import os, sys, logging, argparse, time
sys.path.insert(0, os.path.dirname(__file__))

from load_data       import load_paysim, get_basic_stats
from clean_data      import clean_data, save_cleaned
from build_graph     import build_nodes, build_edges, build_networkx_graph, save_nodes_edges
from compute_features import compute_all_features, save_features
from export_data     import export_all


def setup_logging(verbose=False):
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(H:%M:%S) | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    )


def run_pipeline(data_path=None, max_rows=300_000,
                 filter_types=True, verbose=False):

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    )
    logger = logging.getLogger("main")
    start  = time.time()

    logger.info("=" * 55)
    logger.info("  PHASE 1 — DATA ENGINEERING (max 300k transactions)")
    logger.info("=" * 55)

    # 1. Chargement avec sampling 300k
    logger.info("\n[1/5] Chargement + sampling...")
    kwargs = {"path": data_path} if data_path else {}
    df_raw = load_paysim(max_rows=max_rows, **kwargs)
    logger.info(f"  {len(df_raw):,} transactions chargées")

    # 2. Nettoyage
    logger.info("\n[2/5] Nettoyage...")
    df_clean = clean_data(df_raw, filter_types=filter_types)
    save_cleaned(df_clean)
    logger.info(f"  {len(df_clean):,} transactions après nettoyage")

    # 3. Graphe
    logger.info("\n[3/5] Construction du graphe...")
    edges = build_edges(df_clean)
    nodes = build_nodes(df_clean)
    G     = build_networkx_graph(nodes, edges)
    save_nodes_edges(nodes, edges)
    logger.info(f"  {G.number_of_nodes():,} nœuds, {G.number_of_edges():,} arêtes")

    # 4. Features
    logger.info("\n[4/5] Calcul des features...")
    features = compute_all_features(df_clean, nodes)
    save_features(features)
    logger.info(f"  {features.shape[1]} features pour {features.shape[0]:,} nœuds")

    # 5. Export
    logger.info("\n[5/5] Export...")
    paths = export_all(nodes, edges, features)

    elapsed = time.time() - start
    logger.info("\n" + "=" * 55)
    logger.info(f"  PHASE 1 TERMINÉE en {elapsed:.1f}s")
    logger.info(f"  Nœuds    : {G.number_of_nodes():,}")
    logger.info(f"  Arêtes   : {G.number_of_edges():,}")
    logger.info(f"  Features : {features.shape[1]} colonnes")
    logger.info("=" * 55)

    return {"df_clean": df_clean, "nodes": nodes,
            "edges": edges, "graph": G,
            "features": features, "export_paths": paths}


def parse_args():
    p = argparse.ArgumentParser(description="Phase 1 — Data Engineering (300k)")
    p.add_argument("--data",     type=str, default=None)
    p.add_argument("--max-rows", type=int, default=300_000)
    p.add_argument("--no-filter",action="store_true")
    p.add_argument("--verbose", "-v", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        data_path    = args.data,
        max_rows     = args.max_rows,
        filter_types = not args.no_filter,
        verbose      = args.verbose,
    )