"""Rekenkern: pure Python, geen I/O, volledig getest.

Voorbeeld uit de pitch: €149 · 3× per jaar · 4 jaar → €12,42 per gebruik.
Met de extra kosten erbij (stroom, water, onderhoud: €58,40) → €17,28 per gebruik.
"""

import math

# Richtprijzen voor Vlaanderen (schatting 2025–2026), pas aan als ze niet meer kloppen.
# Het LLM schat enkel kWh en liters; omrekenen naar euro doen wij, want daar vergist het zich.
EURO_PER_KWH = 0.30
EURO_PER_M3_WATER = 5.0  # met saneringsbijdrage


def energy_cost(kwh: float) -> float:
    """Stroom per gebruik in euro. Pitch: 1,5 kWh → €0,45."""
    return round(kwh * EURO_PER_KWH, 2)


def water_cost(liters: float) -> float:
    """Leidingwater per gebruik in euro. Pitch: 350 liter → €1,75."""
    return round(liters / 1000 * EURO_PER_M3_WATER, 2)


def total_uses(uses_per_year: int, years: int) -> int:
    """Totaal aantal gebruiken."""
    return uses_per_year * years


def cost_per_use(price: float, uses_per_year: int, years: int) -> float:
    """Kost per gebruik in euro, afgerond op 2 cijfers."""
    if price <= 0:
        raise ValueError("prijs moet groter zijn dan 0")
    uses = total_uses(uses_per_year, years)
    if uses <= 0:
        raise ValueError("aantal gebruiken moet groter zijn dan 0")
    return round(price / uses, 2)


def total_cost(
    once: float, per_use: float, per_year: float, uses_per_year: int, years: int
) -> float:
    """Wat iets kost over de hele gebruiksduur: eenmalig + per keer × aantal keer
    + per jaar × aantal jaar, afgerond op 2 cijfers. Pitch, wassalon van €6 per keer → €72."""
    return round(once + per_use * total_uses(uses_per_year, years) + per_year * years, 2)


def extra_cost(per_use: float, per_year: float, uses_per_year: int, years: int) -> float:
    """Extra kosten om mee rekening te houden over de hele gebruiksduur: wat per keer kost
    (stroom, water) plus wat per jaar kost (onderhoud, verzekering)."""
    return total_cost(0, per_use, per_year, uses_per_year, years)


def real_cost_per_use(price: float, extra: float, uses_per_year: int, years: int) -> float:
    """Kost per gebruik mét de extra kosten erbij."""
    return cost_per_use(price + extra, uses_per_year, years)


def buying_pays_off_from(
    price: float,
    buy_per_use: float,
    buy_per_year: float,
    alt_once: float,
    alt_per_use: float,
    alt_per_year: float,
    years: int,
) -> int | None:
    """Vanaf hoeveel keer per jaar is zelf kopen goedkoper dan het alternatief?

    Kopen kost vooraf meer (de nieuwprijs), het alternatief kost vaak meer per keer. Vanaf een
    bepaald aantal keer per jaar haalt kopen dat in. None: kopen wordt nooit goedkoper, want
    het alternatief kost per keer niet meer. Wasmachine €600 + €0,79 per keer + €15 per jaar
    tegenover een wassalon van €7 per keer, over 4 jaar → vanaf 27 keer per jaar.
    """
    more_per_use = alt_per_use - buy_per_use  # wat het alternatief per keer méér kost
    if more_per_use <= 0:
        return None
    head_start = price - alt_once + (buy_per_year - alt_per_year) * years  # kopen vooraf méér
    if head_start <= 0:
        return 1
    # het kleinste aantal keer per jaar waarbij kopen écht goedkoper is
    return math.floor(head_start / (more_per_use * years)) + 1
