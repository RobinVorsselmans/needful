"""Antwoorden bewaren per browser, in NiceGUI's app.storage.user.
blijft bewaard bij herladen en werkt met de terugknop van de telefoon
"""

import logging
from typing import Any

from nicegui import app

from needful.flow.answers import Answers

log = logging.getLogger(__name__)

KEY = "answers"


def start_new(product: str) -> None:
    """Nieuwe vraag: alle antwoorden terug naar het vb, met dit product."""
    app.storage.user[KEY] = Answers(product=product).to_dict()
    log.info("nieuwe vraag gestart: product=%r", product)


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
