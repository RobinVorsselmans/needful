import asyncio
import logging

from nicegui.testing import User
from nicegui.testing.user_interaction import UserInteraction

from needful.alternatives import nearby, relevance
from needful.alternatives.examples import EXAMPLE_INSIGHTS
from needful.alternatives.insights import AlternativeDetails, Suggestion
from needful.ui import storage


async def start(user: User, product: str | None = None) -> None:
    await user.open("/")
    if product is not None:
        user.find("Wat wil je kopen").clear().type(product)
    user.find("Start →").click()
    await user.should_see("VRAAG 1/3")


async def choose_alternative(user: User, name: str, names: list[str]) -> None:
    """Klik op vraag 3 "Kies dit alternatief →" onder het alternatief met deze naam.
    De knoppen hebben dezelfde tekst; ze staan in de volgorde van `names`."""
    await user.open("/vraag/3")
    await user.should_see(name)
    buttons = sorted(user.find("Kies dit alternatief →").elements, key=lambda button: button.id)
    UserInteraction(user, {buttons[names.index(name)]}, "Kies dit alternatief →").click()
    await user.should_see("JOUW ADVIES")


async def test_pitch_example_clicks_through_to_lenen(user: User) -> None:
    """start -> 3 vragen -> advies met vb-waarden van de pitch: lenen"""
    await start(user)
    user.find("Het zou handig zijn").click()
    await user.should_see("VRAAG 2/3")
    await user.should_see("= €12,42 per gebruik")
    # zonder LLM-sleutel (zie conftest.py) tonen we de extra kosten van het voorbeeld
    await user.should_see("EXTRA KOSTEN OM MEE REKENING TE HOUDEN")
    await user.should_see("Met extra kosten: €17,28 per gebruik")
    user.find("Klopt →").click()
    await user.should_see("VRAAG 3/3")
    await user.should_see("Tuinslang met spuitstuk en een harde borstel")
    # elk alternatief tegenover kopen: €149 nieuwprijs + €58,40 extra kosten
    await user.should_see("12 keer in 4 jaar: €25 · kopen: €207,40")
    user.find("Nee, lenen of huren is ook goed").click()
    await user.should_see("JOUW ADVIES")
    await user.should_see("Lenen is de slimste keuze.")
    # een eigen keuze: je keuze naast nieuw kopen, niet alles op een rij
    await user.should_see("VERGELIJKING · 12 KEER IN 4 JAAR")
    await user.should_see("Nieuw kopen")
    await user.should_see("★ ONS ADVIES")
    await user.should_see("JOUW KEUZE")
    await user.should_not_see("ALLES OP EEN RIJ")
    await user.should_not_see("Niet kopen")


async def test_everything_in_a_row_is_one_of_the_choices(user: User) -> None:
    """Keuze "Zet alles op een rij" toont alle mogelijkheden, zonder "jouw keuze"."""
    await start(user)
    await user.open("/vraag/3")
    user.find("Zet alles op een rij").click()
    await user.should_see("JOUW ADVIES")
    await user.should_see("ALLES OP EEN RIJ · 12 KEER IN 4 JAAR")
    await user.should_see("Je bespaart €207,40 en ± 40 kg CO2.")
    for name in ("Nieuw kopen", "Huren bij een verhuurder", "Tuinslang", "Niet kopen"):
        await user.should_see(name)
    # nieuw kopen met de exit-strategie erbij
    await user.should_see("verhuur hem aan je buren")
    await user.should_see("★ ONS ADVIES")
    await user.should_not_see("JOUW KEUZE")


async def test_impulse_answer_ends_in_laten(user: User) -> None:
    await start(user)
    user.find("Eerlijk? Ik wil het gewoon").click()
    await user.should_see("VRAAG 2/3")
    await user.open("/advies")
    await user.should_see("Laat het even liggen.")


async def test_must_be_new_and_own_means_buy_consciously(user: User) -> None:
    """Vraag 3 = nieuw en van mij: lenen en huren tellen niet meer mee."""
    await start(user)
    await user.open("/vraag/3")
    user.find("Ja, nieuw en van mij").click()
    await user.should_see("Kopen kan, maar kies bewust.")


