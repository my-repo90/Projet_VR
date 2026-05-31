from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.data_store import store


@pytest.fixture()
def client() -> TestClient:
    data_dir = Path(__file__).parent / "fixtures" / "data"
    original_data_dir = settings.data_dir
    original_phase2_dir = settings.phase2_export_dir
    original_phase1_dir = settings.phase1_export_dir
    settings.data_dir = data_dir
    settings.phase2_export_dir = data_dir / "missing_phase2"
    settings.phase1_export_dir = data_dir / "missing_phase1"
    store.clear()

    try:
        yield TestClient(app)
    finally:
        settings.data_dir = original_data_dir
        settings.phase2_export_dir = original_phase2_dir
        settings.phase1_export_dir = original_phase1_dir
        store.clear()
