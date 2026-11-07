import pytest
from pydantic import ValidationError

from needful.alternatives import insights, llm
from needful.alternatives.examples import EXAMPLE_INSIGHTS
from needful.alternatives.insights import (
    AlternativeDetails,
    ExtraCost,
    ProductInsights,
    Suggestion,
)


def openrouter(content: str) -> dict:
    """Zo ziet een antwoord van OpenRouter eruit (ingekort)."""
    return {"choices": [{"message": {"content": content}}], "usage": {"total_tokens": 900}}


def test_valid_answer_is_parsed():
    data = openrouter(EXAMPLE_INSIGHTS.model_dump_json())
    assert llm.parse_answer(data, ProductInsights) == EXAMPLE_INSIGHTS


def test_answer_that_is_no_json_gives_none():
    assert llm.parse_answer(openrouter("Sorry, dat weet ik niet."), ProductInsights) is None


def test_answer_with_missing_field_gives_none():
    assert llm.parse_answer(openrouter('{"co2_kg": 40}'), ProductInsights) is None


def test_empty_response_gives_none():
    assert llm.parse_answer({"choices": []}, ProductInsights) is None


async def test_without_api_key_the_llm_is_skipped():
    # conftest.py zet de sleutel leeg
    assert await llm.ask("systeem", "vraag", ProductInsights) is None


def test_schema_is_strict_for_the_llm():
    # strikte JSON-schema's: elk object verbiedt extra velden en vraagt álle velden
    schema = ProductInsights.model_json_schema()
    for part in [schema, *schema["$defs"].values()]:
        assert part["additionalProperties"] is False
        assert set(part["required"]) == set(part["properties"])


def test_extra_cost_of_the_pitch_example():
    # stroom €0,45 + water €1,75 per keer × 12 keer, onderhoud €8 per jaar × 4 jaar
    assert EXAMPLE_INSIGHTS.extra_cost(3, 4) == 58.40


def suggestion(
    name: str, once: float = 0, per_use: float = 0, kind: str = "ander", per_year: float = 0
) -> Suggestion:
    return Suggestion(
        name=name,
        kind=kind,
        search_term=name.lower(),
        meaning="",
        once=once,
        per_use=per_use,
        per_year=per_year,
        place="geen",
        shop_types=[],
    )


async def test_llm_mistakes_are_cleaned_up(monkeypatch):
    answer = EXAMPLE_INSIGHTS.model_copy(
        update={
            "extra_costs": [ExtraCost(name="Fout", per_use=-5, per_year=0, note="")]
            + [ExtraCost(name=f"Kost {i}", per_use=1, per_year=0, note="") for i in range(5)],
            "alternatives": [suggestion("Fout", per_use=-1)]
            + [suggestion(f"Alternatief {i}") for i in range(4)],
            "shop_types": ["doityourself", "ruimteschip", '"];out;'],
        }
    )

    async def fake_ask(system, prompt, model):
        return answer

    monkeypatch.setattr(llm, "ask", fake_ask)
    found = await insights.product_insights("hogedrukreiniger")
    assert [cost.name for cost in found.extra_costs] == ["Kost 0", "Kost 1", "Kost 2", "Kost 3"]
    names = [alternative.name for alternative in found.alternatives]
    assert names == ["Alternatief 0", "Alternatief 1", "Alternatief 2"]
    assert found.shop_types == ["doityourself"]


async def test_failing_llm_gives_none(monkeypatch):
    async def fake_ask(system, prompt, model):
        return None

    monkeypatch.setattr(llm, "ask", fake_ask)
    assert await insights.product_insights("hogedrukreiniger") is None


def test_prompt_mentions_the_product():
    assert "Iemand overweegt dit te kopen: wasmachine" in insights.prompt("wasmachine")


def test_alternative_costs_over_the_same_period_as_buying():
    # wassalon €6 per keer, 3 keer per jaar, 4 jaar
    assert suggestion("Wassalon", per_use=6).total_cost(3, 4) == 72
    # tuinslang en borstel: één keer €25
    assert EXAMPLE_INSIGHTS.alternatives[0].total_cost(3, 4) == 25


def test_alternative_place_must_be_one_we_know():
    # het schema laat het LLM enkel kiezen uit de soorten plaatsen die we kunnen zoeken
    with pytest.raises(ValidationError):
        Suggestion(
            name="x",
            kind="ander",
            search_term="x",
            meaning="",
            once=0,
            per_use=0,
            per_year=0,
            place="kasteel",
            shop_types=[],
        )


def test_prompt_lists_the_places_we_can_search():
    assert "wassalon, carwash" in insights.prompt("wasmachine")


def test_energy_and_water_are_computed_by_us():
    # het voorbeeld geeft 1,5 kWh en 350 liter; wij maken er €0,45 en €1,75 van
    costs = {cost.name: cost for cost in EXAMPLE_INSIGHTS.costs()}
    assert costs["Stroom"].per_use == 0.45
    assert costs["Water"].per_use == 1.75
    assert costs["Stroom"].note == "± 1,5 kWh per keer"
    assert list(costs) == ["Stroom", "Water", "Onderhoud"]


def test_no_energy_or_water_means_no_such_rows():
    dry = EXAMPLE_INSIGHTS.model_copy(update={"kwh_per_use": 0, "liters_per_use": 0})
    assert [cost.name for cost in dry.costs()] == ["Onderhoud"]


