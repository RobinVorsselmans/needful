"""NiceGUI-pagina's. Nu enkel een startscherm; de vragenwizard komt in sprint 2."""

from nicegui import ui


@ui.page("/")
def index() -> None:
    with ui.column().classes("w-full max-w-md mx-auto p-6 gap-4"):
        ui.label("needful.").classes("text-3xl font-bold")
        ui.label("Koop minder. Kies beter.").classes("text-lg")
        product = ui.input("Wat wil je kopen?", placeholder="bv. hogedrukreiniger").classes(
            "w-full"
        )
        ui.button(
            "Start",
            on_click=lambda: ui.notify(f"Vragenflow voor '{product.value}' komt in sprint 2"),
        )
