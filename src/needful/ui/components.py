"""Bouwstenen die op meerdere schermen terugkomen."""

import logging
from collections.abc import Callable
from typing import Any

from nicegui import ui

from needful.alternatives.insights import AlternativeDetails, Option, ProductInsights, Suggestion
from needful.calc.cost import buying_pays_off_from
from needful.calc.format import euro, price_text
from needful.flow.answers import Answers
from needful.ui.theme import GOLD, INK, LINE, PAPER, apply_theme

log = logging.getLogger(__name__)

QUESTIONS = 3

# hoe elke soort mogelijkheid heet op het scherm; de kleur komt uit nf-tag-<soort> (theme.py)
OPTION_LABELS = {
    "kopen": "nieuw",
    "tweedehands": "tweedehands",
    "huren": "huren",
    "lenen": "lenen",
    "ander": "ander product",
    "laten": "niet kopen",
}


def screen(name: str, background: str = PAPER) -> ui.column:
    """Thema toepassen, het bezoek loggen en de smalle kolom maken voor het scherm."""
    log.info("scherm geopend: %s", name)
    apply_theme(background)
    return ui.column().classes("nf-frame")


def logo(dot: str = GOLD) -> None:
    ui.html(f'needful<span style="color: {dot}">.</span>').classes("text-xl font-bold")


def header(step: int) -> None:
    """Logo, 'VRAAG n/4' en de voortgangsbalk."""
    with ui.row().classes("w-full justify-between items-center"):
        logo()
        ui.label(f"VRAAG {step}/{QUESTIONS}").classes("nf-mono nf-muted")
    with ui.grid(columns=QUESTIONS).classes("w-full gap-1.5"):
        for i in range(1, QUESTIONS + 1):
            # Kleur hangt af van de stap, dus die blijft inline (maar wel als constante)
            color = INK if i <= step else LINE
            ui.element("div").classes("nf-bar").style(f"background: {color}")


def example_note() -> None:
    """Labeltje onder iets van het taalmodel, als we het pitchvoorbeeld tonen."""
    ui.label("voorbeeld · taalmodel niet bereikbaar").classes("nf-mono nf-muted")


def waiting(text: str) -> None:
    """Spinner mét uitleg: wie ziet waarop we wachten en hoe lang het duurt, haakt minder af."""
    with ui.row().classes("w-full items-center no-wrap gap-3"):
        ui.spinner(size="md")
        ui.label(text).classes("text-sm nf-muted")


def alternative_card(
    alternative: Suggestion,
    answers: Answers,
    buy_total: float,
    on_choose: Callable[[], Any] | None = None,
    chosen: bool = False,
) -> None:
    """Eén alternatief: naam, prijsindicatie, wat het betekent, en wat het kost over dezelfde
    gebruiksduur als kopen (`buy_total` = nieuwprijs + extra kosten). Met `on_choose` komt er
    een knop "Kies dit alternatief" onder (vraag 3); `chosen` maakt die knop zwart."""
    with ui.column().classes("w-full gap-1"):
        with ui.row().classes("w-full justify-between no-wrap gap-3"):
            ui.label(alternative.name).classes("font-bold")
            price = price_text(alternative.once, alternative.per_use, alternative.per_year)
            ui.label(price if price == "gratis" else f"± {price}").classes(
                "text-sm font-bold text-right"
            )
        ui.label(alternative.meaning).classes("text-sm")
        total = alternative.total_cost(answers.uses_per_year, answers.years)
        ui.label(
            f"{answers.total_uses} keer in {answers.years} jaar: {euro(total)} · "
            f"kopen: {euro(buy_total)}"
        ).classes("text-sm font-medium")
        if on_choose is not None:
            style = "nf-choice nf-selected" if chosen else "nf-choice"
            button("Kies dit alternatief →", on_choose, style).classes("nf-btn-sm w-full")


def alternative_verdict(
    alternative: Suggestion, answers: Answers, insights: ProductInsights
) -> None:
    """Wat het alternatief jou oplevert tegenover kopen, en vanaf wanneer kopen toch loont."""
    per_use, per_year = insights.rates()
    buy_total = answers.price + insights.extra_cost(answers.uses_per_year, answers.years)
    difference = buy_total - alternative.total_cost(answers.uses_per_year, answers.years)
    if difference > 0:
        ui.label(f"Je bespaart {euro(difference)} tegenover kopen.").classes("font-bold")
    else:
        ui.label(f"Kopen is {euro(-difference)} goedkoper.").classes("font-bold")
    pays_off = buying_pays_off_from(
        answers.price,
        per_use,
        per_year,
        alternative.once,
        alternative.per_use,
        alternative.per_year,
        answers.years,
    )
    if pays_off is None:
        text = "Hoe vaak je het ook gebruikt: het alternatief blijft goedkoper."
    else:
        text = (
            f"Zelf kopen loont vanaf {pays_off} keer per jaar; "
            f"jij rekent op {answers.uses_per_year} keer."
        )
    ui.label(text).classes("text-sm")


