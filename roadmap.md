# Roadmap needful.

Levend document: vink af wat klaar is, vul **Wie** in bij het verdelen van het werk en voeg onderaan nieuwe items toe.
Planning is gebaseerd op de urenraming (120 u. in totaal, 4 sprints). Laatste statusupdate: 29 oktober 2026.

**Legenda:** `[x]` klaar · `[~]` deels gedaan (zie opmerking) · `[ ]` nog te doen
**Wie:** R = Robin · F = Femke · C = Christian

## Overzicht

| Sprint | Thema | Raming | Status |
|--------|-------|--------|--------|
| 1 | Fundament | ± 26 u. + deel van "code doornemen" | bezig |
| 2 | Vragenflow | 14 u. + deel van NiceGUI/PWA | nog niet gestart |
| 3 | Advies & live | ± 52 u. | nog niet gestart |
| 4 | Spraak | 16 u. + deel buffer | nog niet gestart |
| | **Totaal** | **120 u.** | |

---

## Sprint 1 · Fundament

### Vragen, uitkomsten & scoremodel uitschrijven (12 u.)

- [~] Vier vragen en zeven uitkomsten beschrijven (laten, lenen, huren, samen kopen, alternatief, kopen & doorverkopen, bewust kopen) — *concept staat in `docs/concept/`, nog niet vastgelegd als beslisregels in code of docs*. Wie: ?
- [ ] Scoremodel duurzaamheid /100 uitschrijven (levensduur, herstelbaar, recycleerbaar, reviews: gewichten + formule). Wie: ?
- [ ] Beslisregels: welke antwoordcombinatie leidt tot welk advies. Wie: ?
- [ ] Vraagteksten en uitkomstteksten finaliseren (taal en toon). Wie: ?

### Design & frontend-basis (8 u.)

- [~] Startscherm met titel, tagline en productveld — *placeholder in `ui/pages.py`, nog geen design*. Wie: ?
- [ ] Huisstijl: kleuren, typografie, basiscomponenten (kaart, knop, voortgangsbalk). Wie: ?
- [ ] Mobile-first layout voor de wizard (schetsen of wireframes). Wie: ?

### Setup: repo, Docker, database (6 u.)

- [x] Repo met projectstructuur (`api/ flow/ calc/ alternatives/ voice/ db/ ui/`)
- [x] uv + `pyproject.toml` + `uv.lock`
- [x] Dockerfile en `docker-compose.yml` (app + Postgres)
- [x] `.env.example`, `.gitignore`
- [x] README met lokale setup en Docker
- [x] `CONTRIBUTING.md` en PR-template
- [ ] Database-verbinding en eerste SQLModel-modellen (`db/` is nog leeg). Wie: ?
- [ ] Alembic opzetten + eerste migratie. Wie: ?
- [ ] CI (ruff + pytest bij elke PR). Wie: ?
- [ ] Kanban/Projects-bord aanmaken in GitHub. Wie: ?

### Code samen doornemen & leren (12 u., sprint 1–4)

- [ ] Doorlopend: elke PR samen bekijken, niets mergen wat niemand begrijpt. Per sprint ± 3 u.

---

## Sprint 2 · Vragenflow

### API + flow + calc + tests (14 u.)

- [x] `calc/cost.py`: kost per gebruik (€ ÷ aantal keer) met tests
- [x] FastAPI-app met `/api/health` en `/api/cost-per-use`
- [ ] `flow/`: vragen en volgorde als datamodel (state machine of lijst van stappen). Wie: ?
- [ ] `calc/`: duurzaamheidsscore /100 + tests. Wie: ?
- [ ] `calc/`: adviesbepaling (antwoorden → uitkomst) + tests. Wie: ?
- [ ] API-endpoints voor de flow (start, antwoord, resultaat). Wie: ?
- [ ] Pydantic-schema's voor requests en responses. Wie: ?
- [ ] Rate limiting (`RATE_LIMIT_PER_MINUTE` staat al in `.env.example`). Wie: ?

