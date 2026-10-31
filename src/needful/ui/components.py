import logging
from collections.abc import Callable

from nicegui import ui

from needful.ui.theme import GOLD, INK, LINE, MUTED, PAPER, apply_theme

log = logging.getLogger(__name__)

QUESTIONS = 4


def screen(name: str, background: str = PAPER) -> ui.column:
    """Thema toepassen,  het bezoek loggen en de smalle kolom maken voor het scherm."""
    log.info("scherm geopend: %s", name)
    apply_theme(background)
    return ui.column().classes("nf-frame")


def logo(dot: str = GOLD) -> None:
    ui.html(f'needful<span style="color: {dot}">.</span>').classes("text-xl font-bold")


def header(step: int) -> None:
    """Logo, vraag n/4 en de voortgangsbalk."""
    with ui.row().classes("w-full justify-between items-center"):
        logo()
        ui.label(f"VRAAG {step} / {QUESTIONS}").classes("nf-mono").style(f"color: {MUTED}")
    with ui.grid(columns=QUESTIONS).classes("w-full gap-1.5"):
        for i in range(1, QUESTIONS + 1):
            color = INK if i <= step else LINE
            ui.element("div").style(f"height: 6px; border-radius: 3px; background: {color}")


def button(text: str, on_click: Callable[[], None], style: str = "nf-dark") -> ui.button:
    """Knop in de huisstijl. style: nf)dark, nf)yellow of nf-choice"""
    return (
        ui.button(text, on_click=on_click, color=None)
        .props("unelevated no-caps")
        .classes(f"nf-btn {style}")
    )


def nav(back: str, next_to: str, next_label: str = "Volgende →", style: str = "nf-dark") -> None:
    """onderste rij: "<- Terug" links,  volgende-kno rechts, Duwt zichzelf n aar onder."""
    ui.space()
    with ui.row().classes("w-full justify-between items-center"):
        ui.link("← Terug", back).classes("nf-back")
        button(next_label, lambda: ui.navigate.to(next_to), style).style(
            "min-height: 48px; font-size: 16px; border-radius: 12px"
        )
