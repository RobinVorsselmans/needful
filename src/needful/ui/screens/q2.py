"""Vraag 2: hoe vaak ga je het gebruiken"""

import logging

from nicegui import ui

from needful.calc.cost import cost_per_use
from needful.calc.format import euro
from needful.ui.components import header, nav, screen
from needful.ui.storage import load_answers, save_answer

log = logging.getLogger(__name__)


@ui.page("/vraag/2")
def q2() -> None:
    answers = load_answers()
    with screen("vraag 2"):
        header(2)
        ui.html("Hoe vaak ga je het gebruiken?", tag="h1").classes("nf-h1")

        with ui.column().classes("w-full items-center gap-6 py-3"):
            ui.button(icon="mic", color=None).props("round unelevated disable").classes(
                "nf-mic"
            ).tooltip("Spraak komt in sprint 4")
            ui.label("spraak komt later - typ hieronder").classes("nf-mono nf-muted")

        with ui.column().classes("w-full gap-3"):
            uses = ui.number("Gebruik per jaar", value=answers.uses_per_year, min=1, precision=0)
            years = ui.number("Aantal jaar", value=answers.years, min=1, precision=0)
            price = ui.number("Nieuwprijs (€)", value=answers.price, min=0.01, precision=2)
            for field in (uses, years, price):
                field.props("outlined").classes("w-full")

        result = ui.label().classes("text-xl font-bold")

        def update() -> None:
            # veld kan leeg zijn als je typt
            if None in (uses.value, years.value, price.value):
                result.text = "= - per gebruik"
                return
            try:
                value = cost_per_use(price.value, int(uses.value), int(years.value))
            except ValueError as error:
                log.warning("ongeldige invoer op vraag 2: %s", error)
                result.text = "= - per gebruik"
                return
            result.text = f"= {euro(value)} per gebruik"

        def save(field: str, value: float | None, cast: type) -> None:
            if value is not None:
                save_answer(field, cast(value))
            update()

        uses.on_value_change(lambda e: save("uses_per_year", e.value, int))
        years.on_value_change(lambda e: save("years", e.value, int))
        price.on_value_change(lambda e: save("price", e.value, float))
        update()

        nav(back="/vraag/1", next_to="/vraag/3", next_label="Klopt →")
