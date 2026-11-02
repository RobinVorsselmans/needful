import pytest

from needful.calc.cost import cost_per_use, total_uses


def test_pitch_example():
    assert cost_per_use(149, 3, 4) == 12.42


def test_single_use():
    assert cost_per_use(60, 1, 1) == 60.0


def test_invalid_price():
    with pytest.raises(ValueError):
        cost_per_use(0, 3, 4)


def test_invalid_uses():
    with pytest.raises(ValueError):
        cost_per_use(149, 0, 4)


def test_total_uses_pitch_example():
    assert total_uses(3, 4) == 12
