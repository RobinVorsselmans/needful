"""Vraag 3, de laatste: moet het per se nieuw en van jou? Met alternatieven van het taalmodel
(niet altijd goedkoper), elk met een prijsindicatie en wat het kost tegenover kopen.

Hier beslis je ook: elk antwoord, een alternatief of "Zet alles op een rij" gaat naar het
advies. Het advies (en de buurt) toont wat bij je keuze hoort; bij "Zet alles op een rij" alle
mogelijkheden met hun prijs."""

from nicegui import ui

from needful.ui.components import (
    alternative_card,
    button,
    example_note,
    header,
    nav,
    screen,
    waiting,
)
from needful.ui.storage import load_answers, load_insights, save_answer

# key = Choice in flow/answers.py, waarde = tekst op knop
CHOICES = {
    "nieuw": "Ja, nieuw en van mij",
    "tweedehands": "Van mij, maar tweedehands mag",
    "delen": "Nee, lenen of huren is ook goed",
    "alles": "Zet alles op een rij",
}


@ui.page("/vraag/3")
async def q3() -> None:
    answers = load_answers()
    with screen("vraag 3"):
        header(3)
        ui.html('Moet het per se <span class="nf-mark">nieuw</span> en van jou?', tag="h1").classes(
            "nf-h1"
        )

        with ui.column().classes("nf-tip w-full gap-1"):
            ui.label("ALTERNATIEVEN").classes("nf-mono")
            tip = ui.column().classes("w-full gap-3")
            with tip:
                waiting("Het taalmodel zoekt alternatieven…")

        def choose(choice: str, alternative: str = "") -> None:
            """Bewaren en naar het advies. Een alternatief = het hoeft niet nieuw en van jou
            te zijn; het advies gaat er dan verder op in."""
            save_answer("choice", choice)
            save_answer("alternative", alternative)
            ui.navigate.to("/advies")

        with ui.column().classes("w-full gap-3"):
            for choice, label in CHOICES.items():
                style = "nf-choice nf-selected" if choice == answers.choice else "nf-choice"
                # choice=choice: elke knop onthoudt zijn eigen waarde
                button(label, lambda choice=choice: choose(choice), style).props(
                    "align=left"
                ).classes("w-full")
        # houdt de keuze die er al staat (standaard: alles op een rij)
        nav(back="/vraag/2", next_to="/advies", next_label="Toon mijn advies →", style="nf-yellow")

    await ui.context.client.connected()
    insights, example = await load_insights(answers.product)
    buy_total = answers.price + insights.extra_cost(answers.uses_per_year, answers.years)
    tip.clear()
    with tip:
        if not insights.alternatives:
            ui.label("Geen alternatief gevonden.").classes("nf-body")
        for alternative in insights.alternatives:
            chosen = answers.choice == "alternatief" and answers.alternative == alternative.name
            # name=...: elke knop onthoudt zijn eigen alternatief
            alternative_card(
                alternative,
                answers,
                buy_total,
                lambda name=alternative.name: choose("alternatief", name),
                chosen,
            )
        if example:
            example_note()
