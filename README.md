# needful.

**Koop minder. Kies beter.**

Een beslissingshulp vóór je iets koopt. In ± 3 minuten beantwoord je vier eerlijke vragen en krijg je één onderbouwd advies: laten, lenen, huren, samen kopen, alternatief product, kopen & later doorverkopen, of bewust kopen.

Groepswerk **Python Developer 2** · Robin · Femke · Christian · oktober 2026

## De drie vragen

| # | Vraag | Wat we berekenen |
|---|-------|------------------|
| 1 | Heb je het écht nodig? | behoefte of impuls |
| 2 | Hoe vaak ga je het gebruiken? | kost per gebruik (€ ÷ aantal keer), ook mét de extra kosten om mee rekening te houden (LLM) |
| 3 | Moet het per se nieuw en van jou? | welke alternatieven meetellen + alternatieven met prijsindicatie, bv. een wassalon (LLM). Hier kies je ook: een antwoord, een alternatief, of "Zet alles op een rij" als vierde antwoord |

Daarna volgt het advies. Dat vergelijkt je keuze met nieuw kopen en met wat de regels aanraden; koos je een alternatief, dan gaat het er verder op in. Koos je "Zet alles op een rij", dan zie je alle mogelijkheden: nieuw kopen (met extra kosten en exit-strategie), elk alternatief en niet kopen (bespaarde € en CO2), elk met de prijs over jouw gebruiksduur. Vanaf het advies zoek je met postcode + gemeente waar je het in je buurt kunt lenen, huren, tweedehands of nieuw kopen, laten herstellen of een alternatief vindt (OpenStreetMap + repaircafe.org, nagekeken door het LLM), met een link naar tweedehands op 2dehands.

Antwoorden kan typend of met je stem. Geen login, geen persoonsgegevens.

## Stack

- **Python 3.12** via uv
- **NiceGUI** – frontend (desktop web + PWA voor Android/iPhone), draait op FastAPI
- **FastAPI + Pydantic** – API
- **SQLModel / SQLAlchemy 2 + Alembic** – database-laag
- **PostgreSQL** – admin-module (gebruik & verbruik) + cache regio × product
- **BeautifulSoup + httpx** – scraping van repaircafe.org, OpenStreetMap (Nominatim + Overpass) voor winkels en uitleenpunten
- **OpenRouter** – LLM (`anthropic/claude-haiku-5.5`, vergelijking in `.env.example`); Ollama lokaal en spraak volgen later
- **pytest** – tests, vooral op de rekenkern
- **Docker** – lokaal draaien in één commando

Bewust niet: Next.js/JavaScript, Streamlit, Django, LangChain.

## Projectstructuur

```
needful/            Python-package
  api/              FastAPI-routes
  flow/             vragen & volgorde
  calc/             €/gebruik · score · advies  (pure Python, volledig getest)
  alternatives/     LLM (OpenRouter) + zoeken in de buurt (OpenStreetMap, repaircafe.org)
  voice/            spraak → antwoord
  db/               SQLModel-modellen, admin-module, cache
  ui/               NiceGUI-schermen + PWA (manifest, service worker)
tests/              pytest
docs/concept/       pitch & voorontwerp (pdf)
```

## Lokaal draaien

We gebruiken [uv](https://docs.astral.sh/uv/) voor Python en packages (eenmalig installeren):

```powershell
# Windows (PowerShell), daarna terminal opnieuw openen
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Dan in de projectmap:

```bash
cp .env.example .env            # Windows: copy .env.example .env
uv python install 3.12
uv sync --extra dev             # maakt .venv en installeert alles
uv run pytest                   # tests
uv run uvicorn needful.main:app --reload --port 8080
```

`uv run` gebruikt automatisch de .venv, je hoeft niets te activeren. Commit `uv.lock` mee zodat iedereen dezelfde versies heeft.

### Met Docker

Installeer [Docker Desktop](https://www.docker.com/products/docker-desktop/) en start het.

```bash
docker compose up --build       # Postgres + app samen (Ctrl+C om te stoppen)
docker compose up -d db         # alleen de database, app lokaal via uv run
docker compose down             # alles stoppen
```

App: http://localhost:8080 · API-docs: http://localhost:8080/docs

## Tests

```bash
uv run pytest
```

## Werkwijze

- 4 sprints van 30 uur (3 × 10 u.), MVP online na sprint 3, spraak in sprint 4.
- Claude Code schrijft het meeste code; wij plannen elke feature eerst samen, reviewen elke pull request en mergen niets wat niemand van ons begrijpt.
- Werken op een branch per feature (`feat/...`), pull request naar `main`, minstens één review.
- Issues/kanban: zie het Projects-tabblad van deze repo.

## Roadmap

| Sprint | Thema | Belangrijkste onderdelen |
|--------|-------|--------------------------|
| 1 | Fundament | vragen & scoremodel, design & frontend-basis, repo/Docker/db |
| 2 | Vragenflow | api + flow + calc + tests, NiceGUI-wizard |
| 3 | Advies & live | alternatives (LLM + scraping), PWA, admin-module, gebruikerstest, online |
| 4 | Spraak | spraakmodellen vergelijken + inbouwen, afwerking, buffer |

Bewust nog niet (versie 2): avatar · accounts & login · eigen ML-modellen · afkoel-wachtlijst.
