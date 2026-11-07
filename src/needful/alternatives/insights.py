"""Wat het taalmodel weet over een product: extra kosten om mee rekening te houden (vraag 2),
alternatieven met een prijsindicatie (vraag 3 en de buurt), CO2 en een exit-strategie
(vraag 4) en in welke winkels het nieuw ligt.

Eén vraag per product; de UI bewaart het antwoord per browser (zie ui/storage.py).
"""

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict

from needful.alternatives import llm
from needful.alternatives.nearby import ALTERNATIVE_PLACES, SHOP_TYPES, AlternativePlace
from needful.calc.advice import Alternative
from needful.calc.cost import energy_cost, extra_cost, total_cost, total_uses, water_cost
from needful.calc.format import euro, kg, kwh, liters, price_text

# extra="forbid" maakt het schema strikt: het LLM mag geen velden weglaten of bijverzinnen
STRICT = ConfigDict(extra="forbid")
MAX_EXTRA_COSTS = 4
MAX_ALTERNATIVES = 3

# lenen = gratis (of bijna) gebruiken, huren = per keer betalen (ook een dienst zoals een
# wassalon), tweedehands = een gebruikt exemplaar kopen, ander = een ander product kopen
SuggestionKind = Literal["lenen", "huren", "tweedehands", "ander"]
# een mogelijkheid in "Alles op een rij": de soorten hierboven, plus nieuw kopen en niet kopen
OptionKind = Literal["kopen", "lenen", "huren", "tweedehands", "ander", "laten"]


@dataclass(frozen=True)
class Option:
    """Eén mogelijkheid in "Alles op een rij": wat het is en wat het kost over je gebruiksduur."""

    kind: OptionKind
    name: str
    total: float  # euro over de hele gebruiksduur
    per_use: float  # dat totaal gedeeld door het aantal keer
    note: str  # wat het betekent, de exit-strategie, of wat je bespaart


class ExtraCost(BaseModel):
    model_config = STRICT

    name: str  # "Stroom"
    per_use: float  # euro per keer dat je het gebruikt
    per_year: float  # euro per jaar, los van hoe vaak
    note: str  # korte uitleg, bv. "± 1,5 kWh per beurt"


class Suggestion(BaseModel):
    """Een alternatief: een ander product, een dienst (wassalon) of een manier (huren, lenen)."""

    model_config = STRICT

    name: str  # "Wassalon"
    kind: SuggestionKind  # zo weet het advies of het bij huren, lenen … hoort
    search_term: str  # het ding zelf in een paar woorden, zoals op 2dehands: "droogrek"
    meaning: str  # wat het in de praktijk betekent en waarom het slimmer is
    # prijsindicatie in euro; wat niet geldt, staat op 0
    once: float  # eenmalig, bv. een tuinslang
    per_use: float  # per keer, bv. een wasbeurt of een huurdag
    per_year: float  # per jaar, bv. een abonnement
    place: AlternativePlace  # welke soort plaats we ervoor in de buurt zoeken, of "geen"
    shop_types: list[str]  # bij een ander product: waar het nieuw ligt, zie SHOP_TYPES

    def total_cost(self, uses_per_year: int, years: int) -> float:
        """Wat het alternatief kost over dezelfde gebruiksduur als kopen."""
        return total_cost(self.once, self.per_use, self.per_year, uses_per_year, years)