async def test_there_is_no_question_4_anymore(user: User) -> None:
    await start(user)
    await user.open("/vraag/3")
    await user.should_see("VRAAG 3/3")
    # de volgende-knop gaat naar het advies, met de keuze die er staat (standaard: alles)
    user.find("Toon mijn advies →").click()
    await user.should_see("ALLES OP EEN RIJ")
    await user.open("/vraag/3")
    await user.should_not_see("verlanglijst")
    await user.should_not_see("Wat beslis je?")


async def test_back_link_returns_to_previous_question(user: User) -> None:
    await user.open("/vraag/2")
    user.find("← Terug").click()
    await user.should_see("VRAAG 1/3")


async def test_advies_has_a_back_link_to_question_3(user: User) -> None:
    await user.open("/advies")
    user.find("← Terug").click()
    await user.should_see("VRAAG 3/3")


async def test_opening_advies_directly_uses_example_and_warns(user: User, caplog) -> None:
    """Iemand opent /advies zonder eerst de vragen te doorlopen: geen crash,
    wel een waarschuwing die zegt welke antwoorden ontbraken."""
    with caplog.at_level(logging.WARNING, logger="needful"):
        await user.open("/advies")
        await user.should_see("Lenen is de slimste keuze.")
    assert "antwoorden ontbreken" in caplog.text
    assert "price" in caplog.text


async def test_choosing_an_alternative_goes_deeper_in_the_advice(user: User) -> None:
    """Vraag 3: kies lenen → het advies rekent het uit; zonder LLM geen stappen."""
    await start(user)
    names = [alternative.name for alternative in EXAMPLE_INSIGHTS.alternatives]
    await choose_alternative(user, "Lenen bij de buren of de uitleendienst", names)
    await user.should_see("JOUW KEUZE")
    # kopen kost €207,40 (nieuwprijs + extra kosten), lenen is gratis
    await user.should_see("Je bespaart €207,40 tegenover kopen.")
    await user.should_see("Hoe vaak je het ook gebruikt: het alternatief blijft goedkoper.")
    await user.should_see("Meer uitleg komt van het taalmodel, dat nu niet bereikbaar is.")


async def test_alternative_details_from_the_llm_are_shown(user: User, monkeypatch) -> None:
    async def fake_details(product, alternative, uses_per_year):
        return AlternativeDetails(
            steps=["Vraag het in de straatgroep op WhatsApp."],
            pros=["Geen aankoop, geen opslag."],
            cons=["Je moet hem ophalen en terugbrengen."],
        )

    monkeypatch.setattr(storage, "alternative_details", fake_details)
    await start(user)
    names = [alternative.name for alternative in EXAMPLE_INSIGHTS.alternatives]
    await choose_alternative(user, "Tuinslang met spuitstuk en een harde borstel", names)
    await user.should_see("HOE BEGIN JE ERAAN")
    await user.should_see("1. Vraag het in de straatgroep op WhatsApp.")
    await user.should_see("+ Geen aankoop, geen opslag.")
    await user.should_see("– Je moet hem ophalen en terugbrengen.")


async def test_nearby_search_shows_places_per_kind(user: User, monkeypatch) -> None:
    """Zonder internet: de bronnen zijn vervangen door vaste antwoorden."""

    async def fake_geocode(postcode: str, gemeente: str) -> nearby.Point:
        assert (postcode, gemeente) == ("2000", "Antwerpen")
        return (51.22, 4.40)

    async def fake_search(origin, shops, alternative_places, alternative_shops):
        assert shops == ["doityourself", "hardware", "garden_centre"]
        assert alternative_places == ["geen", "geen", "geen"]
        # de tuinslang (ander product) zoeken we in doe-het-zelfzaken en tuincentra
        assert alternative_shops == ["doityourself", "garden_centre"]
        hubo = nearby.Place("Hubo", "Bredabaan 1, 2170 Antwerpen", 2.1, ("kopen", "huren"), "", "")
        yield "OpenStreetMap", [hubo]
        yield "Repair Café", None

    monkeypatch.setattr(nearby, "geocode", fake_geocode)
    monkeypatch.setattr(nearby, "search", fake_search)
    await user.open("/buurt")
    user.find("Zoek een verkoop- of huurpunt").click()
    await user.should_see("Bredabaan 1, 2170 Antwerpen")
    # Hubo staat in twee groepen: nieuw kopen en huren
    await user.should_see("Nieuw kopen")
    await user.should_see("Huren")
    assert len(user.find("Hubo").elements) == 2
    await user.should_see("Geen antwoord van Repair Café.")
    # zonder LLM kunnen we niet nakijken of de plaatsen bij het product passen
    await user.should_see("Niet nagekeken op hogedrukreiniger: het taalmodel is niet bereikbaar.")


