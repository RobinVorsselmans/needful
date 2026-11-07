"""In jouw buurt: postcode + gemeente → adressen per soort (nieuw kopen, tweedehands, huren,
lenen, herstellen, alternatieven). Wat we zoeken en tonen, hangt af van je keuze op vraag 3:
bij "Zet alles op een rij" alles (het product én al zijn alternatieven), bij een gekozen droogrek
enkel winkels met droogrekken, bij "lenen of huren" enkel huren en lenen. Het taalmodel kijkt na
of de tags voor dít product kloppen. Zie alternatives/nearby.py en alternatives/relevance.py."""

from dataclasses import dataclass, field

from nicegui import ui

from needful.alternatives import nearby, relevance
from needful.alternatives.insights import ProductInsights, Suggestion
from needful.calc.format import km
from needful.flow.answers import Answers
from needful.ui.components import (
    button,
    chosen_names,
    example_note,
    logo,
    options_overview,
    screen,
    waiting,
)
from needful.ui.storage import load_answers, load_insights, save_answer

# ?terug=... mag enkel naar onze eigen schermen (anders kan een link je overal naartoe sturen)
BACK = ("/advies",)

# titel per soort plaats; de volgorde komt uit nearby.TAGS
SECTIONS = {
    "kopen": "Nieuw kopen",
    "tweedehands": "Tweedehands",
    "huren": "Huren",
    "lenen": "Lenen",
    "herstellen": "Herstellen",
    "alternatief": "Alternatieven",
}


@dataclass(frozen=True)
class Focus:
    """Wat we in de buurt zoeken en tonen, volgens je keuze op vraag 3."""

    subject: str  # waar de teksten over gaan: "droogkast", of het gekozen "droogrek"
    shop_types: list[str]  # winkels waar het subject nieuw ligt (tag "kopen")
    alternative_places: list[str]  # soorten plaatsen voor een alternatief, bv. ["wassalon"]
    alternative_shops: list[str]  # winkels voor een ander product, bv. ["houseware"] (droogrek)
    alternatives: list[Suggestion]  # wat het nakijken als alternatief mag herkennen
    tags: tuple[nearby.Tag, ...]  # welke groepen we tonen, in deze volgorde
    second_hand: list[str]  # zoekwoorden voor de knoppen naar 2dehands
    titles: dict[str, str] = field(default_factory=dict)  # andere titel voor een groep


# Kies je uitdrukkelijk een tweedehands alternatief, dan tonen we ook de gewone verkooppunten:
# een motordealer verkoopt vaak (niet altijd) occasies, maar OpenStreetMap noteert dat zelden.
ASK_SECOND_HAND = {"kopen": "Verkooppunten · vraag naar tweedehands"}


def unique(terms: list[str]) -> list[str]:
    return list({term.strip().lower(): term.strip() for term in terms if term.strip()}.values())


def focus(answers: Answers, insights: ProductInsights) -> Focus:
    product, alternatives = answers.product, insights.alternatives
    chosen = insights.alternative(answers.alternative) if answers.choice == "alternatief" else None
    if chosen is not None and chosen.kind == "ander":
        # een ander product (droogrek): zoek dát, in de winkels die erbij horen
        term = chosen.search_term or chosen.name
        return Focus(term, chosen.shop_types, [], [], [], ("kopen", "tweedehands"), [term])
    if chosen is not None and chosen.kind == "tweedehands":
        term = chosen.search_term or product
        tags = ("tweedehands", "kopen")
        return Focus(term, insights.shop_types, [], [], [], tags, [term], ASK_SECOND_HAND)
    if chosen is not None or answers.choice == "delen":
        # huren of lenen: het product (ook winkels die verhuren) en die alternatieven (wassalon)
        sharing = [chosen] if chosen else [a for a in alternatives if a.kind in ("huren", "lenen")]
        places = [a.place for a in sharing]
        tags = ("huren", "lenen", "alternatief")
        return Focus(product, insights.shop_types, places, [], sharing, tags, [])
    if answers.choice == "nieuw":
        return Focus(product, insights.shop_types, [], [], [], ("kopen",), [])
    if answers.choice == "tweedehands":
        # "van mij, maar tweedehands mag" = nieuw én tweedehands: allebei zoeken en tonen
        terms = [product] + [a.search_term for a in alternatives if a.kind == "tweedehands"]
        return Focus(
            product, insights.shop_types, [], [], [], ("kopen", "tweedehands"), unique(terms)
        )
    # alles op een rij: het product én al zijn alternatieven
    shops = sorted({shop for a in alternatives if a.kind == "ander" for shop in a.shop_types})
    # alles wat je in de plaats zou kunnen kopen (geen wassalon of uitleendienst)
    terms = [product] + [a.search_term for a in alternatives if a.kind in ("ander", "tweedehands")]
    places = [a.place for a in alternatives]
    return Focus(
        product, insights.shop_types, places, shops, alternatives, nearby.TAGS, unique(terms)
    )


def place_row(place: nearby.Place) -> None:
    with ui.column().classes("nf-row nf-card-line gap-1"):
        with ui.row().classes("w-full justify-between no-wrap gap-3"):
            ui.link(place.name, place.url, new_tab=True).classes("font-bold nf-link")
            ui.label(km(place.distance_km)).classes("text-sm nf-muted")
        ui.label(place.address or "adres niet bekend, zie de link").classes("text-sm")
        with ui.row().classes("gap-1"):
            for tag in place.tags:
                ui.label(tag).classes(f"nf-tag nf-tag-{tag}")


