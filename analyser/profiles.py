from __future__ import annotations

from analyser.models import RadioProfile

DEFAULT_PROFILES: dict[str, RadioProfile] = {
    "au_narrow_916": RadioProfile(
        name="au_narrow_916",
        freq_hz=916_000_000,
        bw_khz=62.5,
        sf=7,
        cr=8,
        sync_word=0x12,
        preamble_len=16,
        cad=True,
    )
}

BW_ENUM_MAP: dict[float, str] = {
    7.8: "BW_7K8",
    10.4: "BW_10K4",
    15.6: "BW_15K6",
    20.8: "BW_20K8",
    31.25: "BW_31K25",
    41.7: "BW_41K7",
    62.5: "BW_62K5",
    125.0: "BW_125K",
    250.0: "BW_250K",
    500.0: "BW_500K",
}


def get_profile(name: str) -> RadioProfile:
    if name not in DEFAULT_PROFILES:
        raise ValueError(f"unknown profile: {name}")
    return DEFAULT_PROFILES[name]


def validate_profile(profile: RadioProfile) -> None:
    if not 100_000_000 <= profile.freq_hz <= 1_000_000_000:
        raise ValueError("freq_hz must be in expected ISM range")
    if profile.bw_khz not in BW_ENUM_MAP:
        raise ValueError(f"unsupported bandwidth {profile.bw_khz}")
    if not 5 <= profile.sf <= 12:
        raise ValueError("sf must be in [5, 12]")
    if not 5 <= profile.cr <= 8:
        raise ValueError("cr must be in [5, 8]")
    if not 0 <= profile.sync_word <= 0xFF:
        raise ValueError("sync_word must be 0..255")
    if not 4 <= profile.preamble_len <= 65535:
        raise ValueError("preamble_len must be >=4")


def profile_to_radio_config(profile: RadioProfile) -> dict[str, int | bool | str]:
    validate_profile(profile)
    return {
        "freq_hz": profile.freq_hz,
        "bw": BW_ENUM_MAP[profile.bw_khz],
        "sf": profile.sf,
        "cr": profile.cr,
        "sync_word": profile.sync_word,
        "preamble_len": profile.preamble_len,
        "cad": profile.cad,
    }
