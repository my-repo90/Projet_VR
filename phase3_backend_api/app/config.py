from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def _resolve_path(value: str | None, default: str) -> Path:
    raw = value or default
    path = Path(raw)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path.resolve()


def _split_origins(value: str) -> List[str]:
    if value.strip() == "*":
        return ["*"]
    return [origin.strip() for origin in value.split(",") if origin.strip()]


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "Data Dive Backend API")
    app_env: str = os.getenv("APP_ENV", "development")
    api_prefix: str = os.getenv("API_PREFIX", "/api")
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))
    cors_origins: List[str] = None
    data_dir: Path = None
    phase2_export_dir: Path = None
    phase1_export_dir: Path = None
    project_data_dir: Path = None
    log_file: Path = None

    def __post_init__(self) -> None:
        self.cors_origins = _split_origins(os.getenv("CORS_ORIGINS", "*"))
        self.data_dir = _resolve_path(os.getenv("DATA_DIR"), "data")
        self.phase2_export_dir = _resolve_path(
            os.getenv("PHASE2_EXPORT_DIR"), "../ph2-main/data/export"
        )
        self.phase1_export_dir = _resolve_path(
            os.getenv("PHASE1_EXPORT_DIR"), "../phase1_data_engineering-main/data/export"
        )
        self.project_data_dir = _resolve_path(os.getenv("PROJECT_DATA_DIR"), "..")
        self.log_file = _resolve_path(os.getenv("LOG_FILE"), "logs/api.log")


settings = Settings()
