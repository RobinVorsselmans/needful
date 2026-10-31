# Explain me

Uitleg bij de code en de structuur van needful., zodat we allemaal kunnen uitleggen wat er gebeurt en waarom.
Dit is een aanvulling op de docstrings en commentaren in de code, geen vervanging.

> **Onderhoud:** voeg bij elke gemergede feature een stukje toe of pas het aan. Staat er iets in dat niet meer klopt, verbeter het in dezelfde PR.
> Dit document beschrijft de staat van **29 oktober 2026** (einde sprint 1, begin). Delen die nog niet bestaan staan onder [Nog te bouwen](#nog-te-bouwen).

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
| `src/needful/calc/` | Rekenkern: kost per gebruik, later score en advies | `cost.py` klaar |
| `src/needful/api/` | HTTP-endpoints (FastAPI) | `/health`, `/cost-per-use` |
| `src/needful/ui/` | NiceGUI-pagina's, later ook PWA | alleen een startscherm |
| `src/needful/flow/` | De vier vragen en hun volgorde | leeg (docstring) |
| `src/needful/alternatives/` | Alternatieven zoeken via LLM en scraping | leeg (docstring) |
| `src/needful/voice/` | Spraak omzetten naar antwoorden | leeg (docstring) |
| `src/needful/db/` | Database-modellen, admin-module, cache | leeg (docstring) |
| `tests/` | pytest-tests | `test_cost.py` |
| `docs/concept/` | Pitch en voorontwerp (pdf) | bestaat |

De `src/`-layout (code in `src/needful/` en niet direct in de root) voorkomt dat je per ongeluk code importeert uit de werkmap in plaats van uit het geïnstalleerde package.

## 4. Bestand voor bestand

### `src/needful/calc/cost.py`

Bevat één functie, `cost_per_use(price, uses_per_year, years)`.

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

Opmerking: `total_uses` wordt in de route ook berekend (`uses_per_year * years`), dus die vermenigvuldiging staat op twee plaatsen. Als dit groeit, hoort dat in `calc/`.

### `src/needful/main.py`

Het startpunt van de app.

```python
app = FastAPI(title="needful.", version="0.1.0")
app.include_router(api_router, prefix="/api")
ui.run_with(app, title="needful.", storage_secret="dev-only-change-me")
```

1. Maakt de FastAPI-app.
2. Hangt de routes uit `api/routes.py` eraan, met prefix `/api`.
3. `ui.run_with(app, ...)` laat NiceGUI **meeliften** op dezelfde app, in plaats van een eigen server te starten.

De regel `from needful.ui import pages` lijkt ongebruikt (daarom `# noqa: F401`), maar hij moet er staan: door de import worden de `@ui.page`-decorators in `pages.py` uitgevoerd en zo bestaan de schermen.

`storage_secret` is een geheime sleutel waarmee NiceGUI zijn sessiestorage versleutelt. De waarde is nu hardcoded en **hoort in productie uit `.env`** (staat op de roadmap).

### `src/needful/ui/pages.py`

Het startscherm. `@ui.page("/")` zegt: "deze functie tekent de pagina op `/`".

- Een kolom met titel, tagline, een invoerveld ("Wat wil je kopen?") en een Start-knop.
- De knop toont voorlopig alleen een melding (`ui.notify`). De echte vragenwizard komt in sprint 2.
- De stijl komt uit Tailwind-klassen (`"w-full max-w-md mx-auto p-6 gap-4"`), die NiceGUI standaard meebrengt. `max-w-md` houdt het smal, zoals een telefoon.

NiceGUI laat je de UI in Python schrijven. Er is dus geen aparte JavaScript-frontend, dat was een bewuste keuze.

### `tests/test_cost.py`

Vier tests voor `cost_per_use`: het pitchvoorbeeld (12,42), een enkele keer gebruiken (60,0), en twee foutgevallen (prijs 0, gebruiken 0). Elke regel in `calc/` krijgt zulke tests.

### `pyproject.toml`

De projectdefinitie: naam, Python ≥ 3.12, dependencies, dev-dependencies (pytest, pytest-cov, ruff) en de configuratie van ruff (regellengte 100) en pytest (`tests/` als testmap). Een deel van de dependencies (SQLModel, Alembic, httpx, BeautifulSoup, psycopg) wordt nog niet gebruikt, ze staan klaar voor latere sprints.

### `uv.lock`

Legt exacte versies vast zodat iedereen dezelfde versies heeft. Niet met de hand aanpassen en wel committen.

### `Dockerfile` en `docker-compose.yml`

- `Dockerfile`: pakt `python:3.12-slim`, kopieert de code, installeert het project met `pip` en start `uvicorn` op poort 8080 met `--reload` (herstart bij codewijziging). Dit is een **ontwikkel**-image, geen productie-image.
- `docker-compose.yml`: twee services.
  - `db`: PostgreSQL 16 met gebruiker/wachtwoord/database `needful`. Data blijft bewaard in de volume `pgdata`.
  - `app`: bouwt het Dockerfile, leest `.env`, krijgt een `DATABASE_URL` die naar de `db`-service wijst en mount de projectmap (`.:/app`) zodat codewijzigingen direct zichtbaar zijn.
- `docker-compose.override.yml` staat **niet in git** (lokale aanpassing): zet de database-poort op 5433 om een conflict met een lokale Postgres te voorkomen.

### `.env.example` en `.env`

`.env.example` is de sjabloon (staat in git), `.env` is jouw eigen kopie met echte waarden (staat in `.gitignore`, **nooit committen**). Variabelen: `DATABASE_URL`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `OLLAMA_BASE_URL`, `APP_PORT`, `RATE_LIMIT_PER_MINUTE`. Op dit moment leest de code er nog geen enkele van; dat komt met de database en de LLM-koppeling.

## 5. Een request van begin tot eind

Voorbeeld: `POST /api/cost-per-use` met `{"price": 149, "uses_per_year": 3, "years": 4}`.

1. De browser (of `curl`) stuurt de request naar uvicorn op poort 8080.
2. FastAPI ziet het pad `/api/cost-per-use` (prefix `/api` uit `main.py` + `/cost-per-use` uit `routes.py`).
3. Pydantic zet de JSON om naar een `CostRequest` en controleert de regels (`gt=0`). Bij een fout is hier al een `422`.
4. `cost()` roept `cost_per_use(149, 3, 4)` aan in `calc/cost.py`.
5. Dat rekent `149 / 12 = 12,4166…` en rondt af op `12.42`.
6. De route pakt het in als `CostResponse` en FastAPI stuurt `{"cost_per_use": 12.42, "total_uses": 12}` terug.

Zelf proberen: start de app (zie README) en open <http://localhost:8080/docs>. Daar kun je endpoints uitproberen zonder code.

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

- Tests staan in `tests/` en draaien met `uv run pytest`.
- Regel: **alles in `calc/` heeft tests**, inclusief de foutgevallen.
- Een goede test noemt wat hij controleert (`test_pitch_example`) en gebruikt voorbeelden waarvan we het juiste antwoord vooraf weten.

## Nog te bouwen

Dit bestaat nog niet. Zodra het er komt, verplaats je het naar de secties hierboven.

| Onderdeel | Wat het gaat doen | Sprint |
|-----------|-------------------|--------|
| `flow/` | De vier vragen en hun volgorde beschrijven, bepalen wat de volgende stap is | 2 |
| `calc/` score en advies | Duurzaamheidsscore /100 en de keuze tussen de zeven uitkomsten | 2 |
| `ui/` wizard | De vier schermen en het resultaatscherm, later ook PWA (manifest, service worker) | 2–3 |
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
In `calc/` (en straks `flow/`). API en UI zijn alleen de buitenkant.

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
