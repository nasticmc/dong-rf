import pytest

from analyser.models import RadioProfile
from analyser.profiles import get_profile, profile_to_radio_config, validate_profile


def test_default_profile_is_available():
    p = get_profile("au_narrow_916")
    assert p.freq_hz == 916_000_000
    assert p.bw_khz == 62.5


def test_profile_converts_to_radio_config():
    cfg = profile_to_radio_config(get_profile("au_narrow_916"))
    assert cfg["bw"] == "BW_62K5"


def test_profile_validation_rejects_invalid_bandwidth():
    p = RadioProfile(
        name="bad",
        freq_hz=916_000_000,
        bw_khz=111.0,
        sf=7,
        cr=8,
        sync_word=0x12,
        preamble_len=16,
        cad=True,
    )
    with pytest.raises(ValueError):
        validate_profile(p)
