from __future__ import annotations

import math


def estimate_airtime_ms(
    bw_khz: float,
    sf: int,
    cr: int,
    preamble_len: int,
    payload_len: int,
    crc_enabled: bool = True,
    explicit_header: bool = True,
    low_data_rate_opt: bool | None = None,
) -> float:
    """Estimate LoRa airtime in milliseconds.

    CR is expected as denominator style coding rate (5..8), corresponding to 4/5..4/8.
    """
    if payload_len < 0:
        raise ValueError("payload_len must be >= 0")

    bw_hz = bw_khz * 1000.0
    de = int(low_data_rate_opt) if low_data_rate_opt is not None else int((sf >= 11) and bw_khz <= 125.0)
    ih = 0 if explicit_header else 1
    crc = 1 if crc_enabled else 0

    t_sym = (2**sf) / bw_hz
    t_preamble = (preamble_len + 4.25) * t_sym

    v = 8 * payload_len - 4 * sf + 28 + 16 * crc - 20 * ih
    denom = 4 * (sf - 2 * de)
    payload_sym = 8 + max(math.ceil(v / denom) * cr, 0)
    t_payload = payload_sym * t_sym

    return (t_preamble + t_payload) * 1000.0