class ProductInsights(BaseModel):
    model_config = STRICT

    # stroom en water als hoeveelheid: het LLM schat die beter dan het rekent (zie calc/cost.py)
    kwh_per_use: float
    liters_per_use: float
    extra_costs: list[ExtraCost]  # alle andere extra kosten, al in euro
    alternatives: list[Suggestion]  # 1 tot 3, het beste eerst
    co2_kg: float  # het maken van één nieuw exemplaar, in kg CO2-equivalent
    exit_tip: str
    shop_types: list[str]  # OpenStreetMap shop=..., zie SHOP_TYPES

    def costs(self) -> list[ExtraCost]:
        """Stroom en water (door ons omgerekend naar euro) plus de andere extra kosten."""
        usage = [
            ExtraCost(
                name="Stroom",
                per_use=energy_cost(self.kwh_per_use),
                per_year=0,
                note=f"± {kwh(self.kwh_per_use)} per keer",
            ),
            ExtraCost(
                name="Water",
                per_use=water_cost(self.liters_per_use),
                per_year=0,
                note=f"± {liters(self.liters_per_use)} per keer",
            ),
        ]
        return [cost for cost in usage if cost.per_use > 0] + self.extra_costs

    def rates(self) -> tuple[float, float]:
        """Alle extra kosten samen: (euro per keer, euro per jaar)."""
        costs = self.costs()
        return sum(cost.per_use for cost in costs), sum(cost.per_year for cost in costs)

    def extra_cost(self, uses_per_year: int, years: int) -> float:
        """Alle extra kosten samen over de hele gebruiksduur."""
        return extra_cost(*self.rates(), uses_per_year, years)

    def advice_alternatives(self, uses_per_year: int, years: int) -> list[Alternative]:
        """De alternatieven in de vorm die de adviesregels (calc/advice.py) verwachten.

        Huren en lenen krijgen hun prijs per keer, met een abonnement erin verrekend; tweedehands
        de aankoopprijs. Een ander product (droogrek) kennen de regels nog niet: dat toont het
        adviesscherm apart. Een afstand kennen we niet (None)."""
        uses = max(total_uses(uses_per_year, years), 1)
        found = []
        for suggestion in self.alternatives:
            if suggestion.kind == "ander":
                continue
            if suggestion.kind == "tweedehands":
                price = suggestion.once
            else:
                price = round(suggestion.total_cost(uses_per_year, years) / uses, 2)
            found.append(Alternative(suggestion.name, suggestion.kind, None, price))
        return found

    def options(self, price: float, uses_per_year: int, years: int) -> list[Option]:
        """Alles op een rij: nieuw kopen, dan de alternatieven van goedkoop naar duur, en als
        laatste niet kopen. Elk met wat het kost over dezelfde gebruiksduur."""
        uses = max(total_uses(uses_per_year, years), 1)
        buy = round(price + self.extra_cost(uses_per_year, years), 2)
        buying = Option("kopen", "Nieuw kopen", buy, round(buy / uses, 2), self.exit_tip)
        others = []
        for suggestion in self.alternatives:
            total = suggestion.total_cost(uses_per_year, years)
            others.append(
                Option(
                    suggestion.kind,
                    suggestion.name,
                    total,
                    round(total / uses, 2),
                    suggestion.meaning,
                )
            )
        others.sort(key=lambda option: option.total)
        skip = Option(
            "laten", "Niet kopen", 0, 0, f"Je bespaart {euro(buy)} en ± {kg(self.co2_kg)} CO2."
        )
        return [buying, *others, skip]

    def alternative(self, name: str) -> Suggestion | None:
        """Het alternatief met deze naam (gekozen op vraag 3), anders het beste, anders None."""
        named = [alternative for alternative in self.alternatives if alternative.name == name]
        return (named or self.alternatives or [None])[0]


class AlternativeDetails(BaseModel):
    """Verder ingaan op het gekozen alternatief (vraag 4): hoe begin je eraan, wat win je."""

    model_config = STRICT

    steps: list[str]  # 2 tot 4 concrete stappen
    pros: list[str]  # 2 of 3 voordelen
    cons: list[str]  # 1 tot 3 nadelen of aandachtspunten


SYSTEM = (
    "Je bent een nuchtere Vlaamse consumentenadviseur. Je antwoordt kort, in het Nederlands, "
    "met realistische bedragen in euro voor België. Schatten mag, overdrijven niet. "
    "Je verstaat Belgisch-Nederlands: een droogkast is een wasdroger."
)


def shop_lines(shops: dict[str, str]) -> str:
    """'   - doityourself: doe-het-zelfzaak (Brico, Gamma, Hubo) …', één regel per winkeltype."""
    return "\n".join(f"   - {shop}: {about}" for shop, about in shops.items())


