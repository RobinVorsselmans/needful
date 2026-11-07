"""Resultaat: één advies, met wat bij je keuze op vraag 3 hoort.

Koos je "Zet alles op een rij", dan staan alle mogelijkheden er met hun prijs: nieuw kopen, de
alternatieven en niet kopen. Bij een andere keuze vergelijken we je keuze met nieuw kopen en met
wat de regels aanraden; bij een alternatief gaan we er verder op in.

Het advies rekent met de alternatieven van het taalmodel voor dít product (of het voorbeeld):
bij een droogkast is "huren" dus de wassalon, niet een verhuurder van €25 per dag.
"""

import logging

from nicegui import ui

from needful.calc.advice import Alternative, Outcome, allowed, best, decide
from needful.calc.format import euro
from needful.ui.components import (
    alternative_verdict,
    button,
    chosen_names,
    example_note,
    logo,
    options_overview,
    screen,
    show_details,
    waiting,
)
from needful.ui.storage import load_answers, load_details, load_insights
from needful.ui.theme import PAPER, YELLOW

log = logging.getLogger(__name__)

# welke soort alternatief bij welk advies hoort (de rest: nieuw kopen)
ADVISED_KIND = {"lenen": "lenen", "huren": "huren", "kopen & doorverkopen": "tweedehands"}


def advised_name(outcome: Outcome, alternatives: list[Alternative]) -> str:
    """Welke regel in "Alles op een rij" de adviesregels aanraden."""
    if outcome == "laten":
        return "Niet kopen"
    kind = ADVISED_KIND.get(outcome)
    if kind and (alternative := best(alternatives, kind)):
        return alternative.name
    return "Nieuw kopen"


def feedback(useful: bool) -> None:
    log.info("feedback op advies: nuttig=%s", useful)
    ui.notify("Bedankt!")


@ui.page("/advies")
async def advies() -> None:
    a = load_answers()
    log.debug("antwoorden: %s", a)

    with screen("advies", background=YELLOW):
        with ui.row().classes("w-full justify-between items-center"):
            logo(dot=PAPER)
            ui.label("JOUW ADVIES").classes("nf-mono")
        ui.label(
            f"{a.product} · {euro(a.price)} · {a.uses_per_year}×/jaar · {a.years} jaar"
        ).classes("nf-mono")
        # het advies hangt af van de alternatieven van het taalmodel, dus pas na het verbinden
        body = ui.column().classes("w-full gap-5")
        with body:
            waiting("We zetten je advies klaar…")

        button("Zoek in mijn buurt", lambda: ui.navigate.to("/buurt?terug=/advies")).classes(
            "w-full"
        )
        button("Nieuwe vraag", lambda: ui.navigate.to("/"), "nf-choice").classes("w-full")
        ui.link("← Terug", "/vraag/3").classes("nf-back")

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

    await ui.context.client.connected()
    insights, example = await load_insights(a.product)
    # vraag 3: moet het nieuw of van jou zijn, dan tellen lenen en huren niet mee
    alternatives = allowed(insights.advice_alternatives(a.uses_per_year, a.years), a.access)
    advice = decide(a.need, a.price, a.total_uses, alternatives)
    # calc/ logt zelf niet; het geeft zijn redenering terug en wij loggen die hier
    for check in advice.checks:
        log.debug("regel %s: %s (%s)", check.rule, check.matched, check.why)
    log.info(
        "advies: %s · %s · keuze: %s %s", advice.outcome, advice.reason, a.choice, a.alternative
    )

    options = insights.options(a.price, a.uses_per_year, a.years)
    alternative = insights.alternative(a.alternative) if a.choice == "alternatief" else None
    deep: ui.column | None = None
    body.clear()
    with body:
        ui.html(advice.headline, tag="h1").classes("nf-h1 nf-display")
        if advice.savings > 0:
            with ui.row().classes("items-baseline gap-3"):
                ui.label(euro(advice.savings)).classes("nf-big")
                ui.label("bespaard").classes("font-medium")
        ui.label(advice.reason).classes("nf-body")

        advised = advised_name(advice.outcome, alternatives)
        chosen = chosen_names(a, options)
        if a.choice == "alles":
            options_overview(options, a, advised)
        else:
            # je keuze naast nieuw kopen (om te vergelijken) en wat de regels aanraden
            names = {"Nieuw kopen", advised, *chosen}
            shown = [option for option in options if option.name in names]
            options_overview(shown, a, advised, chosen, title="VERGELIJKING")
        if example:
            example_note()

        # koos je op vraag 3 een alternatief, dan gaan we er hier verder op in
        if alternative is not None:
            with ui.column().classes("nf-tip w-full gap-2"):
                ui.label("JOUW KEUZE").classes("nf-mono")
                ui.label(alternative.name).classes("font-bold")
                alternative_verdict(alternative, a, insights)
                deep = ui.column().classes("w-full gap-1")
                with deep:
                    waiting("Het taalmodel zoekt uit hoe je hieraan begint…")
                ui.link("Een ander alternatief kiezen", "/vraag/3").classes("nf-link text-sm")

    if deep is not None and alternative is not None:
        details = await load_details(a.product, alternative, a.uses_per_year)
        if not deep.is_deleted:
            deep.clear()
            with deep:
                show_details(details)
