from __future__ import annotations

from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.services import sync_service

router = APIRouter(prefix="/sync", tags=["sync"])


class SyncEvent(BaseModel):
    type: str
    payload: dict[str, Any] = {}


@router.get("/status")
def status() -> dict:
    return sync_service.data_status()


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
