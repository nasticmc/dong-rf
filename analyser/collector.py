from __future__ import annotations

import threading
import time
from datetime import datetime, timezone

from analyser.airtime import estimate_airtime_ms
from analyser.fingerprint import duplicate_key, payload_prefix_hex, payload_sha256
from analyser.models import PacketRecord, RadioProfile
from analyser.radio import DongLoRaRadio, RadioError
from analyser.stats import CollectorStatus
from analyser.storage import Storage


class Collector:
    def __init__(self, storage: Storage, radio: DongLoRaRadio, profile: RadioProfile):
        self.storage = storage
        self.radio = radio
        self.profile = profile
        self.status = CollectorStatus()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._profile_id: int | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        self.status.running = True
        self.status.started_at = datetime.now(timezone.utc)
        try:
            self.storage.init_db()
            self._profile_id = self.storage.upsert_profile(self.profile)
            self.radio.connect()
            self.radio.apply_profile(self.profile)
            self.radio.start_rx()

            while not self._stop_event.is_set():
                pkt = self.radio.recv_packet(timeout=1.0)
                if pkt is None:
                    continue
                now = datetime.now(timezone.utc)
                p_hash = payload_sha256(pkt.payload)
                record = PacketRecord(
                    ts_utc=now,
                    profile_id=self._profile_id,
                    rssi_dbm=pkt.rssi_dbm,
                    snr_db=pkt.snr_db,
                    payload_len=len(pkt.payload),
                    payload_hex=pkt.payload.hex(),
                    payload_sha256=p_hash,
                    prefix_hex_4=payload_prefix_hex(pkt.payload, 4),
                    prefix_hex_8=payload_prefix_hex(pkt.payload, 8),
                    airtime_ms_est=estimate_airtime_ms(
                        bw_khz=self.profile.bw_khz,
                        sf=self.profile.sf,
                        cr=self.profile.cr,
                        preamble_len=self.profile.preamble_len,
                        payload_len=len(pkt.payload),
                    ),
                    duplicate_key=duplicate_key(p_hash, now),
                )
                self.storage.insert_packet(record)
                self.status.packets_seen += 1
                self.status.last_packet_at = now
        except RadioError as exc:
            self.status.last_error = str(exc)
        except Exception as exc:  # pragma: no cover - defensive
            self.status.last_error = f"unexpected error: {exc}"
        finally:
            try:
                self.radio.stop_rx()
            except Exception:
                pass
            self.status.running = False
            time.sleep(0.05)