def test_chosen_alternative_is_found_by_name():
    lend = EXAMPLE_INSIGHTS.alternative("Lenen bij de buren of de uitleendienst")
    assert lend == EXAMPLE_INSIGHTS.alternatives[2]


def test_unknown_or_empty_name_gives_the_best_alternative():
    assert EXAMPLE_INSIGHTS.alternative("") == EXAMPLE_INSIGHTS.alternatives[0]
    assert EXAMPLE_INSIGHTS.alternative("bestaat niet") == EXAMPLE_INSIGHTS.alternatives[0]


def test_no_alternatives_gives_none():
    assert EXAMPLE_INSIGHTS.model_copy(update={"alternatives": []}).alternative("") is None


def test_rates_add_up_all_extra_costs():
    # €0,45 stroom + €1,75 water per keer, €8 onderhoud per jaar
    assert EXAMPLE_INSIGHTS.rates() == (2.20, 8)


def test_details_schema_is_strict_for_the_llm():
    schema = AlternativeDetails.model_json_schema()
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"steps", "pros", "cons"}


def test_details_prompt_names_the_product_and_the_alternative():
    lend = EXAMPLE_INSIGHTS.alternatives[2]
    text = insights.details_prompt("hogedrukreiniger", lend, 3)
    assert "Iemand wou dit kopen: hogedrukreiniger" in text
    assert "kiest nu voor dit alternatief: Lenen bij de buren" in text
    assert "Gebruik: 3 keer per jaar." in text
    # dezelfde prijs als op vraag 3, zodat de uitleg er niet van afwijkt
    assert "Prijsindicatie: gratis" in text


async def test_too_long_details_are_trimmed(monkeypatch):
    async def fake_ask(system, prompt, model):
        return AlternativeDetails(steps=["s"] * 6, pros=["p"] * 5, cons=["c"] * 5)

    monkeypatch.setattr(llm, "ask", fake_ask)
    found = await insights.alternative_details("x", EXAMPLE_INSIGHTS.alternatives[0], 3)
    assert (len(found.steps), len(found.pros), len(found.cons)) == (4, 3, 3)


def test_shop_types_come_with_belgian_examples():
    # zonder die uitleg dacht het model dat Inno (een warenhuis) wasmachines verkoopt
    text = insights.prompt("wasmachine")
    assert "department_store: warenhuis (Inno, HEMA)" in text
    assert "geen groot huishoudtoestel" in text


def test_advice_gets_renting_and_lending_but_not_another_product():
    # pitch: tuinslang (ander product) telt niet mee voor de regels, huren en lenen wel
    found = EXAMPLE_INSIGHTS.advice_alternatives(3, 4)
    assert [(alternative.name, alternative.kind) for alternative in found] == [
        ("Huren bij een verhuurder", "huren"),
        ("Lenen bij de buren of de uitleendienst", "lenen"),
    ]
    assert found[0].price == 25
    assert found[1].price == 0
    assert all(alternative.distance_km is None for alternative in found)


def test_subscription_is_spread_over_the_uses():
    # deelplatform €30 per jaar, 3 keer per jaar: €10 per keer
    sharing = EXAMPLE_INSIGHTS.model_copy(
        update={"alternatives": [suggestion("Deelplatform", kind="huren", per_year=30)]}
    )
    assert sharing.advice_alternatives(3, 4)[0].price == 10


def test_second_hand_counts_with_its_purchase_price():
    second = EXAMPLE_INSIGHTS.model_copy(
        update={"alternatives": [suggestion("Tweedehands", once=60, kind="tweedehands")]}
    )
    assert second.advice_alternatives(3, 4)[0].price == 60


async def test_shop_types_of_an_alternative_are_cleaned_up(monkeypatch):
    rack = suggestion("Droogrek", once=25).model_copy(
        update={"shop_types": ["houseware", "ruimteschip"]}
    )
    answer = EXAMPLE_INSIGHTS.model_copy(update={"alternatives": [rack]})

    async def fake_ask(system, prompt, model):
        return answer

    monkeypatch.setattr(llm, "ask", fake_ask)
    found = await insights.product_insights("droogkast")
    assert found.alternatives[0].shop_types == ["houseware"]


def test_prompt_knows_motorcycle_dealers():
    text = insights.prompt("motorfiets")
    assert "motorcycle: motorzaak of motordealer" in text
    assert "geef dan een lege lijst" in text


def test_everything_in_a_row_for_the_pitch():
    # 12 keer in 4 jaar: kopen €149 + €58,40 extra kosten = €207,40
    rows = [(o.kind, o.name, o.total, o.per_use) for o in EXAMPLE_INSIGHTS.options(149, 3, 4)]
    assert rows == [
        ("kopen", "Nieuw kopen", 207.40, 17.28),
        ("lenen", "Lenen bij de buren of de uitleendienst", 0, 0),
        ("ander", "Tuinslang met spuitstuk en een harde borstel", 25, 2.08),
        ("huren", "Huren bij een verhuurder", 300, 25),
        ("laten", "Niet kopen", 0, 0),
    ]


def test_buying_shows_the_exit_strategy_and_skipping_the_savings():
    options = EXAMPLE_INSIGHTS.options(149, 3, 4)
    assert options[0].note == EXAMPLE_INSIGHTS.exit_tip
    assert options[-1].note == "Je bespaart €207,40 en ± 40 kg CO2."
