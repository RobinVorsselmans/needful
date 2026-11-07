from needful.calc.advice import Alternative, allowed, best, decide

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


def test_reasons_read_as_proper_sentences():
    # De reden staat letterlijk op het adviesscherm: geen aan elkaar geplakte woorden
    impulse = decide("impuls", 149, 12, PITCH, 62).reason
    second_hand = decide("concreet", 149, 12, [RENTAL, SECOND_HAND], 62).reason
    assert "nodig. Wacht" in impulse
    assert "€60 en je kunt" in second_hand
    assert "  " not in impulse + second_hand


def test_best_picks_cheapest():
    assert best(PITCH, "lenen") == NEIGHBOUR


def test_best_return_none_when_nothing_of_that_kind_exists():
    assert best([RENTAL], "lenen") is None


def test_without_score_the_reason_skips_it():
    advice = decide("kapot", 149, 40, [])
    assert advice.outcome == "bewust kopen"
    assert "duurzaamheidsscore" not in advice.reason
    assert advice.reason.startswith("Je gebruikt het 40 keer. Kies")


def test_new_and_own_means_no_alternatives():
    assert allowed(PITCH, "nieuw") == []


def test_own_but_second_hand_keeps_only_second_hand():
    assert allowed(PITCH, "tweedehands") == [SECOND_HAND]


def test_access_is_enough_keeps_everything():
    assert allowed(PITCH, "toegang") == PITCH


def test_pitch_example_that_must_be_new_means_buy_consciously():
    # vraag 3 = "Ja, nieuw en van mij": lenen bij de buren telt dan niet mee
    assert decide("handig", 149, 12, allowed(PITCH, "nieuw")).outcome == "bewust kopen"


def test_lending_without_known_distance_counts_as_nearby():
    # voorstel van het taalmodel: "lenen bij de buren", zonder afstand
    lend = Alternative("Lenen bij de buren", "lenen", None, 0)
    advice = decide("handig", 149, 12, [lend])
    assert advice.outcome == "lenen"
    assert advice.reason == "Je gebruikt het 12 keer. Lenen bij de buren: dat kan gratis."


def test_known_distance_wins_from_unknown_at_the_same_price():
    unknown = Alternative("Uitleendienst", "lenen", None, 0)
    assert best([unknown, NEIGHBOUR], "lenen") == NEIGHBOUR


def test_laundromat_counts_as_renting():
    # droogkast €500, 100 keer: wassalon €3 per keer = €300, goedkoper dan kopen
    laundromat = Alternative("Wassalon", "huren", None, 3)
    advice = decide("concreet", 500, 100, [laundromat])
    assert advice.outcome == "huren"
    assert "Wassalon" in advice.reason
