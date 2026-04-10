from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class RadioProfile:
    name: str
    freq_hz: int
    bw_khz: float
    sf: int
    cr: int
    sync_word: int
    preamble_len: int
    cad: bool = True


@dataclass(slots=True)
class PacketRecord:
    ts_utc: datetime
    profile_id: int
    rssi_dbm: float
    snr_db: float
    payload_len: int
    payload_hex: str
    payload_sha256: str
    prefix_hex_4: str
    prefix_hex_8: str
    airtime_ms_est: float
    duplicate_key: str