### NiceGUI-webversie + PWA (18 u., sprint 2–3)

- [ ] Wizard: vier schermen met voortgang. Wie: ?
- [ ] Resultaatscherm met advies en uitleg. Wie: ?
- [ ] Wizard koppelen aan de API/flow. Wie: ?
- [ ] Responsive voor desktop en mobiel. Wie: ?
- [ ] PWA: manifest, icons, service worker (sprint 3). Wie: ?
- [ ] Testen op Android én iPhone (sprint 3). Wie: ?

---

## Sprint 3 · Advies & live

### Alternatives: LLM + korte scraping per regio (12 u.)

- [ ] LLM-client via OpenRouter (met Ollama als lokale optie). Wie: ?
- [ ] Prompt: alternatieven voorstellen op basis van product + regio. Wie: ?
- [ ] Scraping van enkele uitleen-/huur-/tweedehandssites (httpx + BeautifulSoup), klein houden. Wie: ?
- [ ] Cache regio × product in Postgres. Wie: ?
- [ ] Fallback als LLM of scraping faalt. Wie: ?

### Gebruikerstest, 5 personen (10 u.)

- [ ] Testscript en vragen opstellen. Wie: ?
- [ ] 5 testers vinden en sessies afnemen. Wie: ?
- [ ] Bevindingen verzamelen en prioriteren. Wie: ?
- [ ] Belangrijkste fixes doorvoeren. Wie: ?

### Admin-module: gebruik & verbruik (6 u.)

- [ ] Loggen van gebruik (anoniem, geen persoonsgegevens). Wie: ?
- [ ] Verbruik bijhouden (LLM-calls, kosten). Wie: ?
- [ ] Eenvoudige adminpagina met overzicht. Wie: ?

### Online zetten & buffer (6 u., sprint 3–4)

- [ ] Hosting kiezen (zie open vragen). Wie: ?
- [ ] Deployment, domein en HTTPS. Wie: ?
- [ ] Productie-Dockerfile (nu `--reload` en `pip`, straks `uv` en geen reload). Wie: ?
- [ ] Secrets en `storage_secret` uit `.env` halen (nu hardcoded dev-waarde in `main.py`). Wie: ?
- [ ] **Mijlpaal: MVP online na sprint 3**

---

## Sprint 4 · Spraak

### Voice: spraakmodellen vergelijken + inbouwen (16 u.)

- [ ] Spraakmodellen vergelijken (kwaliteit, snelheid, kost, NL-ondersteuning). Wie: ?
- [ ] Keuze vastleggen met korte motivatie. Wie: ?
- [ ] Spraak → tekst → antwoord op de vier vragen. Wie: ?
- [ ] Micknop in de UI, toestemming en foutafhandeling (vooral iPhone/Safari). Wie: ?
- [ ] Tests en fallback naar typen. Wie: ?

### Afwerking en buffer

- [ ] Eindtest op alle platformen. Wie: ?
- [ ] Documentatie bijwerken (README, uitleg voor het vak). Wie: ?
- [ ] Presentatie voorbereiden. Wie: ?

---

## Backlog en nieuwe ideeën

Hier komt alles wat tijdens het project opduikt. Zet erbij wie het voorstelt, wat het oplevert en in welke sprint het past.

| Item | Voorgesteld door | Sprint | Status |
|------|------------------|--------|--------|
| *(voorbeeld)* Delen van het advies via link | | ? | idee |

### Bewust nog niet (versie 2)

- Avatar
- Accounts & login
- Eigen ML-modellen
- Afkoel-wachtlijst

## Open vragen

- Waar hosten we (gratis tier, school, eigen VPS)?
- Welk LLM-model gebruiken we in productie, en wat is het maandbudget?
- Welke regio's ondersteunen we voor de scraping in de eerste versie?
- Dockerfile gebruikt `pip` terwijl het project op `uv` draait: gelijktrekken?

## Wijzigingslog

| Datum | Wijziging |
|-------|-----------|
| 2026-10-29 | Eerste versie, status bepaald op basis van de repo |
