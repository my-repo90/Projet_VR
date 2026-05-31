"""
main.py — Phase 2 IA / Analytics
Optimisé RAM/CPU pour datasets jusqu'à 3M+ nœuds.
"""

import os, sys, logging, argparse, time
sys.path.insert(0, os.path.dirname(__file__))

from load_data         import load_features, load_edges
from preprocess        import preprocess
from reduce_dimension  import run_reduction
from clustering        import run_clustering
from anomaly_detection import run_anomaly_detection
from merge_results     import run_merge
from export_results    import export_all_results


def run_pipeline(features_path=None, edges_path=None,
                 use_umap=True, n_clusters=8,
                 run_phase1=False, verbose=False):

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    )
    logger = logging.getLogger("main")
    start  = time.time()

    logger.info("=" * 60)
    logger.info("  PHASE 2 — IA / ANALYTICS / CLUSTERING / ANOMALIES")
    logger.info("=" * 60)

    # 0. Phase 1 optionnelle
    if run_phase1:
        logger.info("\n[0/7] Lancement Phase 1...")
        import subprocess
        phase1 = os.path.join(os.path.dirname(__file__), "..", "..",
                              "phase1_data_engineering", "src", "main.py")
        subprocess.run([sys.executable, phase1], check=True)

    # 1. Chargement
    logger.info("\n[1/7] Chargement des données (Phase 1)...")
    kf = {"path": features_path} if features_path else {}
    ke = {"path": edges_path}    if edges_path    else {}
    df_features = load_features(**kf)
    df_edges    = load_edges(**ke)
    logger.info(f"  {len(df_features):,} nœuds, {len(df_edges):,} arêtes")

    # 2. Prétraitement
    logger.info("\n[2/7] Prétraitement des features...")
    X_scaled, feature_cols, scaler = preprocess(df_features, fit=True)
    logger.info(f"  Matrice : {X_scaled.shape}")

    # 3. Réduction dimensionnelle
    logger.info(f"\n[3/7] Réduction dimensionnelle ({'UMAP 3D + transform batch' if use_umap else 'PCA 3D'})...")
    df_3d = run_reduction(X_scaled, df_features["node_id"], use_umap=use_umap)
    logger.info(f"  Coordonnées 3D calculées pour {len(df_3d):,} nœuds")

    # 4. Clustering
    logger.info(f"\n[4/7] Clustering (MiniBatchKMeans k={n_clusters})...")
    df_clusters = run_clustering(X_scaled, df_features["node_id"],
                                  df_features, n_clusters=n_clusters)
    logger.info(f"  {df_clusters['cluster_label'].nunique()} clusters")

    # 5. Détection d'anomalies
    logger.info("\n[5/7] Détection d'anomalies (Isolation Forest)...")
    df_anomalies = run_anomaly_detection(X_scaled, df_features["node_id"], df_features)
    n_anom = int(df_anomalies["anomaly_label"].sum())
    logger.info(f"  {n_anom:,} anomalies détectées")

    # 6. Fusion
    logger.info("\n[6/7] Fusion des résultats...")
    df_final = run_merge(df_features, df_3d, df_clusters, df_anomalies)
    logger.info(f"  {df_final.shape[0]:,} nœuds × {df_final.shape[1]} colonnes")

    # 7. Export
    logger.info("\n[7/7] Export JSON + Parquet...")
    export_paths = export_all_results(df_final)

    elapsed = time.time() - start
    logger.info("\n" + "=" * 60)
    logger.info("  PHASE 2 TERMINÉE")
    logger.info("=" * 60)
    logger.info(f"  Durée      : {elapsed:.1f}s")
    logger.info(f"  Nœuds      : {len(df_final):,}")
    logger.info(f"  Clusters   : {df_clusters['cluster_label'].nunique()}")
    logger.info(f"  Anomalies  : {n_anom:,}")
    logger.info("\n  Fichiers générés :")
    for v in export_paths.values():
        if v: logger.info(f"    {v}")
    logger.info("\n  → Prêt pour la Phase 3 (Backend API)")

    return {"df_features": df_features, "df_3d": df_3d,
            "df_clusters": df_clusters, "df_anomalies": df_anomalies,
            "df_final": df_final, "export_paths": export_paths}


def parse_args():
    p = argparse.ArgumentParser(description="Phase 2 — IA / Analytics (optimisé RAM)")
    p.add_argument("--features",    type=str, default=None)
    p.add_argument("--edges",       type=str, default=None)
    p.add_argument("--run-phase1",  action="store_true")
    p.add_argument("--no-umap",     action="store_true")
    p.add_argument("--n-clusters",  type=int, default=8)
    p.add_argument("--verbose","-v",action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        features_path = args.features,
        edges_path    = args.edges,
        use_umap      = not args.no_umap,
        n_clusters    = args.n_clusters,
        run_phase1    = args.run_phase1,
        verbose       = args.verbose,
    )