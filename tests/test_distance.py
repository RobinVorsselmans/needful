from needful.calc.distance import distance_km

ANTWERPEN = (51.2211, 4.3997)
BRUSSEL = (50.8466, 4.3528)


def test_same_place_is_zero():
    assert distance_km(ANTWERPEN, ANTWERPEN) == 0


def test_antwerpen_brussel_is_about_42_km():
    # in vogelvlucht, niet over de weg
    assert 41 < distance_km(ANTWERPEN, BRUSSEL) < 43


def test_distance_is_the_same_both_ways():
    assert distance_km(ANTWERPEN, BRUSSEL) == distance_km(BRUSSEL, ANTWERPEN)