async def test_nearby_shows_everything_in_a_row_with_second_hand_buttons(user: User) -> None:
    await user.open("/buurt")
    await user.should_see("ALLES OP EEN RIJ · 12 KEER IN 4 JAAR")
    await user.should_see("Lenen bij de buren of de uitleendienst")
    # het product én het andere product (tuinslang) kun je tweedehands zoeken
    await user.should_see("Bekijk tweedehands hogedrukreiniger op 2dehands ↗")
    await user.should_see("Bekijk tweedehands tuinslang op 2dehands ↗")


async def test_nearby_place_not_found(user: User, monkeypatch) -> None:
    async def fake_geocode(postcode: str, gemeente: str) -> None:
        return None

    monkeypatch.setattr(nearby, "geocode", fake_geocode)
    await user.open("/buurt")
    user.find("Zoek een verkoop- of huurpunt").click()
    await user.should_see("We vinden die plaats niet. Klopt de postcode?")


async def test_nearby_back_link_only_goes_to_our_own_screens(user: User) -> None:
    await user.open("/buurt?terug=https://example.com")
    user.find("← Terug").click()
    await user.should_see("JOUW ADVIES")


async def test_nearby_only_keeps_places_the_llm_confirms(user: User, monkeypatch) -> None:
    """Met LLM: Oxfam valt weg voor een wasmachine, de Kringwinkel blijft."""

    async def fake_geocode(postcode: str, gemeente: str) -> nearby.Point:
        return (51.22, 4.40)

    async def fake_search(origin, shops, alternative_places, alternative_shops):
        yield (
            "OpenStreetMap",
            [
                nearby.Place("Oxfam", None, 0.4, ("tweedehands",), "", "OSM"),
                nearby.Place("Kringwinkel Meir", None, 1.0, ("tweedehands",), "", "OSM"),
            ],
        )

    async def fake_check(product, places, alternatives):
        return [place for place in places if place.name != "Oxfam"]

    monkeypatch.setattr(nearby, "geocode", fake_geocode)
    monkeypatch.setattr(nearby, "search", fake_search)
    monkeypatch.setattr(relevance, "check_places", fake_check)
    await user.open("/buurt")
    user.find("Zoek een verkoop- of huurpunt").click()
    await user.should_see("Kringwinkel Meir")
    await user.should_not_see("Oxfam")
    await user.should_not_see("Niet nagekeken")


async def test_nearby_explains_the_wait(user: User, monkeypatch) -> None:
    """Terwijl een bron nog bezig is, zegt het scherm waarop we wachten."""
    release = asyncio.Event()

    async def fake_geocode(postcode: str, gemeente: str) -> nearby.Point:
        return (51.22, 4.40)

    async def fake_search(origin, shops, alternative_places, alternative_shops):
        yield "Repair Café", []
        await release.wait()  # OpenStreetMap laat op zich wachten
        yield "OpenStreetMap", []

    monkeypatch.setattr(nearby, "geocode", fake_geocode)
    monkeypatch.setattr(nearby, "search", fake_search)
    await user.open("/buurt")
    user.find("Zoek een verkoop- of huurpunt").click()
    await user.should_see(
        "Nog aan het zoeken bij OpenStreetMap. Dat kan tot een halve minuut duren."
    )
    release.set()
    await user.should_see("Niets gevonden binnen 5 km.")
    await user.should_not_see("Nog aan het zoeken")


def dryer_insights():
    """Wat het taalmodel over een droogkast zou zeggen: een droogrek en een wassalon (huren)."""

    def alternative(name, kind, search_term, once, per_use, place, shops):
        return Suggestion(
            name=name,
            kind=kind,
            search_term=search_term,
            meaning="",
            once=once,
            per_use=per_use,
            per_year=0,
            place=place,
            shop_types=shops,
        )

    return EXAMPLE_INSIGHTS.model_copy(
        update={
            "alternatives": [
                alternative("Droogrek", "ander", "droogrek", 25, 0, "geen", ["houseware"]),
                alternative("Wassalon", "huren", "wassalon", 0, 3, "wassalon", []),
            ],
            "shop_types": ["appliance", "electronics"],
        }
    )