def prompt(product: str) -> str:
    return f"""Iemand overweegt dit te kopen: {product[:80]}

1. kwh_per_use en liters_per_use: hoeveel stroom (kWh) en leidingwater (liter) één gebruik
   verbruikt, 0 als het er geen gebruikt. Enkel de hoeveelheid; de prijs rekenen wij zelf.
   extra_costs: hoogstens {MAX_EXTRA_COSTS} andere extra kosten om mee rekening te houden
   bovenop de aankoopprijs, zoals verbruiksmateriaal, onderhoud of verzekering, in euro. Geen
   stroom of water (die staan al hierboven), geen aankoopprijs of afschrijving. Wat bij elk
   gebruik terugkomt (verbruiksmateriaal) staat altijd in per_use, per keer; per_year is enkel
   voor wat los staat van hoe vaak je het gebruikt (onderhoud, verzekering, abonnement). Zet
   het andere op 0. Zijn er geen andere extra kosten, geef dan een lege lijst.
2. alternatives: 1 tot {MAX_ALTERNATIVES} slimmere, goedkopere of duurzamere alternatieven, het
   beste eerst, enkel wat een gewone Vlaming echt zou overwegen. Dat mag een ander product zijn
   (een tuinslang en borstel in plaats van een hogedrukreiniger), een dienst (een wassalon in
   plaats van een wasmachine) of een manier zoals huren of lenen. Per alternatief:
   - kind: lenen (gratis of bijna gratis van iemand anders gebruiken), huren (per keer of per
     dag betalen, ook voor een dienst zoals een wassalon), tweedehands (een gebruikt exemplaar
     kopen) of ander (een ander product kopen).
   - search_term: het ding zelf in 1 tot 3 woorden, zoals je het op 2dehands zou zoeken
     (bv. "droogrek"; voor een wassalon: "wassalon").
   - meaning: wat het in de praktijk betekent (tijd, verplaatsing, gemak) en waarom het
     slimmer is, hoogstens 30 woorden.
   - een prijsindicatie in euro: once (eenmalig), per_use (per keer dat je het gebruikt) en
     per_year (per jaar). Zet wat niet geldt op 0; alles op 0 betekent gratis.
   - place: welke soort plaats je ervoor in de buurt zoekt. Kies uit:
     {", ".join(ALTERNATIVE_PLACES)}. Past geen enkele, kies dan "geen".
   - shop_types: bij kind "ander": in welke soorten winkels dat product nieuw te koop is
     (uit de lijst bij punt 5); anders een lege lijst.
3. co2_kg: geschatte CO2-uitstoot in kg CO2-equivalent van het maken van één nieuw exemplaar.
4. exit_tip: als je het toch koopt, hoe deel je het of raak je het later kwijt (doorverkopen,
   verhuren, uitlenen)? Eén zin.
5. shop_types: in welke soorten winkels het in België echt nieuw te koop is. Kies 1 tot 3 uit
   deze lijst, en kies er liever minder dan een die het zelden heeft. Staat het juiste soort
   winkel er niet bij, geef dan een lege lijst (geen ander type dat er maar wat op lijkt):
{shop_lines(SHOP_TYPES)}"""


def positive(*amounts: float) -> bool:
    return all(amount >= 0 for amount in amounts)


async def product_insights(product: str) -> ProductInsights | None:
    """Vraag het LLM; None als dat niet lukt (de UI toont dan het voorbeeld)."""
    found = await llm.ask(SYSTEM, prompt(product), ProductInsights)
    if found is None:
        return None
    # het LLM kan zich vergissen: enkel positieve bedragen, niet te veel, en winkeltypes die we kennen
    costs = [cost for cost in found.extra_costs if positive(cost.per_use, cost.per_year)]
    alternatives = [
        alternative.model_copy(
            update={"shop_types": [s for s in alternative.shop_types if s in SHOP_TYPES]}
        )
        for alternative in found.alternatives
        if positive(alternative.once, alternative.per_use, alternative.per_year)
    ]
    return found.model_copy(
        update={
            "kwh_per_use": max(found.kwh_per_use, 0),
            "liters_per_use": max(found.liters_per_use, 0),
            "extra_costs": costs[:MAX_EXTRA_COSTS],
            "alternatives": alternatives[:MAX_ALTERNATIVES],
            "shop_types": [shop for shop in found.shop_types if shop in SHOP_TYPES],
        }
    )


def details_prompt(product: str, alternative: Suggestion, uses_per_year: int) -> str:
    return f"""Iemand wou dit kopen: {product[:80]}
Die persoon kiest nu voor dit alternatief: {alternative.name}
Wat het betekent: {alternative.meaning}
Prijsindicatie: {price_text(alternative.once, alternative.per_use, alternative.per_year)}
(gebruik die prijs ook in je antwoord)
Gebruik: {uses_per_year} keer per jaar.

Ga verder in op dit alternatief, concreet voor iemand in België:
1. steps: 2 tot 4 stappen om ermee te beginnen (waar zoeken, wat regelen, wat meenemen),
   elk hoogstens 15 woorden.
2. pros: 2 of 3 voordelen voor deze persoon, elk hoogstens 12 woorden.
3. cons: 1 tot 3 nadelen of punten om op te letten, elk hoogstens 12 woorden."""


async def alternative_details(
    product: str, alternative: Suggestion, uses_per_year: int
) -> AlternativeDetails | None:
    """Tweede LLM-vraag, enkel als iemand een alternatief kiest; None als het niet lukt."""
    found = await llm.ask(
        SYSTEM, details_prompt(product, alternative, uses_per_year), AlternativeDetails
    )
    if found is None:
        return None
    return AlternativeDetails(steps=found.steps[:4], pros=found.pros[:3], cons=found.cons[:3])