@ui.page("/buurt")
async def buurt(terug: str = BACK[0]) -> None:
    answers = load_answers()
    back = terug if terug in BACK else BACK[0]
    with screen("buurt"):
        with ui.row().classes("w-full justify-between items-center"):
            logo()
            ui.label("IN JOUW BUURT").classes("nf-mono nf-muted")
        subject_label = ui.label(answers.product).classes("nf-mono nf-muted")
        ui.html("Waar kan het in jouw buurt?", tag="h1").classes("nf-h1")

        # alles op een rij met de prijzen komt van het taalmodel, dus pas na het verbinden
        overview = ui.column().classes("w-full")
        with overview:
            waiting("Het taalmodel zet je mogelijkheden op een rij…")

        with ui.row().classes("w-full no-wrap gap-2"):
            postcode = ui.input("Postcode", value=answers.postcode).props("outlined")
            gemeente = ui.input("Gemeente", value=answers.gemeente).props("outlined")
            postcode.classes("w-28")
            gemeente.classes("flex-grow")
        second_hand = ui.column().classes("w-full gap-2")  # knoppen naar 2dehands, na het laden
        results = ui.column().classes("w-full gap-3")

        def show(
            target: Focus,
            places: list[nearby.Place],
            failed: list[str],
            unchecked: bool,
            status: str | None,
        ) -> None:
            """De groepen tot nu toe. `status`: waarmee we nog bezig zijn, None als alles klaar is."""
            results.clear()
            with results:
                # enkel de soorten die bij je keuze horen, in de volgorde van die keuze
                found = nearby.grouped(places)
                groups = {tag: found[tag] for tag in target.tags if tag in found}
                if not groups and status is None:
                    ui.label(f"Niets gevonden binnen {km(nearby.RADIUS_KM)}.").classes("nf-body")
                for tag, group in groups.items():
                    with ui.row().classes("items-center gap-2"):
                        ui.label(target.titles.get(tag, SECTIONS[tag])).classes("font-bold")
                        ui.label(str(len(group))).classes(f"nf-tag nf-tag-{tag}")
                    for place in group:
                        place_row(place)
                if status is not None:
                    waiting(status)
                if unchecked:
                    ui.label(
                        f"Niet nagekeken op {target.subject}: het taalmodel is niet bereikbaar."
                    ).classes("text-sm nf-muted")
                if failed:
                    ui.label(f"Geen antwoord van {', '.join(failed)}.").classes("text-sm nf-muted")

        async def search() -> None:
            save_answer("postcode", postcode.value.strip())
            save_answer("gemeente", gemeente.value.strip())
            results.clear()
            with results:
                waiting(
                    f"We zoeken waar je in {gemeente.value.strip() or 'je buurt'} terecht kunt…"
                )
            origin = await nearby.geocode(postcode.value.strip(), gemeente.value.strip())
            if origin is None:
                results.clear()
                with results:
                    ui.label("We vinden die plaats niet. Klopt de postcode?").classes("nf-body")
                return
            # wat en waar we zoeken (welke winkels, welke alternatieven) weet het taalmodel
            insights, _ = await load_insights(answers.product)
            target = focus(answers, insights)
            places: list[nearby.Place] = []
            failed: list[str] = []
            done: list[str] = []
            unchecked = False

            def still_busy() -> str:
                pending = ", ".join(source for source in nearby.SOURCES if source not in done)
                return f"Nog aan het zoeken bij {pending}. Dat kan tot een halve minuut duren."

            show(target, places, failed, unchecked, still_busy())
            # elke bron verschijnt zodra ze klaar én nagekeken is
            async for source, found in nearby.search(
                origin, target.shop_types, target.alternative_places, target.alternative_shops
            ):
                done.append(source)
                if found is None:
                    failed.append(source)
                else:
                    what = (
                        f"{target.subject} en de alternatieven"
                        if answers.choice == "alles"
                        else target.subject
                    )
                    show(target, places, failed, unchecked, f"We kijken na wat bij {what} past…")
                    checked = await relevance.check_places(
                        target.subject, found, target.alternatives
                    )
                    unchecked = unchecked or checked is None
                    places += found if checked is None else checked
                busy = still_busy() if len(done) < len(nearby.SOURCES) else None
                show(target, places, failed, unchecked, busy)
            show(target, places, failed, unchecked, None)

        button("Zoek een verkoop- of huurpunt", search).classes("w-full")
        ui.label(
            "Data: © OpenStreetMap-bijdragers (ODbL) en repaircafe.org · tweedehands: 2dehands.be"
        ).classes("nf-mono nf-muted")

        ui.space()
        button("Nieuwe vraag", lambda: ui.navigate.to("/"), "nf-choice").classes("w-full")
        ui.link("← Terug", back).classes("nf-back")

    await ui.context.client.connected()
    insights, example = await load_insights(answers.product)
    target = focus(answers, insights)
    if target.subject != answers.product:
        subject_label.text = f"{target.subject} · alternatief voor {answers.product}"
    options = insights.options(answers.price, answers.uses_per_year, answers.years)
    overview.clear()
    with overview:
        if answers.choice == "alles":
            options_overview(options, answers, compact=True)
        elif shown := [o for o in options if o.name in chosen_names(answers, options)]:
            # geen lege kaart als je keuze geen eigen regel heeft (bv. tweedehands zonder voorstel)
            options_overview(shown, answers, compact=True, title="JOUW KEUZE")
        if example:
            example_note()
    with second_hand:
        for term in target.second_hand:
            # term=term: elke knop onthoudt zijn eigen zoekwoord; de link wordt pas bij het
            # klikken gemaakt, met de postcode die er dan staat
            button(
                f"Bekijk tweedehands {term} op 2dehands ↗",
                lambda term=term: ui.navigate.to(
                    nearby.second_hand_url(term, postcode.value.strip()), new_tab=True
                ),
                "nf-choice",
            ).classes("w-full")
