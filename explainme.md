# Explain me

Uitleg bij de code en de structuur van needful., zodat we allemaal kunnen uitleggen wat er gebeurt en waarom.
Dit is een aanvulling op de docstrings en commentaren in de code, geen vervanging.

> **Onderhoud:** voeg bij elke gemergede feature een stukje toe of pas het aan. Staat er iets in dat niet meer klopt, verbeter het in dezelfde PR.
> Dit document beschrijft de staat van **1 november 2026** (sprint 2: vragenwizard klikbaar). Delen die nog niet bestaan staan onder [Nog te bouwen](#nog-te-bouwen).

## Inhoud

1. [Het idee in één alinea](#1-het-idee-in-één-alinea)
2. [Hoe de onderdelen samenhangen](#2-hoe-de-onderdelen-samenhangen)
3. [Map voor map](#3-map-voor-map)
4. [Bestand voor bestand](#4-bestand-voor-bestand)
5. [Een request van begin tot eind](#5-een-request-van-begin-tot-eind)
6. [Waarom deze keuzes](#6-waarom-deze-keuzes)
7. [Configuratie en omgeving](#7-configuratie-en-omgeving)
8. [Tests](#8-tests)
9. [Nog te bouwen](#nog-te-bouwen)
10. [Woordenlijst](#woordenlijst)
11. [Vragen die we kunnen krijgen](#vragen-die-we-kunnen-krijgen)

---

## 1. Het idee in één alinea

needful. is een beslissingshulp vóór je iets koopt. De gebruiker beantwoordt vier vragen (heb je het nodig, hoe vaak gebruik je het, kan het anders in je regio, hoe duurzaam is het) en krijgt één advies: laten, lenen, huren, samen kopen, alternatief product, kopen & later doorverkopen of bewust kopen. Geen login en geen persoonsgegevens.

## 2. Hoe de onderdelen samenhangen

```
 Browser / telefoon (PWA)
          │
          ▼
 ┌──────────────────────────┐
 │  ui/   NiceGUI-schermen  │  wat de gebruiker ziet
 └────────────┬─────────────┘
              │ roept aan
              ▼
 ┌──────────────────────────┐        ┌──────────────────────────┐
 │  api/  FastAPI-routes    │───────▶│  flow/  vragen & volgorde │
 └────────────┬─────────────┘        └──────────────────────────┘
              │
      ┌───────┼────────────────┬─────────────────┐
      ▼       ▼                ▼                 ▼
   calc/   alternatives/     voice/            db/
  rekenen  LLM + scraping   spraak → tekst   PostgreSQL
 (pure fn)  per regio                         (admin + cache)
```

De pijlen laten zien wie wie mag kennen. Belangrijkste regel: **`calc/` kent niemand anders**. Het is pure Python zonder netwerk, database of UI, dus het is makkelijk te testen en te begrijpen.

Er draait maar **één proces**: een FastAPI-app waar NiceGUI op is geplakt. De UI en de API zitten dus in dezelfde server op poort 8080.

## 3. Map voor map

| Map | Doel | Status |
|-----|------|--------|
| `src/needful/` | De Python-package met alle code | bestaat |
| `src/needful/calc/` | Rekenkern: kost per gebruik, score /100, advies, getalnotatie | `cost.py`, `score.py`, `advice.py`, `format.py` |
| `src/needful/api/` | HTTP-endpoints (FastAPI) | `/health`, `/cost-per-use` |
| `src/needful/ui/` | NiceGUI: huisstijl, bouwstenen, opslag en de zes schermen | wizard klikbaar, PWA nog niet |
| `src/needful/flow/` | De antwoorden van één gebruiker | `answers.py` |
| `src/needful/alternatives/` | Alternatieven zoeken via LLM en scraping | vaste voorbeelden (`examples.py`) |
| `src/needful/voice/` | Spraak omzetten naar antwoorden | leeg (docstring) |
| `src/needful/db/` | Database-modellen, admin-module, cache | leeg (docstring) |
| `src/needful/logging_setup.py` | Logformaat en -niveau voor de hele app | klaar |
| `tests/` | pytest-tests, ook klikt-door-de-app-tests | 38 tests |
| `docs/concept/` | Pitch en voorontwerp (pdf) | bestaat |

De `src/`-layout (code in `src/needful/` en niet direct in de root) voorkomt dat je per ongeluk code importeert uit de werkmap in plaats van uit het geïnstalleerde package.

## 4. Bestand voor bestand

### `src/needful/calc/cost.py`

Bevat twee functies:

- `total_uses(uses_per_year, years)`: hoe vaak je het in totaal gebruikt. Dit is de **enige** plek waar die vermenigvuldiging staat; `cost_per_use`, de API-route en `Answers` gebruiken allemaal deze functie.
- `cost_per_use(price, uses_per_year, years)`:

- Berekent `prijs ÷ (gebruiken per jaar × jaren)` en rondt af op 2 decimalen.
- Voorbeeld uit de pitch: €149, 3× per jaar, 4 jaar → 12 gebruiken → **€12,42 per gebruik**.
- Geeft een `ValueError` bij een prijs ≤ 0 of als het totaal aantal gebruiken ≤ 0 is. De rekenkern weigert dus zelf ongeldige input en vertrouwt niet op de aanroeper.

Waarom dit de kern is: "je koopt iets van €149 dat je 12 keer gebruikt" is het sterkste argument van de app. Het getal moet dus kloppen en getest zijn.

### `src/needful/api/routes.py`

Definieert een `APIRouter` met twee endpoints. Ze komen onder `/api` te staan (zie `main.py`).

| Endpoint | Doet |
|----------|------|
| `GET /api/health` | Geeft `{"status": "ok"}`. Handig om te checken of de server draait (ook voor Docker/hosting). |
| `POST /api/cost-per-use` | Neemt `price`, `uses_per_year`, `years` en geeft `cost_per_use` en `total_uses` terug. |

Twee Pydantic-modellen beschrijven de data:

- `CostRequest`: de input. `Field(gt=0)` betekent "groter dan 0". Pydantic controleert dat automatisch en FastAPI stuurt bij fouten zelf een `422`-antwoord terug.
- `CostResponse`: de vorm van het antwoord. `response_model=CostResponse` zorgt dat de API-docs en het antwoord altijd die vorm hebben.

De route zelf (`cost`) doet bijna niets: hij roept `cost_per_use` aan en pakt het resultaat in. **De logica zit in `calc/`, de route is alleen de poort naar buiten.** Houd dat zo bij nieuwe endpoints.

`total_uses` in het antwoord komt uit `calc/cost.py` (`total_uses()`), niet uit een eigen berekening in de route.

### `src/needful/main.py`

Het startpunt van de app.

```python
from needful.ui.screens import advies, q1, q2, q3, q4, start  # noqa: F401

setup_logging()

app = FastAPI(title="needful.", version="0.1.0")
app.include_router(api_router, prefix="/api")
ui.run_with(app, title="needful.", storage_secret="dev-only-change-me")
```

1. Importeert de zes schermen. Die import lijkt ongebruikt (daarom `# noqa: F401`), maar hij moet er staan: door de import worden de `@ui.page`-decorators uitgevoerd en zo bestaan de routes `/`, `/vraag/1` … `/advies`.
2. Zet de logging aan (zie `logging_setup.py`).
3. Maakt de FastAPI-app en hangt de routes uit `api/routes.py` eraan, met prefix `/api`.
4. `ui.run_with(app, ...)` laat NiceGUI **meeliften** op dezelfde app, in plaats van een eigen server te starten.

**Waarom de schermen hier rechtstreeks geïmporteerd worden** (en niet via een tussenbestand zoals het vroegere `pages.py`): tussen twee UI-tests laadt NiceGUI de module van elke pagina-functie opnieuw. Met een tussenbestand blijft dat bestand in het geheugen hangen en verdwijnen de schermen vanaf de tweede test (404).

`storage_secret` is een geheime sleutel waarmee NiceGUI zijn sessiestorage versleutelt. De waarde is nu hardcoded en **hoort in productie uit `.env`** (staat op de roadmap).

### `src/needful/logging_setup.py`

Eén functie, `setup_logging()`, die `main.py` één keer aanroept.

- Formaat: `[tijd] [NIVEAU] [module] [bestand:regel] bericht`.
- Niveau van onze eigen code komt uit de omgevingsvariabele `LOG_LEVEL` (standaard `INFO`). Bibliotheken (uvicorn, httpx …) loggen pas vanaf `WARNING`, zodat je DEBUG van ónze code ziet zonder ruis.
- Elke module maakt zijn eigen logger met `logging.getLogger(__name__)`. Die heet dan bv. `needful.ui.storage`, een kind van `needful`; daarom werkt één niveau op `needful` voor alles.

Wat er gelogd wordt:

| Niveau | Wanneer |
|--------|---------|
| INFO | scherm geopend, antwoord opgeslagen, nieuwe vraag gestart, advies + reden, feedback 👍/👎 |
| DEBUG | alle antwoorden vlak voor het advies, en per adviesregel of ze paste en waarom |
| WARNING | antwoorden ontbreken (bv. iemand opent `/advies` rechtstreeks) en welke; ongeldige invoer op vraag 2 |

`calc/` logt zelf **niets** (pure code). `decide()` geeft zijn redenering terug in `advice.checks`, en het adviesscherm logt die.

### `src/needful/calc/format.py`

`euro(149)` → `€149`, `euro(12.4)` → `€12,40`, `euro(1280)` → `€1.280`; `km(0.6)` → `0,6 km`. Komma als decimaalteken en punt per duizendtal, zoals een Belg leest. Beide gebruiken één interne hulpfunctie `_belgian(waarde, decimalen)`. We gebruiken bewust geen `locale`: dat hangt af van de instellingen van de computer of server.

### `src/needful/calc/score.py`

`durability_score(lifespan, repairability, recyclability, review)`: vier criteria, elk `"ja"` / `"deels"` / `"nee"` = 100 / 50 / 0 punten, gemiddelde **naar beneden** afgerond met `int()`. Pitchvoorbeeld (ja, deels, nee, ja) → 62,5 → **62**. Niet `round()`: Python rondt 62,5 af naar 62 maar 63,5 naar 64 ("banker's rounding"), dus soms naar boven en soms naar beneden. Een onbekende waarde geeft een `ValueError`.

### `src/needful/calc/advice.py`

`decide(need, price, total_uses, alternatives, score)` geeft één `Advice` terug. De regels worden **in volgorde** gecontroleerd; de eerste die past, wint:

| # | Regel | Advies | Bespaard |
|---|-------|--------|----------|
| 1 | Q1 = "Eerlijk? Ik wil het gewoon" (`impuls`) | laten | nieuwprijs |
| 2 | gratis lenen binnen 2 km **en** ≤ 24 keer gebruiken | lenen | nieuwprijs |
| 3 | huurprijs × aantal keer < nieuwprijs | huren | verschil |
| 4 | tweedehands goedkoper **en** ≤ 24 keer gebruiken | kopen & doorverkopen | verschil |
| 5 | niets anders past | bewust kopen | 0 |

- De grenzen staan als constanten bovenaan: `LEND_MAX_KM = 2.0`, `OWN_FROM_USES = 24`.
- `best(alternatives, kind)` kiest het goedkoopste alternatief van een soort, bij gelijke prijs het dichtstbijzijnde.
- `Alternative`, `RuleCheck` en `Advice` zijn `@dataclass(frozen=True)`: klassen die enkel data dragen en niet meer veranderen.
- `Advice.checks` is de lijst van gecontroleerde regels, met per regel of ze paste en waarom. Zo blijft `calc/` puur en kan de UI de redenering toch loggen.
- Ontbrekend (bewust): "samen kopen" en "alternatief product", daar hebben we nog geen data voor. Komen er meer regels bij, dan is het *strategy pattern* (elke regel een eigen klasse met `check()`, en `decide()` loopt over een lijst) de logische volgende stap.

### `src/needful/flow/answers.py`

`Answers` is een dataclass met de antwoorden van één gebruiker: product, behoefte (Q1), gebruik per jaar, jaren, prijs (Q2), postcode (Q3) en de vier duurzaamheidscriteria (Q4). De standaardwaarden zijn het pitchvoorbeeld.

- `answers.total_uses` is een `@property`: leest als een veld, maar rekent via `calc/cost.py`.
- `to_dict()` / `Answers.from_dict(data)` zetten om van/naar een dict, want NiceGUI bewaart JSON. `from_dict` geeft ook terug **welke velden ontbraken**; de UI logt die als WARNING.

### `src/needful/alternatives/examples.py`

Vier vaste voorbeeldalternatieven (gereedschapsbib, buren, verhuur, tweedehands) tot het echte opzoeken in sprint 3 er is. Vervang je deze lijst later door een functie die hetzelfde type (`list[Alternative]`) teruggeeft, dan hoeven de schermen niet te veranderen.

### `src/needful/ui/theme.py`

De huisstijl uit het prototype, op één plek:

- **Kleuren als constanten** (`INK`, `PAPER`, `YELLOW`, `GREEN` …).
- **CSS-klassen** die met `nf-` beginnen: tekststijlen (`nf-h1`, `nf-display`, `nf-lead`, `nf-body`, `nf-big`, `nf-mono`), kleuren (`nf-muted`, `nf-faint`, `nf-soft`), knoppen (`nf-btn`, `nf-dark`, `nf-yellow`, `nf-choice`), en per scherm wat extra (kaart en pinnen op vraag 3, kaders op vraag 4 en het advies).
- `apply_theme(background)` voegt lettertypes, CSS en achtergrondkleur toe aan de huidige pagina.

**Afspraak:** schermen bevatten geen kleurcodes of vaste px-maten, alleen klassenamen. Enige uitzondering: waarden die uit de data komen (de positie van een pin op de kaart, de kleur van een balkje in de voortgangsbalk). Sommige klassen eindigen op de soort (`nf-row-lenen`, `nf-pin-huren`), zodat een scherm de naam rechtstreeks uit de data kan bouwen: `f"nf-row-{alt.kind}"`.

De Google Fonts worden nu online geladen. Voor een PWA die offline werkt moeten ze later in het project zelf komen.

### `src/needful/ui/components.py`

Bouwstenen die op meerdere schermen terugkomen:

- `screen(naam, achtergrond)`: past het thema toe, logt "scherm geopend" en geeft de smalle kolom (max. 430 px, telefoonbreedte) terug. Elk scherm begint met `with screen("vraag 1"):`.
- `logo()`, `header(stap)` (logo, "VRAAG n/4" en de voortgangsbalk), `button(tekst, actie, stijl)` en `nav(terug, volgende)` (de "← Terug / Volgende →"-rij onderaan).

### `src/needful/ui/storage.py`

Bewaart de antwoorden **per browser** in `app.storage.user` (NiceGUI koppelt die aan een cookie). Ze blijven bewaard bij herladen en werken met de terugknop van de telefoon.

- `start_new(product)`: de Start-knop zet álle antwoorden op het voorbeeld, met het gekozen product.
- `load_answers()`: leest de antwoorden; ontbreekt er iets, dan een WARNING met de veldnamen.
- `save_answer(veld, waarde)`: bewaart één antwoord meteen bij elke wijziging en logt het.

### `src/needful/ui/screens/`

Eén bestand per scherm, elk met een `@ui.page`:

| Bestand | Route | Wat |
|---------|-------|-----|
| `start.py` | `/` | product invullen, Start |
| `q1.py` | `/vraag/1` | heb je het écht nodig? 4 keuzes, klikken = bewaren en door |
| `q2.py` | `/vraag/2` | gebruik per jaar, jaren, prijs → live "= €12,42 per gebruik". Micknop staat er al, maar is uitgeschakeld (spraak = sprint 4) |
| `q3.py` | `/vraag/3` | postcode, voorbeeldkaart met pinnen en lijst van alternatieven |
| `q4.py` | `/vraag/4` | vier criteria met ja/deels/nee → live score /100 |
| `advies.py` | `/advies` | het advies, de vergelijking kopen/huren/tweedehands/lenen, bespaard bedrag, reden, 👍/👎 |

Let op in `q1.py` en `q4.py`: `lambda need=need: choose(need)`. Zonder `=need` onthoudt elke knop pas bij het klikken welke `need` er is, en dan is de lus al voorbij: alle knoppen zouden de laatste waarde bewaren.

NiceGUI laat je de UI in Python schrijven. Er is dus geen aparte JavaScript-frontend, dat was een bewuste keuze.

### Tests (`tests/`)

| Bestand | Wat |
|---------|-----|
| `test_cost.py` | kost per gebruik en `total_uses`, ook de foutgevallen |
| `test_format.py` | euro- en km-notatie, duizendtallen |
| `test_score.py` | pitch = 62, alles ja = 100, alles nee = 0, naar beneden afronden, foute waarde |
| `test_advice.py` | elke regel, de volgorde, grensgevallen (2,0 vs 2,1 km; 24 vs 25 keer), zinnen zonder aan elkaar geplakte woorden |
| `test_answers.py` | standaardwaarden, bewaren en terugladen, ontbrekende velden |
| `test_logging_setup.py` | niveau uit `LOG_LEVEL` |
| `test_ui_flow.py` | een gesimuleerde gebruiker klikt door de app: start → advies "lenen", impulsaankoop → "laten", terugknop, `/advies` rechtstreeks openen geeft een waarschuwing in de log |
| `conftest.py` | zet NiceGUI's `user`-testhulp aan |

### `pyproject.toml`

De projectdefinitie: naam, Python ≥ 3.12, dependencies, dev-dependencies (pytest, pytest-asyncio, pytest-cov, ruff) en de configuratie van ruff (regellengte 100) en pytest (`tests/` als testmap, `asyncio_mode = "auto"` voor de `async`-UI-tests en `main_file` zodat de testgebruiker weet welke app hij moet starten). Een deel van de dependencies (SQLModel, Alembic, httpx, BeautifulSoup, psycopg) wordt nog niet gebruikt, ze staan klaar voor latere sprints.

### `uv.lock`

Legt exacte versies vast zodat iedereen dezelfde versies heeft. Niet met de hand aanpassen en wel committen.

### `Dockerfile` en `docker-compose.yml`

- `Dockerfile`: pakt `python:3.12-slim`, kopieert de code, installeert het project met `pip` en start `uvicorn` op poort 8080 met `--reload` (herstart bij codewijziging). Dit is een **ontwikkel**-image, geen productie-image.
- `docker-compose.yml`: twee services.
  - `db`: PostgreSQL 16 met gebruiker/wachtwoord/database `needful`. Data blijft bewaard in de volume `pgdata`.
  - `app`: bouwt het Dockerfile, leest `.env`, krijgt een `DATABASE_URL` die naar de `db`-service wijst en mount de projectmap (`.:/app`) zodat codewijzigingen direct zichtbaar zijn.
- `docker-compose.override.yml` staat **niet in git** (lokale aanpassing): zet de database-poort op 5433 om een conflict met een lokale Postgres te voorkomen.

### `.env.example` en `.env`

`.env.example` is de sjabloon (staat in git), `.env` is jouw eigen kopie met echte waarden (staat in `.gitignore`, **nooit committen**). Variabelen: `DATABASE_URL`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `OLLAMA_BASE_URL`, `APP_PORT`, `RATE_LIMIT_PER_MINUTE`, `LOG_LEVEL`. Op dit moment leest de code enkel `LOG_LEVEL`; de rest komt met de database en de LLM-koppeling.

## 5. Een request van begin tot eind

Voorbeeld: `POST /api/cost-per-use` met `{"price": 149, "uses_per_year": 3, "years": 4}`.

1. De browser (of `curl`) stuurt de request naar uvicorn op poort 8080.
2. FastAPI ziet het pad `/api/cost-per-use` (prefix `/api` uit `main.py` + `/cost-per-use` uit `routes.py`).
3. Pydantic zet de JSON om naar een `CostRequest` en controleert de regels (`gt=0`). Bij een fout is hier al een `422`.
4. `cost()` roept `cost_per_use(149, 3, 4)` aan in `calc/cost.py`.
5. Dat rekent `149 / 12 = 12,4166…` en rondt af op `12.42`.
6. De route pakt het in als `CostResponse` en FastAPI stuurt `{"cost_per_use": 12.42, "total_uses": 12}` terug.

Zelf proberen: start de app (zie README) en open <http://localhost:8080/docs>. Daar kun je endpoints uitproberen zonder code.

### Een klik door de wizard

Voorbeeld: je kiest "Het zou handig zijn" op vraag 1 en loopt door tot het advies.

1. **Start** (`start.py`): `start_new("hogedrukreiniger")` zet alle antwoorden op het voorbeeld in `app.storage.user`, daarna `ui.navigate.to("/vraag/1")`.
2. **Vraag 1** (`q1.py`): `load_answers()` leest ze, de knop "Het zou handig zijn" is zwart. Klikken → `save_answer("need", "handig")` (log: `antwoord opgeslagen: need='handig'`) → naar `/vraag/2`.
3. **Vraag 2**: `cost_per_use(149, 3, 4)` uit `calc/` toont "= €12,42 per gebruik". Elke wijziging wordt meteen bewaard.
4. **Vraag 3 en 4**: postcode bewaren bij het verlaten van het veld; de vier toggles rekenen live `durability_score(...)` = 62.
5. **Advies** (`advies.py`): leest alle antwoorden, rekent de score, roept `decide(...)` aan en logt elke gecontroleerde regel (DEBUG) en het advies (INFO). Regel 2 past (gratis lenen op 0,6 km, 12 keer ≤ 24) → "Lenen is de slimste keuze.", €149 bespaard.

Herlaad je een pagina, dan staan je antwoorden er nog: ze zitten in de browserstorage, niet in het scherm.

Logs met alle details zien:

```powershell
$env:LOG_LEVEL="DEBUG"; uv run uvicorn needful.main:app --reload --port 8080
```

## 6. Waarom deze keuzes

| Keuze | Reden |
|-------|-------|
| **Python overal** | We zijn een Python-vak en willen één taal begrijpen en uitleggen. Daarom geen Next.js of JavaScript. |
| **NiceGUI** | UI in Python, draait op FastAPI en kan als PWA op Android en iPhone. |
| **FastAPI + Pydantic** | Snelle API met automatische validatie en automatische docs op `/docs`. |
| **Aparte `calc/`** | Pure functies zonder I/O zijn makkelijk te testen en uit te leggen. Hier zit de waarde van de app. |
| **PostgreSQL + SQLModel** | Voor de admin-module en de cache regio × product. SQLModel combineert SQLAlchemy en Pydantic. |
| **Alembic** | Databasewijzigingen als migraties, zodat iedereen hetzelfde schema heeft. |
| **uv** | Snel, regelt Python-versie en packages in één tool en geeft een lockfile. |
| **Docker** | Postgres en app starten met één commando, op elk besturingssysteem hetzelfde. |
| **Geen LangChain/Django/Streamlit** | Te veel magie. We willen elke regel kunnen uitleggen. |
| **Geen login of persoonsgegevens** | Minder risico (privacy) en minder werk. Accounts staan in "versie 2". |

## 7. Configuratie en omgeving

Lokaal draaien (details in de README):

```bash
cp .env.example .env
uv sync --extra dev
uv run pytest
uv run uvicorn needful.main:app --reload --port 8080
```

Voor je pusht: `uv run ruff check . && uv run pytest` (zie `CONTRIBUTING.md`).

## 8. Tests

- Tests staan in `tests/` en draaien met `uv run pytest` (38 tests, ± 2 seconden).
- Regel: **alles in `calc/` heeft tests**, inclusief de foutgevallen en de grenzen (2,0 vs 2,1 km).
- Werkwijze: **eerst de test, dan zien dat hij faalt (rood), dan de code (groen)**. Een test die nooit rood is geweest, test misschien niets.
- Een goede test noemt wat hij controleert (`test_pitch_example`) en gebruikt voorbeelden waarvan we het juiste antwoord vooraf weten. Het commentaar beschrijft de regel in gewone woorden, niet in variabelenamen.
- De UI-tests (`test_ui_flow.py`) gebruiken NiceGUI's `user`: een gesimuleerde gebruiker die knoppen vindt op hun tekst en erop klikt, zonder echte browser. Verander je een knoptekst ("Start →"), pas dan ook de test aan.
- Een lange foutmelding lezen: zoek de regel met `src\needful\…` erin. Alles onder `.venv\` is bibliotheekcode.

## Nog te bouwen

Dit bestaat nog niet. Zodra het er komt, verplaats je het naar de secties hierboven.

| Onderdeel | Wat het gaat doen | Sprint |
|-----------|-------------------|--------|
| `calc/` advies, rest | De uitkomsten "samen kopen" en "alternatief product" | 3 |
| `ui/` PWA | Manifest, icons, service worker, lettertypes lokaal voor offline gebruik | 3 |
| `ui/` kaart | Echte OpenStreetMap-kaart en postcode → coördinaten op vraag 3 | 3 |
| `db/` | SQLModel-modellen, Alembic-migraties, admin-gegevens, cache | 1–3 |
| `alternatives/` | LLM (OpenRouter of Ollama) plus korte scraping van uitleen-, huur- en tweedehandssites | 3 |
| admin-module | Gebruik en verbruik bijhouden (anoniem) | 3 |
| `voice/` | Spraak omzetten naar een antwoord op de vragen | 4 |

## Woordenlijst

| Term | Betekenis |
|------|-----------|
| **API** | Aan de buitenkant van de app: URL's waar je data heen stuurt en data van terugkrijgt. |
| **Endpoint / route** | Eén zo'n URL met een bepaalde actie, bv. `POST /api/cost-per-use`. |
| **FastAPI** | Python-framework om een API te bouwen. |
| **Pydantic** | Bibliotheek die data controleert en omzet op basis van klassen met types. |
| **NiceGUI** | Python-bibliotheek om webschermen te maken zonder zelf HTML en JavaScript te schrijven. |
| **PWA** | Progressive Web App: een website die op je telefoon als app te installeren is. |
| **uvicorn** | De server die FastAPI uitvoert. |
| **ORM / SQLModel** | Laat je met Python-klassen met een database werken in plaats van met rauwe SQL. |
| **Migratie (Alembic)** | Een script dat het databaseschema van versie A naar B brengt. |
| **LLM** | Large language model, het taalmodel dat alternatieven voorstelt. |
| **Scraping** | Automatisch informatie van websites halen. |
| **Cache** | Een bewaard antwoord, zodat we dezelfde (trage of dure) opzoeking niet opnieuw doen. |
| **Docker / compose** | Draait app en database in afgeschermde containers. Compose start er meerdere samen. |
| **Lockfile** | Bestand met exacte versies van alle packages. |

## Vragen die we kunnen krijgen

**Waar zit de logica van de app?**
In `calc/` (kost, score, advies) en `flow/` (de antwoorden). API en UI zijn alleen de buitenkant.

**Hoe beslist de app welk advies je krijgt?**
Vijf regels in `calc/advice.py`, in vaste volgorde; de eerste die past, wint (zie de tabel bij `advice.py`). In de log met `LOG_LEVEL=DEBUG` zie je per regel of ze paste en waarom.

**Waarom staan er geen kleuren in de schermen?**
Alle kleuren en maten staan in `ui/theme.py`. Wil de groep de huisstijl aanpassen, dan is dat één bestand in plaats van zes schermen.

**Waar blijven de antwoorden van een gebruiker?**
In de browser zelf (`app.storage.user`, gekoppeld aan een cookie), niet in een database. Er is geen login en we bewaren niets op naam.

**Waarom gebruiken jullie niet overal klassen (OOP)?**
Data die samen hoort is wel een klasse (`Answers`, `Advice`, `Alternative`). Berekeningen zijn gewone functies: ze onthouden niets, dus een klasse zou niets toevoegen, en een functie test je met één regel.

**Waarom staat het rekenen niet gewoon in de route?**
Dan moet je voor elke test een server starten, en een wijziging in de API zou de rekenregels kunnen breken. Als pure functie is het snel te testen en te hergebruiken, bijvoorbeeld door de UI én de API.

**Wat gebeurt er als iemand een negatieve prijs invult?**
Pydantic weigert het al in de API (`422`). Zou `cost_per_use` rechtstreeks worden aangeroepen, dan gooit die zelf een `ValueError`. Beide lagen controleren dus, bewust.

**Hoe komen de UI en de API in dezelfde server?**
`ui.run_with(app)` in `main.py` koppelt NiceGUI aan de bestaande FastAPI-app.

**Wat is het verschil tussen `.env` en `.env.example`?**
`.env.example` is een sjabloon zonder geheimen (in git). `.env` bevat echte waarden zoals API-sleutels en blijft lokaal.

**Waarom twee database-ports (5432/5433)?**
Compose zet standaard 5432 open. Heb je lokaal al een Postgres draaien, dan kan een lokale override (`docker-compose.override.yml`, niet in git) die naar 5433 verplaatsen.

**Waarom zijn er dependencies die nog niet gebruikt worden?**
We hebben de stack vooraf gekozen en in één keer vastgezet. Ze worden in sprint 1–3 gebruikt (database, scraping).
