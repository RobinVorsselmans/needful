"""Adviesbepaling: antwoorden -> 1 uitkomst met een reden, pure pytohn geen I/O.

regels in volgorde, de eerste die past wint"""

from dataclasses import dataclass
from typing import Literal

from needful.calc.format import euro, km

Need = Literal["concreet", "handig", "impuls", "kapot"]
Kind = Literal["lenen", "huren", "tweedehands"]
Outcome = Literal["laten", "lenen", "huren", "kopen & doorverkopen", "bewust kopen"]

LEND_MAX_KM = 2.0  # verder dan dit gaan we niet lene
OWN_FROM_USES = 24  # gebruiken we het meer dan dit, dan is het zelf hebben het waard


@dataclass(frozen=True)
class Alternative:
    name: str
    kind: Kind
    distance_km: float
    price: float  # lenen=0, huren=per dag, tweedehands=eenmaling


@dataclass(frozen=True)
class RuleCheck:
    rule: str
    matched: bool
    why: str


@dataclass(frozen=True)
class Advice:
    outcome: Outcome
    headline: str
    reason: str
    savings: float  # bespaarde euries
    checks: list[RuleCheck]


def best(alternatives: list[Alternative], kind: Kind) -> Alternative | None:
    "cheapste alternatief van deze soort; bij gelijke prijs het dichtsbijzijnde."
    options = [alternative for alternative in alternatives if alternative.kind == kind]
    return min(
        options, key=lambda alternative: (alternative.price, alternative.distance_km), default=None
    )


def decide(
    need: Need,
    price: float,
    total_uses: int,
    alternatives: list[Alternative],
    score: int,
) -> Advice:
    checks: list[RuleCheck] = []
    rarely = total_uses <= OWN_FROM_USES

    # 1 - impulsaankoop -> laten
    impulse = need == "impuls"
    checks.append(RuleCheck("impuls", impulse, f"behoefte is {need!r}"))
    if impulse:
        return Advice(
            "laten",
            "Laat het even liggen.",
            "Je wilt het vooral, je hebt het niet echt nodig."
            "Wacht een maand en kijk of je het dan nog wilt.",
            price,
            checks,
        )

    # 2 gratis lenen  dichtbij, en je gebruikt het weinig -> lenen
    lend = best(alternatives, "lenen")
    free_nearby = lend is not None and lend.price == 0 and lend.distance_km <= LEND_MAX_KM
    checks.append(
        RuleCheck(
            "lenen",
            free_nearby and rarely,
            f"gratis lenen binnen {km(LEND_MAX_KM)}: {free_nearby},"
            f"{total_uses} keer <= {OWN_FROM_USES}: {rarely}",
        )
    )
    if free_nearby and rarely:
        return Advice(
            "lenen",
            "Lenen is de slimste keuze.",
            f"Je gebruikt het  {total_uses} keer. "
            f"{lend.name} leent het gratis uit op {km(lend.distance_km)}.",
            price,
            checks,
        )

    # 3 huren is goedkoper dan nieuw kopen -> huren
    rent = best(alternatives, "huren")
    rent_total = rent.price * total_uses if rent else None
    cheaper_to_rent = rent_total is not None and rent_total < price
    checks.append(
        RuleCheck("huren", cheaper_to_rent, f"huren in totaal{rent_total} vs nieuw {price}")
    )
    if cheaper_to_rent:
        return Advice(
            "huren",
            "Huren is de slimste keuze.",
            f"{total_uses} keer huren bij {rent.name} kost {euro(rent_total)}, "
            f"minder dan {euro(price)} nieuw.",
            price - rent_total,
            checks,
        )

    # 4 tweedehands is goedkoper en je gebruikt het niet vaak -> kopen en doorverkopen
    second = best(alternatives, "tweedehands")
    cheaper_second = second is not None and second.price < price
    checks.append(
        RuleCheck(
            "tweedehands",
            cheaper_second and rarely,
            f"tweedehands goedkoper: {cheaper_second}, "
            f"{total_uses} keer =< {OWN_FROM_USES}: {rarely}",
        )
    )
    if cheaper_second and rarely:
        return Advice(
            "kopen & doorverkopen",
            "Koop tweedehands, verkoop later door.",
            f"Je gebruikt het {total_uses} keer. Tweedehands kost het {euro(second.price)}"
            "en je kunt het daarna weer verkopen.",
            price - second.price,
            checks,
        )

    # 5 · niets anders past → bewust kopen
    checks.append(RuleCheck("bewust kopen", True, "geen andere regel paste"))
    return Advice(
        "bewust kopen",
        "Kopen kan, maar kies bewust.",
        f"Je gebruikt het {total_uses} keer en de duurzaamheidsscore is {score}/100. "
        "Kies een model dat je kunt laten herstellen.",
        0,
        checks,
    )
