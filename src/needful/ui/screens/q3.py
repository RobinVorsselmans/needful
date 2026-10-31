"""Vraag 3: kan het anders in jouw buurt? Kaart en lijst zijn voorlopig voorbeelden."""

from nicegui import ui

from needful.alternatives.examples import EXAMPLE_ALTERNATIVES
from needful.calc.advice import Alternative
from needful.calc.format import euro, km
from needful.ui.components import header, nav, screen
from needful.ui.storage import load_answers, save_answer

# Waar de genummerde punten op de voorbeeldkaart staan: (links %, boven %)
SPOTS = [(16, 22), (64, 58), (28, 74), (80, 20)]


def price_text(alt: Alternative) -> str:
    """€0, €60 of €25/dag: huren is per dag, de rest eenmalig."""
    return euro(alt.price) + ("/dag" if alt.kind == "huren" else "")


def map_placeholder() -> None:
    """Grijs vlak met genummerde punten. De echte OpenStreetMap-kaart komt in sprint 3."""
    with ui.element("div").classes("nf-map"):
        ui.element("div").classes("nf-map-me")
        for number, (alt, (left, top)) in enumerate(zip(EXAMPLE_ALTERNATIVES, SPOTS), start=1):
            # De positie hangt af van de data, dus die blijft inline
            ui.label(str(number)).classes(f"nf-pin nf-pin-{alt.kind}").style(
                f"left: {left}%; top: {top}%"
            )
        ui.label("kaart · voorbeeld").classes("nf-mono nf-map-note")


@ui.page("/vraag/3")
def q3() -> None:
    answers = load_answers()
    with screen("vraag 3"):
        header(3)
        ui.html("Kan het anders in jouw buurt?", tag="h1").classes("nf-h1")

        postcode = ui.input("Postcode", value=answers.postcode).props("outlined").classes("w-full")
        # "blur" = je verlaat het veld: één logregel per wijziging, niet per letter
        postcode.on("blur", lambda: save_answer("postcode", postcode.value))

        map_placeholder()

        with ui.column().classes("w-full gap-2"):
            for number, alt in enumerate(EXAMPLE_ALTERNATIVES, start=1):
                row_classes = f"nf-row nf-row-{alt.kind} justify-between items-center no-wrap"
                with ui.row().classes(row_classes):
                    with ui.column().classes("gap-0"):
                        ui.label(f"{number} · {alt.name}").classes("font-bold")
                        ui.label(f"{alt.kind} · {km(alt.distance_km)}").classes("text-sm")
                    ui.label(price_text(alt)).classes("font-bold text-lg")

        nav(back="/vraag/2", next_to="/vraag/4")
