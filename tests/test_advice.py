from needful.calc.advice import Alternative, best, decide

# De voorbeeldalternatieven uit de pitch
LIBRARY = Alternative("Gereedschapsbib", "lenen", 1.2, 0)
NEIGHBOUR = Alternative("Buren", "lenen", 0.6, 0)
RENTAL = Alternative("Verhuur", "huren", 2.1, 25)
SECOND_HAND = Alternative("Tweedehands", "tweedehands", 10, 60)
PITCH = [LIBRARY, NEIGHBOUR, RENTAL, SECOND_HAND]


def test_pitch_example_says_lend_from_the_neighbour():
    advice = decide("handig", 149, 12, PITCH, 62)
    assert advice.outcome == "lenen"
    assert advice.headline == "Lenen is de slimste keuze."
    assert "Buren" in advice.reason
    assert advice.savings == 149


def test_impulse_buy_means_leave_it_even_if_lending_is_free():
    advice = decide("impuls", 149, 12, PITCH, 62)
    assert advice.outcome == "laten"
    assert advice.headline == "Laat het even liggen."
    assert [c.rule for c in advice.checks] == ["impuls"]


def test_lending_exactly_at_the_limit_still_counts():
    lend = Alternative("Gereedschapsbib", "lenen", 2.0, 0)
    assert decide("handig", 149, 12, [lend], 62).outcome == "lenen"


def test_lending_just_past_the_limit_does_not_count():
    lend = Alternative("Gereedschapsbib", "lenen", 2.1, 0)
    assert decide("handig", 149, 12, [lend], 62).outcome != "lenen"


def test_using_it_often_means_lending_is_not_advised():
    assert decide("handig", 149, 25, [NEIGHBOUR], 62).outcome != "lenen"


def test_rent_when_renting_is_cheaper_than_buying():
    advice = decide("concreet", 149, 3, [RENTAL, SECOND_HAND], 62)
    assert advice.outcome == "huren"
    assert advice.savings == 74


def test_buy_second_hand_when_renting_is_too_expensive():
    advice = decide("concreet", 149, 12, [RENTAL, SECOND_HAND], 62)
    assert advice.outcome == "kopen & doorverkopen"
    assert advice.savings == 89


def test_nothing_fits_means_buy_consciously():
    advice = decide("kapot", 149, 40, [], 62)
    assert advice.outcome == "bewust kopen"
    assert "62/100" in advice.reason
    assert [c.rule for c in advice.checks] == [
        "impuls",
        "lenen",
        "huren",
        "tweedehands",
        "bewust kopen",
    ]


def test_best_picks_cheapest():
    assert best(PITCH, "lenen") == NEIGHBOUR


def test_best_return_none_when_nothing_of_that_kind_exists():
    assert best([RENTAL], "lenen") is None
