from __future__ import annotations

import hashlib
from datetime import datetime, timezone


def payload_sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def payload_prefix_hex(payload: bytes, n_bytes: int) -> str:
    return payload[:n_bytes].hex()


def duplicate_key(payload_hash: str, ts: datetime, bucket_secs: int = 30) -> str:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    bucket = int(ts.timestamp()) // bucket_secs
    return f"{payload_hash[:16]}:{bucket}"
