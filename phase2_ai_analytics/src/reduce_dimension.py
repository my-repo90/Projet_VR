"""
reduce_dimension.py — Phase 2
Stratégie optimisée RAM/CPU pour gros datasets.

PIPELINE :
  1. PCA 20 dims         → tout le dataset, rapide
  2. UMAP fit 300k       → échantillon représentatif
  3. UMAP transform()    → par batch de 50k pour les restants
  → 100% des nœuds ont des coordonnées 3D
  → RAM pic ~4GB max
"""

import pandas as pd
import numpy as np
import os, logging

logger       = logging.getLogger(__name__)
NODES_3D_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "output", "nodes_3d.parquet"
)

UMAP_PARAMS      = {
    "n_components": 3,
    "n_neighbors":  15,
    "min_dist":     0.1,
    "metric":       "euclidean",
    "random_state": None,   # None = multi-core
    "n_jobs":       -1,
}
UMAP_SAMPLE_SIZE = 300_000
BATCH_SIZE       = 50_000


# ── Étape 1 : PCA ────────────────────────────────────────────────

def pca_reduce(X_scaled, n_components=20):
    from sklearn.decomposition import PCA
    n = min(n_components, X_scaled.shape[1])
    logger.info(f"Step 1: PCA ({n} dims)")
    pca     = PCA(n_components=n, random_state=42)
    X_pca   = pca.fit_transform(X_scaled)
    logger.info(f"PCA variance: {pca.explained_variance_ratio_.sum():.3f}")
    return X_pca


# ── Étape 2 : UMAP fit sur échantillon ───────────────────────────

def umap_fit_sample(X_pca, sample_size=UMAP_SAMPLE_SIZE):
    import umap

    n = X_pca.shape[0]
    if n > sample_size:
        logger.warning(f"Sampling UMAP: {n:,} → {sample_size:,}")
        idx     = np.random.choice(n, sample_size, replace=False)
        X_sample = X_pca[idx]
    else:
        idx      = np.arange(n)
        X_sample = X_pca

    logger.info(f"UMAP 3D sur {len(X_sample):,} nœuds")
    reducer = umap.UMAP(**UMAP_PARAMS)
    reducer.fit(X_sample)
    logger.info("UMAP fit terminé")
    return reducer, idx


# ── Étape 3 : transform() par batch sur les restants ─────────────

def umap_transform_all(X_pca, reducer, fit_idx, node_ids,
                       batch_size=BATCH_SIZE):
    """
    Applique reducer.transform() sur tout le dataset par batch.
    Les nœuds déjà dans fit_idx utilisent les coords directes.
    """
    n          = X_pca.shape[0]
    embeddings = np.zeros((n, 3), dtype=np.float32)

    # Nœuds déjà dans le sample → transform direct
    logger.info(f"Transform batch : {n:,} nœuds par batch de {batch_size:,}")
    for start in range(0, n, batch_size):
        end        = min(start + batch_size, n)
        batch      = X_pca[start:end]
        emb        = reducer.transform(batch)
        embeddings[start:end] = emb
        logger.info(f"  Batch {start:,}–{end:,} / {n:,}")

    # Normalisation Unity [-25, 25]
    for i in range(3):
        col = embeddings[:, i]
        embeddings[:, i] = 50.0 * (col - col.min()) / (col.max() - col.min() + 1e-9) - 25.0

    df_3d = pd.DataFrame({
        "node_id": node_ids.values,
        "x": embeddings[:, 0],
        "y": embeddings[:, 1],
        "z": embeddings[:, 2],
    })
    logger.info(f"Coordonnées 3D calculées pour {len(df_3d):,} nœuds")
    return df_3d


# ── Fallback PCA complet ─────────────────────────────────────────

def reduce_pca_fallback(X_scaled, node_ids):
    from sklearn.decomposition import PCA
    logger.warning("Fallback PCA utilisé (UMAP indisponible)")
    pca = PCA(n_components=3, random_state=42)
    emb = pca.fit_transform(X_scaled)
    logger.info(f"PCA variance expliquée : {pca.explained_variance_ratio_.sum():.3f}")

    df_3d = pd.DataFrame({
        "node_id": node_ids.values,
        "x": emb[:, 0].astype(float),
        "y": emb[:, 1].astype(float),
        "z": emb[:, 2].astype(float),
    })

    # Normalisation
    for axis in ["x", "y", "z"]:
        v = df_3d[axis]
        df_3d[axis] = 50.0 * (v - v.min()) / (v.max() - v.min() + 1e-9) - 25.0

    return df_3d


# ── Sauvegarde ───────────────────────────────────────────────────

def save_nodes_3d(df_3d, path=NODES_3D_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df_3d.to_parquet(path, index=False)
    logger.info(f"nodes_3d sauvegardé : {path}")


# ── Pipeline principal ───────────────────────────────────────────

def run_reduction(X_scaled, node_ids, use_umap=True):
    try:
        # Étape 1 : PCA
        X_pca = pca_reduce(X_scaled, n_components=20)

        if use_umap:
            # Étape 2 : UMAP fit sur échantillon
            logger.info("Step 2: UMAP")
            reducer, fit_idx = umap_fit_sample(X_pca)

            # Étape 3 : transform tout le dataset par batch
            df_3d = umap_transform_all(X_pca, reducer, fit_idx, node_ids)
        else:
            df_3d = reduce_pca_fallback(X_scaled, node_ids)

    except Exception as e:
        logger.warning(f"UMAP échoué ({e}) → fallback PCA")
        df_3d = reduce_pca_fallback(X_scaled, node_ids)

    save_nodes_3d(df_3d)
    return df_3d