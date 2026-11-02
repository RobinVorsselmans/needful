"""Resultaat: één advies, met de vergelijking en de reden erbij."""

import logging

from nicegui import ui

from needful.alternatives.examples import EXAMPLE_ALTERNATIVES
from needful.calc.advice import best, decide
from needful.calc.cost import cost_per_use
from needful.calc.format import euro, km
from needful.calc.score import durability_score
from needful.ui.components import button, logo, screen
from needful.ui.storage import load_answers
from needful.ui.theme import PAPER, YELLOW

log = logging.getLogger(__name__)


def compare_row(label: str, value: str, win: bool = False) -> None:
    """Eén regel in de vergelijking; het gekozen alternatief licht groen op."""
    with ui.row().classes("w-full justify-between no-wrap gap-3").classes(
        "nf-compare-win" if win else "nf-compare"
    ):
        ui.label(label)
        ui.label(value)


def feedback(useful: bool) -> None:
    log.info("feedback op advies: nuttig=%s", useful)
    ui.notify("Bedankt!")


@ui.page("/advies")
def advies() -> None:
    a = load_answers()
    log.debug("antwoorden: %s", a)
    score = durability_score(a.lifespan, a.repairable, a.recyclable, a.review)
    advice = decide(a.need, a.price, a.total_uses, EXAMPLE_ALTERNATIVES, score)
    # calc/ logt zelf niet; het geeft zijn redenering terug en wij loggen die hier
    for check in advice.checks:
        log.debug("regel %s: %s (%s)", check.rule, check.matched, check.why)
    log.info("advies: %s · %s", advice.outcome, advice.reason)

    with screen("advies", background=YELLOW):
        with ui.row().classes("w-full justify-between items-center"):
            logo(dot=PAPER)
            ui.label("JOUW ADVIES").classes("nf-mono")
        ui.label(
            f"{a.product} · {euro(a.price)} · {a.uses_per_year}×/jaar · {a.years} jaar"
        ).classes("nf-mono")
        ui.html(advice.headline, tag="h1").classes("nf-h1 nf-display")

        with ui.column().classes("w-full gap-2 nf-card-dark"):
            compare_row("Kopen", f"{euro(cost_per_use(a.price, a.uses_per_year, a.years))} /keer")
            # "if x := ...": maak x aan en ga verder als het iets is (geen None)
            if rent := best(EXAMPLE_ALTERNATIVES, "huren"):
                compare_row("Huren", f"{euro(rent.price)} /dag")
            if second := best(EXAMPLE_ALTERNATIVES, "tweedehands"):
                per_use = cost_per_use(second.price, a.uses_per_year, a.years)
                compare_row("Tweedehands", f"{euro(per_use)} /keer")
            if lend := best(EXAMPLE_ALTERNATIVES, "lenen"):
                compare_row(
                    f"Lenen · {lend.name}, {km(lend.distance_km)}",
                    euro(lend.price),
                    win=advice.outcome == "lenen",
                )

        with ui.row().classes("items-baseline gap-3"):
            if advice.savings > 0:
                ui.label(euro(advice.savings)).classes("nf-big")
                ui.label(f"bespaard · {score}/100 duurzaam").classes("font-medium")
            else:
                ui.label(f"{score}/100 duurzaam").classes("font-medium")
        ui.label(advice.reason).classes("nf-body")

        button("Toon uitleenpunten op kaart", lambda: ui.navigate.to("/vraag/3")).classes(
            "w-full"
        )
        button("Nieuwe vraag", lambda: ui.navigate.to("/"), "nf-choice").classes("w-full")

        ui.space()
        with ui.row().classes("w-full justify-between items-center"):
            ui.label("Was dit advies nuttig?")
            with ui.row().classes("gap-2"):
                for useful, icon, label in (
                    (True, "thumb_up", "Ja, nuttig"),
                    (False, "thumb_down", "Nee, niet nuttig"),
                ):
                    ui.button(
                        icon=icon, on_click=lambda useful=useful: feedback(useful), color=None
                    ).props(f'round outline aria-label="{label}"')
