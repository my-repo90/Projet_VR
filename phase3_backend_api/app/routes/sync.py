from __future__ import annotations

from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.services import sync_service

router = APIRouter(prefix="/sync", tags=["sync"])


# ── MODÈLE ET ÉTAT DE SYNCHRONISATION (AJOUTÉ) ─────────────────────
class UnitySyncData(BaseModel):
    cluster_id: int
    is_fraud: int

current_sync_state = {
    "cluster_id": -1,
    "is_fraud": 0
}
# ───────────────────────────────────────────────────────────────────


class SyncEvent(BaseModel):
    type: str
    payload: dict[str, Any] = {}


@router.get("/status")
def status() -> dict:
    return sync_service.data_status()


# ── NOUVELLES ROUTES POUR STREAMLIT ET UNITY (AJOUTÉES) ────────────
@router.post("/nodes/update")
async def update_unity_state(data: UnitySyncData):
    global current_sync_state
    current_sync_state["cluster_id"] = data.cluster_id
    current_sync_state["is_fraud"] = data.is_fraud
    # Optionnel: Notifie aussi via ton système d'événement ou WS existant
    await sync_service.publish_event("ui_sync_updated", current_sync_state)
    return {"status": "success", "updated_state": current_sync_state}


@router.get("/nodes/state")
async def get_unity_sync_state():
    return current_sync_state
# ───────────────────────────────────────────────────────────────────


@router.post("/reload")
async def reload_data() -> dict:
    result = sync_service.clear_cache()
    await sync_service.publish_event("data_reloaded", result)
    return result


@router.post("/import")
async def import_data() -> dict:
    result = sync_service.import_exports()
    await sync_service.publish_event("data_imported", result)
    return result


@router.post("/from-phase2")
async def import_from_phase2() -> dict:
    result = sync_service.import_exports()
    await sync_service.publish_event("data_imported", result)
    return result


@router.post("/events")
async def publish_event(event: SyncEvent) -> dict:
    return await sync_service.publish_event(event.type, event.payload)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await sync_service.manager.connect(websocket)
    try:
        await websocket.send_json({"type": "connected", "payload": sync_service.data_status()})
        while True:
            payload = await websocket.receive_json()
            await sync_service.publish_event("client_event", payload)
    except WebSocketDisconnect:
        sync_service.manager.disconnect(websocket)
