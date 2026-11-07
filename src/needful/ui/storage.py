"""Antwoorden bewaren per browser, in NiceGUI's app.storage.user.
blijft bewaard bij herladen en werkt met de terugknop van de telefoon

Ook het antwoord van het taalmodel staat hier, zodat vraag 2, 3, 4 en het advies
samen maar één LLM-vraag per product kosten.
"""

import logging
from typing import Any

from nicegui import app
from pydantic import ValidationError

from needful.alternatives.examples import EXAMPLE_INSIGHTS
from needful.alternatives.insights import (
    AlternativeDetails,
    ProductInsights,
    Suggestion,
    alternative_details,
    product_insights,
)
from needful.flow.answers import Answers

log = logging.getLogger(__name__)

KEY = "answers"
INSIGHTS = "insights"
DETAILS = "details"


def start_new(product: str) -> None:
    """Nieuwe vraag: alle antwoorden terug naar het vb, met dit product."""
    app.storage.user[KEY] = Answers(product=product).to_dict()
    # ook een nieuwe LLM-vraag, zodat een mislukte vraag een tweede kans krijgt
    app.storage.user.pop(INSIGHTS, None)
    app.storage.user.pop(DETAILS, None)
    log.info("nieuwe vraag gestart: product=%r", product)


async def load_insights(product: str) -> tuple[ProductInsights, bool]:
    """Wat het taalmodel over het product weet, één keer per product gevraagd en dan bewaard.
    Geeft ook terug of het het voorbeeld is (geen sleutel, of het LLM faalde)."""
    cached = app.storage.user.get(INSIGHTS)
    if cached and cached["product"] == product:
        if cached["data"] is None:
            return EXAMPLE_INSIGHTS, True
        try:
            return ProductInsights.model_validate(cached["data"]), False
        except ValidationError:
            # bewaard door een oudere versie van ProductInsights: opnieuw vragen
            log.info("bewaard LLM-antwoord heeft een oude vorm, opnieuw gevraagd")
    found = await product_insights(product)
    app.storage.user[INSIGHTS] = {"product": product, "data": found.model_dump() if found else None}
    return (found, False) if found else (EXAMPLE_INSIGHTS, True)


async def load_details(
    product: str, alternative: Suggestion, uses_per_year: int
) -> AlternativeDetails | None:
    """Meer uitleg over het gekozen alternatief, één keer per product en alternatief gevraagd.
    Een mislukte vraag bewaren we niet, zodat ze de volgende keer opnieuw kan."""
    key = f"{product}|{alternative.name}"
    saved = dict(app.storage.user.get(DETAILS, {}))
    if key in saved:
        try:
            return AlternativeDetails.model_validate(saved[key])
        except ValidationError:
            log.info("bewaarde uitleg heeft een oude vorm, opnieuw gevraagd")
    found = await alternative_details(product, alternative, uses_per_year)
    if found is not None:
        saved[key] = found.model_dump()
        app.storage.user[DETAILS] = saved
    return found


def load_answers() -> Answers:
    answers, missing = Answers.from_dict(app.storage.user.get(KEY, {}))
    if missing:
        log.warning("antwoorden ontbreken, voorbeeldwaarden gebruikt voor: %s", ", ".join(missing))
    return answers


def save_answer(field: str, value: Any) -> None:
    """een kopie terugzetten,  zodat NiceGUI ziet dat er iets veranderd werd en het opslaat."""
    data = dict(app.storage.user.get(KEY, {}))
    data[field] = value
    app.storage.user[KEY] = data
    log.info("antwoord opgeslagen: %s=%r", field, value)
