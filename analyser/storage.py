from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from analyser.models import PacketRecord, RadioProfile


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS radio_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    freq_hz INTEGER NOT NULL,
    bw_khz REAL NOT NULL,
    sf INTEGER NOT NULL,
    cr INTEGER NOT NULL,
    sync_word INTEGER NOT NULL,
    preamble_len INTEGER NOT NULL,
    cad INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS packets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_utc TEXT NOT NULL,
    profile_id INTEGER NOT NULL,
    rssi_dbm REAL NOT NULL,
    snr_db REAL NOT NULL,
    payload_len INTEGER NOT NULL,
    payload_hex TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    prefix_hex_4 TEXT NOT NULL,
    prefix_hex_8 TEXT NOT NULL,
    airtime_ms_est REAL NOT NULL,
    duplicate_key TEXT NOT NULL,
    FOREIGN KEY(profile_id) REFERENCES radio_profiles(id)
);

CREATE INDEX IF NOT EXISTS idx_packets_ts ON packets(ts_utc);
CREATE INDEX IF NOT EXISTS idx_packets_hash ON packets(payload_sha256);
CREATE INDEX IF NOT EXISTS idx_packets_dup ON packets(duplicate_key);
"""


class Storage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA_SQL)

    def upsert_profile(self, profile: RadioProfile) -> int:
        created_at = datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO radio_profiles
                    (name, freq_hz, bw_khz, sf, cr, sync_word, preamble_len, cad, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    freq_hz=excluded.freq_hz,
                    bw_khz=excluded.bw_khz,
                    sf=excluded.sf,
                    cr=excluded.cr,
                    sync_word=excluded.sync_word,
                    preamble_len=excluded.preamble_len,
                    cad=excluded.cad
                """,
                (
                    profile.name,
                    profile.freq_hz,
                    profile.bw_khz,
                    profile.sf,
                    profile.cr,
                    profile.sync_word,
                    profile.preamble_len,
                    int(profile.cad),
                    created_at,
                ),
            )
            row = conn.execute("SELECT id FROM radio_profiles WHERE name = ?", (profile.name,)).fetchone()
        return int(row["id"])

    def insert_packet(self, packet: PacketRecord) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO packets (
                    ts_utc, profile_id, rssi_dbm, snr_db, payload_len,
                    payload_hex, payload_sha256, prefix_hex_4, prefix_hex_8,
                    airtime_ms_est, duplicate_key
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    packet.ts_utc.isoformat(),
                    packet.profile_id,
                    packet.rssi_dbm,
                    packet.snr_db,
                    packet.payload_len,
                    packet.payload_hex,
                    packet.payload_sha256,
                    packet.prefix_hex_4,
                    packet.prefix_hex_8,
                    packet.airtime_ms_est,
                    packet.duplicate_key,
                ),
            )

    def recent_packets(self, limit: int = 100) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT p.*, rp.name as profile_name
                FROM packets p
                JOIN radio_profiles rp ON rp.id = p.profile_id
                ORDER BY p.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def stats_summary(self, minutes: int = 60) -> dict:
        since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT
                  COUNT(*) as packet_count,
                  COALESCE(SUM(airtime_ms_est), 0) as airtime_ms_total,
                  COALESCE(AVG(rssi_dbm), 0) as avg_rssi,
                  COALESCE(AVG(snr_db), 0) as avg_snr
                FROM packets
                WHERE ts_utc >= ?
                """,
                (since.isoformat(),),
            ).fetchone()
        return dict(row)

    def stats_timeseries(self, minutes: int = 60) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                  strftime('%Y-%m-%dT%H:%M:00Z', ts_utc) AS minute,
                  COUNT(*) as packet_count,
                  SUM(airtime_ms_est) as airtime_ms_total
                FROM packets
                WHERE ts_utc >= ?
                GROUP BY minute
                ORDER BY minute ASC
                """,
                (since.isoformat(),),
            ).fetchall()
        return [dict(r) for r in rows]

    def top_fingerprints(self, limit: int = 50) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT payload_sha256, prefix_hex_4, prefix_hex_8, COUNT(*) as count
                FROM packets
                GROUP BY payload_sha256, prefix_hex_4, prefix_hex_8
                ORDER BY count DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_profile(self, name: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM radio_profiles WHERE name = ?", (name,)).fetchone()
        return dict(row) if row else None
