"""Wat de schermen tonen als het taalmodel niet bereikbaar is (geen sleutel in .env, of een
fout): het pitchvoorbeeld, de hogedrukreiniger. Ook het advies rekent dan met deze alternatieven.
"""

from needful.alternatives.insights import ExtraCost, ProductInsights, Suggestion

EXAMPLE_INSIGHTS = ProductInsights(
    # stroom en water rekent calc/cost.py om: 1,5 kWh → €0,45, 350 liter → €1,75 per keer
    kwh_per_use=1.5,
    liters_per_use=350,
    extra_costs=[
        ExtraCost(name="Onderhoud", per_use=0, per_year=8, note="reinigingsmiddel, sproeikop"),
    ],
    alternatives=[
        Suggestion(
            name="Tuinslang met spuitstuk en een harde borstel",
            kind="ander",
            search_term="tuinslang",
            meaning="Een paar keer per jaar het terras schrobben: wat meer tijd en spierkracht, "
            "maar geen stroom en bijna geen onderhoud.",
            once=25,
            per_use=0,
            per_year=0,
            place="geen",
            shop_types=["doityourself", "garden_centre"],
        ),
        Suggestion(
            name="Huren bij een verhuurder",
            kind="huren",
            search_term="hogedrukreiniger",
            meaning="Een bouwmarkt of verhuurder verhuurt hem per dag. Wel ophalen, "
            "terugbrengen en op tijd reserveren in de lente.",
            once=0,
            per_use=25,
            per_year=0,
            place="geen",
            shop_types=[],
        ),
        Suggestion(
            name="Lenen bij de buren of de uitleendienst",
            kind="lenen",
            search_term="hogedrukreiniger",
            meaning="Voor 3 keer per jaar hoef je er geen te hebben: vraag rond in de straat of "
            "bij je gemeente. Wel even ophalen en terugbrengen.",
            once=0,
            per_use=0,
            per_year=0,
            place="geen",
            shop_types=[],
        ),
    ],
    co2_kg=40,
    exit_tip="Bewaar doos en bonnetje: verhuur hem aan je buren of verkoop hem na 4 jaar "
    "tweedehands.",
    shop_types=["doityourself", "hardware", "garden_centre"],
)
