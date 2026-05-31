# Phase 1 — Data Engineering

## Rôle
Cette phase charge, nettoie et transforme les données de transactions financières (PaySim) en un graphe structuré avec features calculées, prêt pour la phase 2 (IA / Analytics).

## Pipeline
```
paysim.csv
   → load_data.py       : chargement brut
   → clean_data.py      : nettoyage et filtrage
   → build_graph.py     : construction du graphe (nœuds + arêtes)
   → compute_features.py: calcul des features par nœud
   → export_data.py     : export JSON + Parquet
```

## Installation
```bash
pip install -r requirements.txt
```
## Installation
```bash
 python -m pip install pandas 
```
## Installation
```bash
python -m pip install networkx 
```

## Utilisation
```bash
# Placer paysim.csv dans data/raw/
python src/main.py
```

## Sorties
- `data/processed/cleaned_transactions.csv`
- `data/processed/nodes.csv`
- `data/processed/edges.csv`
- `data/processed/nodes_features.parquet`
- `data/export/nodes.json`
- `data/export/edges.json`

## Dataset
PaySim : simulation de transactions mobiles financières.
Source : https://www.kaggle.com/ntnu-testimon/paysim1
