# Phase 2 — IA / Analytics / Clustering / Détection d'anomalies

## Rôle
Cette phase reçoit les features de la Phase 1 et produit :
- Une projection 3D des nœuds (UMAP → coordonnées x, y, z pour Unity)
- Des clusters comportementaux (HDBSCAN)
- Un score d'anomalie par nœud (Isolation Forest)
- Un fichier `final_nodes.parquet` prêt pour le backend (Phase 3)

## Chaînage avec Phase 1
```
phase1_data_engineering/data/processed/nodes_features.parquet  ──→  data/input/
phase1_data_engineering/data/processed/edges.csv               ──→  data/input/
```

## Pipeline
```
nodes_features.parquet + edges.csv
   → load_data.py          : chargement depuis Phase 1
   → preprocess.py         : normalisation, sélection features
   → reduce_dimension.py   : UMAP 3D
   → clustering.py         : HDBSCAN clustering
   → anomaly_detection.py  : Isolation Forest + score
   → merge_results.py      : fusion de tous les résultats
   → export_results.py     : export Parquet + JSON
```

## Installation
```bash
pip install -r requirements.txt
```

## Utilisation
```bash
# Option 1 : lancer après Phase 1 (données déjà générées)
python src/main.py

# Option 2 : spécifier les chemins manuellement
python src/main.py --features /path/to/nodes_features.parquet --edges /path/to/edges.csv

# Option 3 : lancer les deux phases d'un coup depuis la racine
python src/main.py --run-phase1
```

## Sorties
- `data/output/nodes_3d.parquet`       → coordonnées 3D UMAP
- `data/output/clusters.parquet`       → labels de clusters
- `data/output/anomalies.parquet`      → scores d'anomalie
- `data/output/final_nodes.parquet`    → fichier final fusionné pour Phase 3
- `data/export/nodes_3d.json`          → export JSON pour Unity / backend
- `data/export/anomalies.json`         → export JSON anomalies
- `models/scaler.pkl`                  → scaler sauvegardé
- `models/clustering_model.pkl`        → modèle HDBSCAN sauvegardé
- `models/anomaly_model.pkl`           → modèle Isolation Forest sauvegardé
