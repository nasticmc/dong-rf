from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class CollectorStatus:
    running: bool = False
    started_at: datetime | None = None
    packets_seen: int = 0
    last_packet_at: datetime | None = None
    last_error: str | None = None

    def as_dict(self) -> dict:
        return {
            "running": self.running,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "packets_seen": self.packets_seen,
            "last_packet_at": self.last_packet_at.isoformat() if self.last_packet_at else None,
            "last_error": self.last_error,
            "now": datetime.now(timezone.utc).isoformat(),
        }
