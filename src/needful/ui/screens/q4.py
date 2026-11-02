"""Vraag 4: hoe duurzaam is het product? Vier criteria → score /100."""

from nicegui import ui

from needful.calc.score import durability_score
from needful.ui.components import header, nav, screen
from needful.ui.storage import load_answers, save_answer

# (veld in Answers, titel, voorbeelduitleg). De uitleg komt later uit reviews en specs.
CRITERIA = [
    ("lifespan", "Levensduur", "reviews: 6–8 jaar bij licht gebruik"),
    ("repairable", "Herstelbaar", "onderdelen beperkt leverbaar"),
    ("recyclable", "Recycleerbaar", "kunststof behuizing, geen take-back"),
    ("review", "Reviews", "4,3 / 5 · 1.280 beoordelingen"),
]
OPTIONS = {"ja": "✓ ja", "deels": "~ deels", "nee": "✗ nee"}


@ui.page("/vraag/4")
def q4() -> None:
    answers = load_answers()
    with screen("vraag 4"):
        header(4)
        ui.html("Hoe duurzaam is het product?", tag="h1").classes("nf-h1")
        ui.label("We zochten reviews en specs. Pas aan als je het beter weet.").classes("nf-body")

        toggles = {}
        with ui.column().classes("w-full gap-2"):
            for field, title, note in CRITERIA:
                with ui.column().classes("nf-row nf-card-line gap-1"):
                    ui.label(title).classes("font-bold")
                    ui.label(note).classes("text-sm nf-muted")
                    # getattr(answers, "lifespan") is hetzelfde als answers.lifespan
                    toggles[field] = (
                        ui.toggle(OPTIONS, value=getattr(answers, field))
                        .props("no-caps unelevated toggle-color=dark spread")
                        .classes("w-full")
                    )

        with ui.row().classes("items-baseline gap-3"):
            score = ui.label().classes("nf-big")
            ui.label("/100 · DUURZAAMHEIDSSCORE").classes("nf-mono nf-muted")

        def update() -> None:
            # * pakt de vier waarden uit als vier aparte argumenten
            score.text = str(durability_score(*(toggles[f].value for f, _, _ in CRITERIA)))

        def changed(field: str, value: str) -> None:
            save_answer(field, value)
            update()

        for field, toggle in toggles.items():
            # field=field: elke toggle onthoudt zijn eigen veld
            toggle.on_value_change(lambda e, field=field: changed(field, e.value))
        update()

        nav(back="/vraag/3", next_to="/advies", next_label="Toon mijn advies →", style="nf-yellow")
