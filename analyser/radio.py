from __future__ import annotations

from dataclasses import dataclass

from analyser.profiles import profile_to_radio_config


class RadioError(RuntimeError):
    pass


@dataclass(slots=True)
class NormalizedPacket:
    rssi_dbm: float
    snr_db: float
    payload: bytes


class DongLoRaRadio:
    def __init__(self, port: str):
        self.port = port
        self._client = None

    def connect(self) -> None:
        try:
            from donglora import connect  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on local package availability
            raise RadioError("donglora package not available") from exc

        try:
            self._client = connect(self.port)
        except Exception as exc:
            raise RadioError(f"failed to connect to {self.port}") from exc

    def apply_profile(self, profile) -> None:
        if self._client is None:
            raise RadioError("radio not connected")
        cfg = profile_to_radio_config(profile)
        try:
            self._client.send("SetConfig", cfg)
        except Exception as exc:
            raise RadioError("failed to apply radio config") from exc

    def start_rx(self) -> None:
        if self._client is None:
            raise RadioError("radio not connected")
        self._client.send("StartRx", {})

    def stop_rx(self) -> None:
        if self._client is None:
            return
        self._client.send("StopRx", {})

    def recv_packet(self, timeout: float = 1.0) -> NormalizedPacket | None:
        if self._client is None:
            raise RadioError("radio not connected")
        msg = self._client.recv(timeout=timeout)
        if not msg or msg.get("type") != "RxPacket":
            return None
        payload = msg.get("payload", b"")
        if isinstance(payload, str):
            payload = bytes.fromhex(payload)
        return NormalizedPacket(
            rssi_dbm=float(msg.get("rssi", 0.0)),
            snr_db=float(msg.get("snr", 0.0)),
            payload=payload,
        )