async def start_dryer(user: User, monkeypatch) -> None:
    async def fake_insights(product):
        return dryer_insights()

    monkeypatch.setattr(storage, "product_insights", fake_insights)
    await start(user, "droogkast")


async def test_dryer_advice_rents_the_laundromat_not_a_rental_company(
    user: User, monkeypatch
) -> None:
    await start_dryer(user, monkeypatch)
    await user.open("/advies")
    await user.should_see("Wassalon")
    await user.should_see("Droogrek")
    await user.should_not_see("Huren bij een verhuurder")


async def test_dryer_advice_shows_the_chosen_drying_rack(user: User, monkeypatch) -> None:
    await start_dryer(user, monkeypatch)
    names = [alternative.name for alternative in dryer_insights().alternatives]
    await choose_alternative(user, "Droogrek", names)
    await user.should_see("JOUW KEUZE")
    await user.should_see("Je bespaart")


async def test_nearby_looks_for_the_product_and_all_alternatives(user: User, monkeypatch) -> None:
    """Droogkast: elektrozaken, wassalons en winkels met droogrekken, in één zoektocht."""
    seen = {}

    async def fake_geocode(postcode: str, gemeente: str) -> nearby.Point:
        return (51.22, 4.40)

    async def fake_search(origin, shops, alternative_places, alternative_shops):
        seen["search"] = (shops, alternative_places, alternative_shops)
        yield "OpenStreetMap", [nearby.Place("HEMA", None, 1.0, ("alternatief",), "", "")]

    async def fake_check(product, places, alternatives):
        seen["check"] = (product, [alternative.name for alternative in alternatives])
        return places

    await start_dryer(user, monkeypatch)
    monkeypatch.setattr(nearby, "geocode", fake_geocode)
    monkeypatch.setattr(nearby, "search", fake_search)
    monkeypatch.setattr(relevance, "check_places", fake_check)
    await user.open("/buurt")
    await user.should_see("Bekijk tweedehands droogkast op 2dehands ↗")
    await user.should_see("Bekijk tweedehands droogrek op 2dehands ↗")
    await user.should_not_see("Bekijk tweedehands wassalon")
    user.find("Zoek een verkoop- of huurpunt").click()
    await user.should_see("HEMA")
    await user.should_see("Alternatieven")
    assert seen["search"] == (["appliance", "electronics"], ["geen", "wassalon"], ["houseware"])
    assert seen["check"] == ("droogkast", ["Droogrek", "Wassalon"])


async def nearby_with_dryer_choice(user: User, monkeypatch, choose) -> dict:
    """Droogkast, kies iets op vraag 3, en zoek in de buurt met vervangen bronnen.
    Geeft terug waarmee gezocht en nagekeken werd."""
    seen = {}

    async def fake_geocode(postcode: str, gemeente: str) -> nearby.Point:
        return (51.22, 4.40)

    async def fake_search(origin, shops, alternative_places, alternative_shops):
        seen["search"] = (shops, alternative_places, alternative_shops)
        yield (
            "OpenStreetMap",
            [
                nearby.Place("Krëfel", None, 1.0, ("kopen",), "", ""),
                nearby.Place("Wassalon OASE", None, 1.5, ("alternatief",), "", ""),
            ],
        )

    async def fake_check(product, places, alternatives):
        seen["check"] = (product, [alternative.name for alternative in alternatives])
        return places

    await start_dryer(user, monkeypatch)
    await choose()
    monkeypatch.setattr(nearby, "geocode", fake_geocode)
    monkeypatch.setattr(nearby, "search", fake_search)
    monkeypatch.setattr(relevance, "check_places", fake_check)
    await user.open("/buurt")
    await user.should_see("Waar kan het in jouw buurt?")
    user.find("Zoek een verkoop- of huurpunt").click()
    return seen


async def test_nearby_after_choosing_the_drying_rack_looks_for_drying_racks(
    user: User, monkeypatch
) -> None:
    names = [alternative.name for alternative in dryer_insights().alternatives]

    async def choose():
        await choose_alternative(user, "Droogrek", names)

    seen = await nearby_with_dryer_choice(user, monkeypatch, choose)
    await user.should_see("Krëfel")
    await user.should_see("droogrek · alternatief voor droogkast")
    await user.should_see("Bekijk tweedehands droogrek op 2dehands ↗")
    await user.should_not_see("Bekijk tweedehands droogkast")
    # enkel winkels voor het droogrek; de wassalon toont dit scherm niet
    assert seen["search"] == (["houseware"], [], [])
    assert seen["check"] == ("droogrek", [])
    await user.should_not_see("Wassalon OASE")


