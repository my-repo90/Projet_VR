# DATA-DIVE v2.0 — Streamlit App

Dashboard cyberpunk de visualisation de graphes réseau avec intégration Unity VR.

## Installation

```bash
pip install -r requirements.txt
```

## Lancement

```bash
streamlit run app.py
```

L'application s'ouvre sur `http://localhost:8501`

## Intégration Unity WebGL

1. Dans Unity, exportez votre projet en **WebGL** (File → Build Settings → WebGL → Build)
2. Hébergez le build sur un serveur (Netlify, GitHub Pages, itch.io, etc.)
3. Dans l'onglet **UNITY-LIVE CONSOLE**, collez l'URL de votre build WebGL
4. Le dashboard embarque le jeu/app VR via `<iframe>` avec support `xr-spatial-tracking`

## Architecture

```
DATA-DIVE v2.0
├── app.py                  # Application principale Streamlit
├── requirements.txt        # Dépendances Python
│
├── Onglet NETWORK EXPLORER
│   ├── Cypher Command (Neo4j)
│   ├── Cluster Density T-SNE (Plotly)
│   ├── Network Graph VR (Plotly)
│   ├── Métriques (Anomalies, Compute, ECS)
│   ├── Live Frame Telemetry
│   ├── Real-Time Alerts
│   ├── Collaborative Focus
│   └── Session Peers
│
├── Onglet ANOMALY ENGINE
│   ├── Anomaly Feed
│   └── Distribution Chart
│
└── Onglet UNITY-LIVE CONSOLE
    ├── Unity WebGL iFrame embed
    ├── Console Log (temps réel)
    ├── VR Controls
    ├── VR Session Metrics
    └── Integration Status
```

## Connexion WebSocket Unity ↔ Streamlit (avancé)

Pour synchroniser les données en temps réel entre Unity et Streamlit,
utilisez `streamlit-websocket` ou une API REST côté Unity :

```csharp
// Unity C# — envoyer les métriques VR vers Streamlit
IEnumerator SendMetrics() {
    var data = new { fps = 89.4f, anomalies = 14, cluster = "8821" };
    string json = JsonUtility.ToJson(data);
    using var req = new UnityWebRequest("http://localhost:8502/metrics", "POST");
    req.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
    req.downloadHandler = new DownloadHandlerBuffer();
    yield return req.SendWebRequest();
}
```
