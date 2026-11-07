"""Startscherm: product invullen en starten."""

from nicegui import ui

from needful.ui.components import button, logo, screen
from needful.ui.storage import start_new
from needful.ui.theme import INK, YELLOW


@ui.page("/")
def start() -> None:
    with screen("start", background=INK).classes("nf-on-dark"):
        with ui.row().classes("w-full justify-between items-center"):
            logo(dot=YELLOW)
            ui.label("PWA - NL").classes("nf-mono nf-faint")

        ui.space()
        ui.html('Koop minder.<br><span class="nf-mark">Kies beter.</span>', tag="h1").classes(
            "nf-h1 nf-display"
        )
        ui.label(
            "Drie eerlijke vragen, ± 3 minuten. Je ziet wat je aankoop écht kost per gebruik "
            "en of lenen of huren slimmer is."
        ).classes("nf-lead nf-soft")

        product = (
            ui.input("Wat wil je kopen", value="hogedrukreiniger")
            .props("outlined dark")
            .classes("w-full")
        )

        def go() -> None:
            start_new(product.value.strip() or "iets")
            ui.navigate.to("/vraag/1")

        button("Start →", go, "nf-yellow").classes("w-full")
        ui.space()

        with ui.row().classes("nf-mono nf-faint gap-4"):
            ui.label("✓ gratis")
            ui.label("✓ geen login")
            ui.label("✓ tik óf spreek")
