# Phase 3 - Backend API

API FastAPI permettant d'exposer les données d'analyse aux clients Unity VR et desktop.

## Installation

Depuis la racine du projet :

```powershell
python -m pip install -r requirements.txt
cd phase3_backend_api
```

## Démarrage

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
```

Documentation interactive : [http://127.0.0.1:8010/docs](http://127.0.0.1:8010/docs)

Vérification de l'API : [http://127.0.0.1:8010/health](http://127.0.0.1:8010/health)

## Données

Les fichiers JSON sont chargés depuis `data/`. Pour importer automatiquement les exports disponibles depuis les phases précédentes :

```text
POST /api/sync/from-phase2
```

Endpoints utiles :

```text
GET  /api/nodes
GET  /api/edges
GET  /api/clusters
GET  /api/anomalies
GET  /api/sync/status
WS   /api/sync/ws
```

