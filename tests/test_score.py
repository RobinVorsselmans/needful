import pytest

from needful.calc.score import durability_score


def test_pitch_example_scores_62():
    assert durability_score("ja", "deels", "nee", "ja") == 62


def test_everything_yes_scores_100():
    assert durability_score("ja", "ja", "ja", "ja") == 100


def test_everything_no_scores_0():
    assert durability_score("nee", "nee", "nee", "nee") == 0


def test_half_points_round_down():
    assert durability_score("ja", "ja", "ja", "deels") == 87


def test_unkown_value_raises_value_error():
    with pytest.raises(ValueError):
        durability_score("ja", "misschien", "ja", "nee")
