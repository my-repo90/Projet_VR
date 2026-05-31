from __future__ import annotations


def test_top_anomalies(client):
    response = client.get("/api/anomalies/top", params={"limit": 5})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["node_id"] == "C1"


def test_anomaly_summary(client):
    response = client.get("/api/anomalies/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_anomalies"] == 1
    assert payload["risk_distribution"]["critique"] == 1


def test_sync_status(client):
    response = client.get("/api/sync/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert all(item["available"] for item in payload["files"])
