from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    db_path: str = os.getenv("ANALYSER_DB_PATH", "meshcore_analyser.db")
    profile_name: str = os.getenv("ANALYSER_PROFILE", "au_narrow_916")
    device_port: str = os.getenv("ANALYSER_DEVICE_PORT", "/dev/ttyACM0")
    host: str = os.getenv("ANALYSER_HOST", "127.0.0.1")
    port: int = int(os.getenv("ANALYSER_PORT", "8000"))


def get_settings() -> Settings:
    return Settings()
