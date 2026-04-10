from analyser.airtime import estimate_airtime_ms


def test_airtime_increases_with_payload_size():
    small = estimate_airtime_ms(62.5, 7, 8, 16, 8)
    large = estimate_airtime_ms(62.5, 7, 8, 16, 32)
    assert large > small


def test_airtime_positive():
    value = estimate_airtime_ms(125.0, 9, 5, 8, 12)
    assert value > 0
