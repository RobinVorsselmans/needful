# Roadmap needful.

Levend document: vink af wat klaar is, vul **Wie** in bij het verdelen van het werk en voeg onderaan nieuwe items toe.
Planning is gebaseerd op de urenraming (120 u. in totaal, 4 sprints). Laatste statusupdate: 1 november 2026.

**Legenda:** `[x]` klaar · `[~]` deels gedaan (zie opmerking) · `[ ]` nog te doen
**Wie:** R = Robin · F = Femke · C = Christian

## Overzicht

| Sprint | Thema | Raming | Status |
|--------|-------|--------|--------|
| 1 | Fundament | ± 26 u. + deel van "code doornemen" | bezig (db, CI, scoremodel uitschrijven open) |
| 2 | Vragenflow | 14 u. + deel van NiceGUI/PWA | bezig (wizard klikbaar, API-koppeling open) |
| 3 | Advies & live | ± 52 u. | nog niet gestart |
| 4 | Spraak | 16 u. + deel buffer | nog niet gestart |
| | **Totaal** | **120 u.** | |

---

## Sprint 1 · Fundament

### Vragen, uitkomsten & scoremodel uitschrijven (12 u.)

- [~] Vier vragen en zeven uitkomsten beschrijven (laten, lenen, huren, samen kopen, alternatief, kopen & doorverkopen, bewust kopen) — *concept staat in `docs/concept/`, nog niet vastgelegd als beslisregels in code of docs*. Wie: ?
- [~] Scoremodel duurzaamheid /100 uitschrijven (levensduur, herstelbaar, recycleerbaar, reviews: gewichten + formule) — *voorlopig gelijke gewichten ja/deels/nee = 100/50/0 in `calc/score.py`, nog samen vastleggen*. Wie: R
- [~] Beslisregels: welke antwoordcombinatie leidt tot welk advies — *5 voorbeeldregels in `calc/advice.py` (laten, lenen, huren, kopen & doorverkopen, bewust kopen); "samen kopen" en "alternatief" ontbreken nog*. Wie: R
- [ ] Vraagteksten en uitkomstteksten finaliseren (taal en toon). Wie: ?

### Design & frontend-basis (8 u.)

- [x] Startscherm met titel, tagline en productveld (`ui/screens/start.py`). Wie: R
- [x] Huisstijl: kleuren, typografie, basiscomponenten (kaart, knop, voortgangsbalk) — `ui/theme.py` + `ui/components.py`, uit het prototype. Wie: R
- [x] Mobile-first layout voor de wizard (prototype "needful. — PWA screens", 24 okt). Wie: R

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
- [~] `flow/`: vragen en volgorde als datamodel — *`Answers`-dataclass klaar; de volgorde zit nu in de routes `/vraag/1`…`/advies`*. Wie: R
- [x] `calc/`: duurzaamheidsscore /100 + tests. Wie: R
- [x] `calc/`: adviesbepaling (antwoorden → uitkomst) + tests. Wie: R
- [ ] API-endpoints voor de flow (start, antwoord, resultaat). Wie: ?
- [ ] Pydantic-schema's voor requests en responses. Wie: ?
- [ ] Rate limiting (`RATE_LIMIT_PER_MINUTE` staat al in `.env.example`). Wie: ?

### NiceGUI-webversie + PWA (18 u., sprint 2–3)

- [x] Wizard: vier schermen met voortgang (`ui/screens/q1–q4.py`). Wie: R
- [x] Resultaatscherm met advies en uitleg (`ui/screens/advies.py`). Wie: R
- [~] Wizard koppelen aan de API/flow — *schermen roepen `calc/` rechtstreeks aan; API-endpoints voor de flow nog niet*. Wie: ?
- [x] Responsive voor desktop en mobiel (telefoonkolom van max. 430 px, op desktop gecentreerd). Wie: R
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
- Python-versie vastpinnen? README zegt 3.12, maar `uv` kiest lokaal soms een nieuwere (bij Robin 3.15). Voorstel: `uv python pin 3.12`, `.python-version` uit `.gitignore` halen en committen.

## Wijzigingslog

| Datum | Wijziging |
|-------|-----------|
| 2026-10-29 | Eerste versie, status bepaald op basis van de repo |
| 2026-11-01 | Vragenwizard klikbaar (start → 4 vragen → advies) met huisstijl, score, adviesregels, logging en UI-tests (branch `feat/wizard-screens`) |
