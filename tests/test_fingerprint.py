from datetime import datetime, timezone

from analyser.fingerprint import duplicate_key, payload_prefix_hex, payload_sha256


def test_payload_hash_and_prefixes():
    payload = bytes.fromhex("0102030405060708")
    assert len(payload_sha256(payload)) == 64
    assert payload_prefix_hex(payload, 4) == "01020304"
    assert payload_prefix_hex(payload, 8) == "0102030405060708"


def test_duplicate_key_buckets_time():
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    key = duplicate_key("ab" * 32, ts, bucket_secs=30)
    assert key.startswith("abababababababab:")
