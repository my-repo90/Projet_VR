from __future__ import annotations


def test_list_nodes_with_filters(client):
    response = client.get("/api/nodes", params={"risk_level": "critique"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["node_id"] == "C1"


def test_get_node_by_id(client):
    response = client.get("/api/nodes/C2")

    assert response.status_code == 200
    assert response.json()["cluster_label"] == 2


def test_edges_endpoint(client):
    response = client.get("/api/edges", params={"fraud_only": True})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["edge_id"] == "E1"
