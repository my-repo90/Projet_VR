from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import WebSocket

from app.config import settings
from app.services.data_store import resolve_data_file, store


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        disconnected: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except RuntimeError:
                disconnected.append(connection)
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


def clear_cache() -> dict[str, Any]:
    store.clear()
    return {
        "status": "reloaded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def data_status() -> dict[str, Any]:
    files = ["nodes_3d.json", "edges.json", "clusters.json", "anomalies.json"]
    result = []

    for filename in files:
        path = resolve_data_file(filename)
        result.append(
            {
                "name": filename,
                "available": path is not None,
                "path": str(path) if path else None,
                "size_bytes": path.stat().st_size if path and path.exists() else 0,
            }
        )

    return {
        "status": "ok",
        "connected_clients": len(manager.active_connections),
        "files": result,
    }


def import_exports() -> dict[str, Any]:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    copied: list[dict[str, str]] = []
    missing: list[str] = []

    mappings = {
        "nodes_3d.json": [
            settings.phase2_export_dir / "nodes_3d.json",
        ],
        "anomalies.json": [
            settings.phase2_export_dir / "anomalies.json",
        ],
        "clusters.json": [
            settings.phase2_export_dir / "clusters_summary.json",
            settings.phase2_export_dir / "clusters.json",
        ],
        "edges.json": [
            settings.phase1_export_dir / "edges.json",
            settings.project_data_dir / "edges.csv",
        ],
    }

    for target_name, candidates in mappings.items():
        source = next((candidate for candidate in candidates if candidate.exists()), None)
        if source is None:
            missing.append(target_name)
            continue
        target = settings.data_dir / (
            source.name if source.suffix.lower() != Path(target_name).suffix.lower() else target_name
        )
        shutil.copy2(source, target)
        copied.append({"source": str(source.resolve()), "target": str(target.resolve())})

    store.clear()
    return {
        "status": "imported",
        "copied": copied,
        "missing": missing,
    }


async def publish_event(event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    message = {
        "type": event_type,
        "payload": payload or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await manager.broadcast(message)
    return {
        "status": "sent",
        "connected_clients": len(manager.active_connections),
        "event": message,
    }
