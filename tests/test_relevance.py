from needful.alternatives import llm, relevance
from needful.alternatives.examples import EXAMPLE_INSIGHTS
from needful.alternatives.nearby import Place
from needful.alternatives.relevance import PlaceCheck, PlaceChecks

OXFAM = Place("Oxfam", None, 0.4, ("tweedehands",), "", "OSM", "shop=charity, brand=Oxfam")
KRINGWINKEL = Place("Kringwinkel", None, 1.0, ("tweedehands",), "", "OSM", "shop=second_hand")
HUBO = Place("Hubo", None, 2.0, ("kopen", "huren"), "", "OSM", "shop=doityourself")
PLACES = [OXFAM, KRINGWINKEL, HUBO]


def checks(*confirmed: tuple[int, list[str]]) -> PlaceChecks:
    return PlaceChecks(
        places=[PlaceCheck(id=number, reason="", tags=tags) for number, tags in confirmed]
    )


def test_only_confirmed_places_and_tags_stay():
    # wasmachine: Oxfam niet (1 ontbreekt), Kringwinkel wel, Hubo enkel kopen
    kept = relevance.apply(PLACES, checks((2, ["tweedehands"]), (3, ["kopen"])))
    assert [place.name for place in kept] == ["Kringwinkel", "Hubo"]
    assert kept[1].tags == ("kopen",)


def test_llm_cannot_add_tags():
    # Oxfam krijgt van het LLM "kopen" en "lenen", maar wij hadden enkel tweedehands
    kept = relevance.apply(PLACES, checks((1, ["kopen", "lenen"])))
    assert kept == []


def test_empty_list_from_the_llm_removes_the_place():
    assert relevance.apply([OXFAM], checks((1, []))) == []


def test_prompt_numbers_the_places_and_shows_what_they_are():
    text = relevance.prompt("wasmachine", PLACES, EXAMPLE_INSIGHTS.alternatives)
    assert "1. Oxfam (shop=charity, brand=Oxfam) · tags: tweedehands" in text
    assert "3. Hubo (shop=doityourself) · tags: kopen, huren" in text
    assert "Iemand zoekt in de buurt naar: wasmachine" in text


async def test_without_llm_nothing_is_checked():
    # conftest.py zet de sleutel leeg: None = het scherm toont alles, met een melding
    assert await relevance.check_places("wasmachine", PLACES, []) is None


async def test_no_places_needs_no_llm():
    assert await relevance.check_places("wasmachine", [], []) == []


async def test_llm_answer_is_applied(monkeypatch):
    async def fake_ask(system, prompt, model):
        return checks((2, ["tweedehands"]))

    monkeypatch.setattr(llm, "ask", fake_ask)
    kept = await relevance.check_places("wasmachine", PLACES, [])
    assert [place.name for place in kept] == ["Kringwinkel"]


def test_prompt_explains_the_kinds_of_shops_in_the_list():
    inno = Place("Inno", None, 0.5, ("kopen",), "", "OSM", "shop=department_store, brand=Inno")
    text = relevance.prompt("wasmachine", [inno, OXFAM], [])
    assert "department_store: warenhuis (Inno, HEMA)" in text
    assert "charity: liefdadigheidswinkel (Oxfam)" in text
    # winkeltypes die niet in de lijst staan, staan ook niet in de uitleg
    assert "doityourself" not in text