async def test_nearby_after_choosing_to_rent_or_borrow_shows_only_that(
    user: User, monkeypatch
) -> None:
    async def choose():
        await user.open("/vraag/3")
        user.find("Nee, lenen of huren is ook goed").click()
        await user.should_see("JOUW ADVIES")

    seen = await nearby_with_dryer_choice(user, monkeypatch, choose)
    await user.should_see("Wassalon OASE")
    # Krëfel verkoopt enkel nieuw: dat hoort niet bij "lenen of huren"
    await user.should_not_see("Krëfel")
    await user.should_not_see("2dehands ↗")
    assert seen["search"] == (["appliance", "electronics"], ["wassalon"], [])
    assert seen["check"] == ("droogkast", ["Wassalon"])


async def test_nearby_new_or_second_hand_shows_both(user: User, monkeypatch) -> None:
    """ "Van mij, maar tweedehands mag" = nieuw én tweedehands: de verkooppunten (een motordealer)
    staan er gewoon bij als nieuw kopen. Vroeger zochten we enkel tweedehands en vonden we niets."""

    async def choose():
        await user.open("/vraag/3")
        user.find("Van mij, maar tweedehands mag").click()
        await user.should_see("JOUW ADVIES")

    seen = await nearby_with_dryer_choice(user, monkeypatch, choose)
    await user.should_see("Krëfel")
    await user.should_see("Nieuw kopen")
    await user.should_not_see("vraag naar tweedehands")
    await user.should_see("Bekijk tweedehands droogkast op 2dehands ↗")
    await user.should_not_see("Wassalon OASE")
    assert seen["search"] == (["appliance", "electronics"], [], [])


def dryer_with_second_hand():
    """Droogkast met ook een tweedehands wasdroger als alternatief."""
    second = Suggestion(
        name="Tweedehands wasdroger",
        kind="tweedehands",
        search_term="wasdroger",
        meaning="",
        once=120,
        per_use=0,
        per_year=0,
        place="geen",
        shop_types=[],
    )
    insights = dryer_insights()
    return insights.model_copy(update={"alternatives": [*insights.alternatives, second]})


async def test_advice_new_or_second_hand_marks_both_as_your_choice(user: User, monkeypatch) -> None:
    async def fake_insights(product):
        return dryer_with_second_hand()

    monkeypatch.setattr(storage, "product_insights", fake_insights)
    await start(user, "droogkast")
    await user.open("/vraag/3")
    user.find("Van mij, maar tweedehands mag").click()
    await user.should_see("VERGELIJKING")
    await user.should_see("Tweedehands wasdroger")
    # nieuw kopen én tweedehands zijn allebei jouw keuze
    assert len(user.find("JOUW KEUZE").elements) == 2


async def test_nearby_chosen_second_hand_alternative_asks_dealers(user: User, monkeypatch) -> None:
    """Uitdrukkelijk "Tweedehands wasdroger" gekozen: de verkooppunten met "vraag naar tweedehands"."""

    async def fake_insights(product):
        return dryer_with_second_hand()

    async def fake_geocode(postcode: str, gemeente: str) -> nearby.Point:
        return (51.22, 4.40)

    async def fake_search(origin, shops, alternative_places, alternative_shops):
        yield "OpenStreetMap", [nearby.Place("Krëfel", None, 1.0, ("kopen",), "", "")]

    monkeypatch.setattr(storage, "product_insights", fake_insights)
    await start(user, "droogkast")
    names = [alternative.name for alternative in dryer_with_second_hand().alternatives]
    await choose_alternative(user, "Tweedehands wasdroger", names)
    monkeypatch.setattr(nearby, "geocode", fake_geocode)
    monkeypatch.setattr(nearby, "search", fake_search)
    await user.open("/buurt")
    await user.should_see("Waar kan het in jouw buurt?")
    user.find("Zoek een verkoop- of huurpunt").click()
    await user.should_see("Verkooppunten · vraag naar tweedehands")
    await user.should_see("Bekijk tweedehands wasdroger op 2dehands ↗")


async def test_nearby_has_a_new_question_button(user: User) -> None:
    await user.open("/buurt")
    user.find("Nieuwe vraag").click()
    await user.should_see("Start →")
