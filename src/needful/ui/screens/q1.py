from nicegui import ui

from needful.ui.components import button, header, nav, screen
from needful.ui.storage import load_answers, save_answer

# key = de waarde die calc/advice.py verwachte, waarde = tekst op knop
CHOICES = {
    "concreet": "Ja, voor iets concreets",
    "handig": "Het zou handig zijn",
    "impuls": "Eerlijk? Ik wil het gewoon",
    "kapot": "Iets ging kapot",
}


@ui.page("/vraag/1")
def q1() -> None:
    answers = load_answers()
    with screen("vraag 1"):
        header(1)
        ui.label(answers.product).classes("nf-mono nf-muted")
        ui.html('Heb je dit <span class="nf-mark">écht</span> nodig?', tag="h1").classes("nf-h1")

        def choose(need: str) -> None:
            save_answer("need", need)
            ui.navigate.to("/vraag/2")

        with ui.column().classes("w-full gap-3"):
            for need, label in CHOICES.items():
                style = "nf-choice nf-selected" if need == answers.need else "nf-choice"
                # need=need: elke knop onthoudt zijn eigen  waarden (anders krijgen  ze allemaal de laatste)
                button(label, lambda need=need: choose(need), style).props("align=left").classes(
                    "w-full"
                )
        ui.label(
            "„Voor het terras, één keer in de lente.” → handig, niet nodig. "
            "Geen oordeel, we rekenen gewoon verder."
        ).classes("nf-tip w-full")
        nav(back="/", next_to="/vraag/2")
