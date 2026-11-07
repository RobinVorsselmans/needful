"""Past deze plaats bij het product? OpenStreetMap weet welk soort winkel iets is, niet wat er in
de rekken ligt: Oxfam (shop=charity) verkoopt geen wasmachines, Boels (shop=rental) verhuurt er
geen. Het taalmodel kijkt de gevonden plaatsen na en mag tags enkel weghalen, nooit bijverzinnen.
"""

import logging
import re
from dataclasses import replace

from pydantic import BaseModel

from needful.alternatives import llm
from needful.alternatives.insights import STRICT, Suggestion, shop_lines
from needful.alternatives.nearby import OTHER_SHOPS, SHOP_TYPES, Place, Tag

log = logging.getLogger(__name__)

MAX_CHECK = 40  # de dichtste 40 nakijken: genoeg om er na het filteren 25 over te houden


class PlaceCheck(BaseModel):
    model_config = STRICT

    id: int  # het nummer van de plaats in de lijst van de prompt
    # eerst de reden, dan de tags: zo denkt het model na vóór het beslist (en wij zien waarom)
    reason: str
    tags: list[Tag]


class PlaceChecks(BaseModel):
    model_config = STRICT

    places: list[PlaceCheck]


SYSTEM = (
    "Je kent Belgische winkels, ketens en diensten. Je beoordeelt per plaats of iemand er dít "
    "product echt kan kopen, huren, lenen, tweedehands vinden of laten herstellen. Je bent "
    "streng: heeft zo'n plaats het product zelden of nooit, dan krijgt ze geen tag. "
    "Je verstaat Belgisch-Nederlands: een droogkast is een wasdroger."
)

SHOPS = SHOP_TYPES | OTHER_SHOPS


def legend(places: list[Place]) -> str:
    """Uitleg bij de winkeltypes die in de lijst voorkomen, met Belgische ketens."""
    shops = {shop for place in places for shop in re.findall(r"shop=(\w+)", place.about)}
    return shop_lines({shop: SHOPS[shop] for shop in sorted(shops) if shop in SHOPS})


def prompt(product: str, places: list[Place], alternatives: list[Suggestion]) -> str:
    lines = "\n".join(
        f"{number}. {place.name} ({place.about or place.source}) · tags: {', '.join(place.tags)}"
        for number, place in enumerate(places, start=1)
    )
    names = ", ".join(alternative.name for alternative in alternatives) or "geen"
    return f"""Iemand zoekt in de buurt naar: {product[:80]}
Alternatieven: {names}

Wat de soorten winkels in België meestal verkopen:
{legend(places)}

Hieronder plaatsen met de tags die wij afleidden uit het soort plaats. De tags betekenen:
kopen = je kunt er dit product nieuw kopen, huren = je kunt het er huren, lenen = je kunt het er
lenen, tweedehands = je kunt het er tweedehands kopen, herstellen = ze herstellen het er,
alternatief = je kunt er een van de alternatieven kopen of gebruiken.

Kijk naar wat zo'n winkel of keten echt verkoopt, niet enkel naar het soort winkel: een
kringwinkel met van alles kan het hebben, een wereldwinkel, kledingzaak of boekenwinkel meestal
niet; een gsm-winkel of kassasystemen-zaak is geen elektrozaak.

Geef voor elke plaats (id = het nummer) eerst een reden van hoogstens 8 woorden, dan enkel de
tags die voor dit product echt kloppen. Voeg geen tags toe die er niet staan. Klopt er geen
enkele, geef dan een lege lijst.

{lines}"""


def apply(places: list[Place], checks: PlaceChecks) -> list[Place]:
    """Enkel wat het taalmodel bevestigt, blijft over. Een tag die wij niet hadden, telt niet:
    het taalmodel kan weghalen, niet bijverzinnen."""
    confirmed = {check.id: set(check.tags) for check in checks.places}
    kept = []
    for number, place in enumerate(places, start=1):
        tags = tuple(tag for tag in place.tags if tag in confirmed.get(number, set()))
        if tags:
            kept.append(replace(place, tags=tags))
    return kept


async def check_places(
    product: str, places: list[Place], alternatives: list[Suggestion]
) -> list[Place] | None:
    """De plaatsen die passen, met enkel de tags die kloppen. None als het taalmodel niet
    antwoordt: dan toont het scherm de plaatsen zoals ze zijn, met een melding."""
    if not places:
        return []
    candidates = sorted(places, key=lambda place: place.distance_km)[:MAX_CHECK]
    checks = await llm.ask(SYSTEM, prompt(product, candidates, alternatives), PlaceChecks)
    if checks is None:
        return None
    for check in checks.places:
        log.debug("plaats %s: %s → %s", check.id, check.reason, check.tags)
    return apply(candidates, checks)