def options_overview(
    options: list[Option],
    answers: Answers,
    advised: str | None = None,
    chosen: tuple[str, ...] = (),
    compact: bool = False,
    title: str = "ALLES OP EEN RIJ",
) -> None:
    """Mogelijkheden op een rij: per mogelijkheid de soort, de naam en wat het kost over je
    gebruiksduur. `advised` is de naam die de adviesregels aanraden, `chosen` wat je op
    vraag 3 koos. `compact` laat de uitleg weg (in de buurt), behalve wat je bespaart."""
    with ui.column().classes("w-full gap-3 nf-card-dark"):
        ui.label(f"{title} · {answers.total_uses} KEER IN {answers.years} JAAR").classes("nf-mono")
        for option in options:
            with ui.column().classes("w-full gap-0"):
                with ui.row().classes("w-full justify-between items-center no-wrap gap-3"):
                    with ui.row().classes("items-center no-wrap gap-2"):
                        ui.label(OPTION_LABELS[option.kind]).classes(f"nf-tag nf-tag-{option.kind}")
                        ui.label(option.name).classes("font-bold")
                    total = (
                        "gratis"
                        if option.total == 0 and option.kind != "laten"
                        else euro(option.total)
                    )
                    ui.label(total).classes("font-bold text-right")
                if option.kind == "laten":
                    ui.label(option.note).classes("text-sm")
                else:
                    line = f"{euro(option.per_use)} per keer" if option.per_use else "gratis"
                    if option.note and not compact:
                        line += f" · {option.note}"
                    ui.label(line).classes("text-sm nf-soft")
                with ui.row().classes("gap-3"):
                    if option.name == advised:
                        ui.label("★ ONS ADVIES").classes("nf-mono nf-advised")
                    if option.name in chosen:
                        ui.label("JOUW KEUZE").classes("nf-mono nf-chosen")


def chosen_names(answers: Answers, options: list[Option]) -> tuple[str, ...]:
    """Wat je op vraag 3 koos, als namen uit "Alles op een rij". Leeg bij "Zet alles op een rij".
    "Van mij, maar tweedehands mag" = nieuw én tweedehands: allebei jouw keuze."""
    if answers.choice == "alternatief":
        return (answers.alternative,)
    kinds = {
        "nieuw": ("kopen",),
        "tweedehands": ("kopen", "tweedehands"),
        "delen": ("huren", "lenen"),
    }.get(answers.choice, ())
    return tuple(option.name for option in options if option.kind in kinds)


def details_list(title: str, items: list[str], mark: str) -> None:
    """'HOE BEGIN JE ERAAN' met de stappen eronder, elk met een teken ervoor (1., +, –)."""
    ui.label(title).classes("nf-mono")
    for number, item in enumerate(items, start=1):
        ui.label(f"{number}. {item}" if mark == "1." else f"{mark} {item}").classes("text-sm")


def show_details(details: AlternativeDetails | None) -> None:
    """De verdere uitleg van het taalmodel over een gekozen alternatief."""
    if details is None:
        ui.label("Meer uitleg komt van het taalmodel, dat nu niet bereikbaar is.").classes(
            "text-sm nf-muted"
        )
        return
    details_list("HOE BEGIN JE ERAAN", details.steps, "1.")
    details_list("VOORDELEN", details.pros, "+")
    details_list("LET OP", details.cons, "–")


def button(text: str, on_click: Callable[[], Any], style: str = "nf-dark") -> ui.button:
    """Knop in de huisstijl. style: nf-dark, nf-yellow of nf-choice."""
    return (
        ui.button(text, on_click=on_click, color=None)
        .props("unelevated no-caps")
        .classes(f"nf-btn {style}")
    )


def nav(
    back: str,
    next_to: str = "",
    next_label: str = "Volgende →",
    style: str = "nf-dark",
    on_next: Callable[[], Any] | None = None,
) -> None:
    """Onderste rij: '← Terug' links, volgende-knop rechts. Duwt zichzelf naar onder.
    Met `on_next` doet de knop dat in plaats van naar `next_to` te gaan (bv. eerst bewaren)."""
    ui.space()
    with ui.row().classes("w-full justify-between items-center"):
        ui.link("← Terug", back).classes("nf-back")
        button(next_label, on_next or (lambda: ui.navigate.to(next_to)), style).classes("nf-btn-sm")
