# Explain me

Uitleg bij de code en de structuur van needful., zodat we allemaal kunnen uitleggen wat er gebeurt en waarom.
Dit is een aanvulling op de docstrings en commentaren in de code, geen vervanging.

> **Onderhoud:** voeg bij elke gemergede feature een stukje toe of pas het aan. Staat er iets in dat niet meer klopt, verbeter het in dezelfde PR.
> Dit document beschrijft de staat van **7 november 2026** (sprint 2–3: nieuwe vragenflow met LLM en zoeken in de buurt, branch `feat/smart-purchase-flow`). Delen die nog niet bestaan staan onder [Nog te bouwen](#nog-te-bouwen).

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

needful. is een beslissingshulp vóór je iets koopt. De gebruiker beantwoordt drie vragen (heb je het nodig, hoe vaak gebruik je het en wat kost het echt, moet het nieuw en van jou zijn, met meteen de keuze voor een alternatief) en krijgt één advies (koos je "Zet alles op een rij", met alle mogelijkheden en hun prijs): laten, lenen, huren, samen kopen, alternatief product, kopen & later doorverkopen of bewust kopen. Een taalmodel schat de extra kosten om mee rekening te houden, stelt alternatieven voor (met wat ze betekenen en een prijsindicatie) en geeft CO2 en een exit-strategie. Met postcode + gemeente zie je waar je het in je buurt kunt lenen, huren, tweedehands of nieuw kopen, of laten herstellen. Geen login en geen persoonsgegevens.

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
| `src/needful/calc/` | Rekenkern: kost per gebruik (ook met extra kosten), wat een optie kost over de gebruiksduur, score /100, advies, afstand, getalnotatie | `cost.py`, `score.py`, `advice.py`, `distance.py`, `format.py` |
| `src/needful/api/` | HTTP-endpoints (FastAPI) | `/health`, `/cost-per-use` |
| `src/needful/ui/` | NiceGUI: huisstijl, bouwstenen, opslag en de zes schermen | wizard klikbaar, PWA nog niet |
| `src/needful/flow/` | De antwoorden van één gebruiker | `answers.py` |
| `src/needful/alternatives/` | LLM (OpenRouter) en zoeken in de buurt (OpenStreetMap, repaircafe.org) | `llm.py`, `insights.py`, `nearby.py`, `relevance.py`, voorbeelden in `examples.py` |
| `src/needful/settings.py` | Instellingen uit `.env` (LLM-sleutel en -model) | klaar |
| `src/needful/voice/` | Spraak omzetten naar antwoorden | leeg (docstring) |
| `src/needful/db/` | Database-modellen, admin-module, cache | leeg (docstring) |
| `src/needful/logging_setup.py` | Logformaat en -niveau voor de hele app | klaar |
| `tests/` | pytest-tests, ook klikt-door-de-app-tests | 166 tests |
| `docs/concept/` | Pitch en voorontwerp (pdf) | bestaat |

De `src/`-layout (code in `src/needful/` en niet direct in de root) voorkomt dat je per ongeluk code importeert uit de werkmap in plaats van uit het geïnstalleerde package.

## 4. Bestand voor bestand

### `src/needful/calc/cost.py`

Bevat vier functies:

- `total_uses(uses_per_year, years)`: hoe vaak je het in totaal gebruikt. Dit is de **enige** plek waar die vermenigvuldiging staat; `cost_per_use`, de API-route en `Answers` gebruiken allemaal deze functie.
- `cost_per_use(price, uses_per_year, years)`:

- Berekent `prijs ÷ (gebruiken per jaar × jaren)` en rondt af op 2 decimalen.
- Voorbeeld uit de pitch: €149, 3× per jaar, 4 jaar → 12 gebruiken → **€12,42 per gebruik**.
- Geeft een `ValueError` bij een prijs ≤ 0 of als het totaal aantal gebruiken ≤ 0 is. De rekenkern weigert dus zelf ongeldige input en vertrouwt niet op de aanroeper.

- `total_cost(once, per_use, per_year, uses_per_year, years)`: wat iets kost over de hele gebruiksduur: eenmalig + per keer × aantal keer + per jaar × aantal jaar. Zo vergelijken we een alternatief met kopen: een wassalon van €6 per keer, 3× per jaar, 4 jaar → €72.
- `extra_cost(per_use, per_year, uses_per_year, years)`: de extra kosten om mee rekening te houden over de hele gebruiksduur, via `total_cost` zonder eenmalig deel. Pitch: €2,20 × 12 + €8 × 4 = **€58,40**.
- `real_cost_per_use(price, extra, uses_per_year, years)`: kost per gebruik mét die extra kosten: (€149 + €58,40) ÷ 12 = **€17,28**. Gebruikt `cost_per_use`, dus dezelfde foutcontroles.
- `energy_cost(kwh)` en `water_cost(liter)`: stroom en water per gebruik in euro, met de richtprijzen `EURO_PER_KWH = 0.30` en `EURO_PER_M3_WATER = 5.0` (schatting Vlaanderen 2025–2026, één plek om aan te passen). Pitch: 1,5 kWh → €0,45, 350 liter → €1,75. **Waarom niet het LLM laten rekenen?** In een test noemde een model 1 kWh aan €0,30 "€0,90" en 50 liter water "€1". Hoeveelheden schat een taalmodel goed, rekenen niet; dat doet `calc/`, met tests.
- `buying_pays_off_from(prijs, kopen_per_keer, kopen_per_jaar, alt_eenmalig, alt_per_keer, alt_per_jaar, jaren)`: vanaf hoeveel keer per jaar is zelf kopen goedkoper dan het alternatief? Kopen kost vooraf meer, een alternatief zoals een wassalon kost per keer meer; vanaf een bepaald aantal keer haalt kopen dat in. Wasmachine €600 + €0,79 per keer + €15 per jaar tegenover een wassalon van €7 per keer, 4 jaar → **27 keer per jaar**. `None` als kopen nooit goedkoper wordt (het alternatief kost per keer niet meer, bv. lenen).

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
from needful.ui.screens import advies, buurt, q1, q2, q3, start  # noqa: F401

setup_logging()

app = FastAPI(title="needful.", version="0.1.0")
app.include_router(api_router, prefix="/api")
ui.run_with(app, title="needful.", storage_secret="dev-only-change-me")
```

1. Importeert de zes schermen. Die import lijkt ongebruikt (daarom `# noqa: F401`), maar hij moet er staan: door de import worden de `@ui.page`-decorators uitgevoerd en zo bestaan de routes `/`, `/vraag/1` … `/advies` en `/buurt`.
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

`euro(149)` → `€149`, `euro(12.4)` → `€12,40`, `euro(1280)` → `€1.280`; `km(0.6)` → `0,6 km`; `kg(40)` → `40 kg` (CO2 bij "niet kopen"); `kwh(1.5)` → `1,5 kWh`; `liters(350)` → `350 liter`. `price_text(once, per_use, per_year)` maakt er één prijs van: `€25`, `€6 per keer + €10 per jaar`, of `gratis`. Komma als decimaalteken en punt per duizendtal, zoals een Belg leest. Ze gebruiken één interne hulpfunctie `_belgian(waarde, decimalen)`.

### `src/needful/calc/distance.py`

`distance_km(a, b)`: de afstand in vogelvlucht tussen twee punten (breedte, lengte), met de haversine-formule (de aarde is een bol, geen plat vlak). Afgerond op 0,1 km. Antwerpen → Brussel ≈ 42 km. Gebruikt door het zoeken in de buurt. We gebruiken bewust geen `locale`: dat hangt af van de instellingen van de computer of server.

### `src/needful/calc/score.py`

**Niet meer in de wizard** sinds de nieuwe vragenflow; de code en tests blijven staan tot de groep beslist of de score terugkomt.

`durability_score(lifespan, repairability, recyclability, review)`: vier criteria, elk `"ja"` / `"deels"` / `"nee"` = 100 / 50 / 0 punten, gemiddelde **naar beneden** afgerond met `int()`. Pitchvoorbeeld (ja, deels, nee, ja) → 62,5 → **62**. Niet `round()`: Python rondt 62,5 af naar 62 maar 63,5 naar 64 ("banker's rounding"), dus soms naar boven en soms naar beneden. Een onbekende waarde geeft een `ValueError`.

### `src/needful/calc/advice.py`

`decide(need, price, total_uses, alternatives, score=None)` geeft één `Advice` terug. De regels worden **in volgorde** gecontroleerd; de eerste die past, wint:

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
- `allowed(alternatives, access)` filtert eerst op het antwoord van vraag 3: `"nieuw"` (nieuw en van mij) → geen alternatieven, `"tweedehands"` → enkel tweedehands, `"toegang"` (lenen of huren mag) → alles. De regels zelf veranderen dus niet; ze krijgen alleen minder alternatieven.
- `score` is optioneel: de wizard vraagt de duurzaamheid niet meer. Zonder score laat regel 5 dat stukje van de zin weg. `score.py` en zijn tests blijven bestaan.
- `Alternative.distance_km` mag `None` zijn: een voorstel van het taalmodel ("lenen bij de buren") heeft geen afstand en telt voor regel 2 als dichtbij. De reden zegt dan "Lenen bij de buren: dat kan gratis." zonder km. Bij gelijke prijs gaat een gekende afstand voor.
- De alternatieven komen sinds deze versie van het taalmodel, per product (`insights.advice_alternatives()`): bij een droogkast is "huren" de wassalon, niet een verhuurder van €25 per dag.
- Ontbrekend (bewust): "samen kopen" en "alternatief product". Voor een ander product (droogrek i.p.v. droogkast) is er nu wel data, maar nog geen regel: het adviesscherm toont het in de vergelijking, de regels houden er nog geen rekening mee. Komen er meer regels bij, dan is het *strategy pattern* (elke regel een eigen klasse met `check()`, en `decide()` loopt over een lijst) de logische volgende stap.

### `src/needful/flow/answers.py`

`Answers` is een dataclass met de antwoorden van één gebruiker: product, behoefte (Q1), gebruik per jaar, jaren, prijs (Q2), `choice` (Q3: `nieuw`, `tweedehands`, `delen`, `alternatief`, of `alles` voor de knop "Zet alles op een rij"), `alternative` (de naam van het gekozen alternatief) en postcode + gemeente (zoeken in de buurt). De standaardwaarden zijn het pitchvoorbeeld. `answers.access` is een `@property`: wat de adviesregels uit `choice` moeten weten (nieuw, tweedehands of toegang). `tweedehands` betekent: het moet van jou zijn, nieuw of tweedehands; lenen en huren tellen dan niet mee. `Choice` staat hier en niet in `calc/`, want de rekenkern kent enkel `Access`.

- `answers.total_uses` is een `@property`: leest als een veld, maar rekent via `calc/cost.py`.
- `to_dict()` / `Answers.from_dict(data)` zetten om van/naar een dict, want NiceGUI bewaart JSON. `from_dict` geeft ook terug **welke velden ontbraken**; de UI logt die als WARNING.

### `src/needful/alternatives/examples.py`

De vaste `EXAMPLE_ALTERNATIVES` (gereedschapsbib, buren, verhuur, tweedehands) zijn weg: het advies rekent nu met de alternatieven van het taalmodel, of zonder taalmodel met die van het voorbeeld hieronder.

`EXAMPLE_INSIGHTS` is wat de schermen tonen als het taalmodel niet bereikbaar is: de extra kosten (1,5 kWh en 350 liter per keer, €8 onderhoud per jaar), twee alternatieven (tuinslang + borstel voor €25, lenen bij de buren), CO2 en de exit-strategie van de hogedrukreiniger. De schermen zetten er dan "voorbeeld · taalmodel niet bereikbaar" onder.

### `src/needful/settings.py`

Leest instellingen uit omgevingsvariabelen of uit `.env`, met `pydantic-settings`. Nu enkel `OPENROUTER_API_KEY` en `OPENROUTER_MODEL`. Een omgevingsvariabele wint van `.env`; daarom kan `tests/conftest.py` de sleutel in elke test leeg zetten.

### `src/needful/alternatives/llm.py`

`ask(system, prompt, answer)` stelt één vraag aan OpenRouter en geeft een Pydantic-object van het type `answer` terug, of `None`.

- Het JSON-schema van het Pydantic-model gaat mee als `response_format` met `strict: true`: het model **moet** in precies die vorm antwoorden. `provider.require_parameters` laat OpenRouter enkel providers kiezen die dat ondersteunen.
- `parse_answer()` controleert het antwoord daarna nog eens met Pydantic. Twee lagen, net als bij de API.
- Geen sleutel, netwerkfout, timeout (30 s) of ongeldig antwoord → `None` en een WARNING in de log. **De aanroeper kiest de fallback**, de app loopt nooit vast door het LLM.
- Elke geslaagde vraag logt model, duur en `usage` (tokens en kost): de basis voor de admin-module.

### `src/needful/alternatives/insights.py`

Eén LLM-vraag per product levert alles wat de schermen nodig hebben, in het Pydantic-model `ProductInsights`:

| Veld | Scherm |
|------|--------|
| `kwh_per_use`, `liters_per_use`: stroom en water per gebruik, als **hoeveelheid** | vraag 2 (in euro via `calc/cost.py`) |
| `extra_costs`: andere extra kosten als `ExtraCost` (naam, `per_use`, `per_year`, uitleg) | vraag 2 |
| `alternatives`: 1 tot 3 `Suggestion`s, het beste eerst: naam, `kind` (lenen, huren, tweedehands of ander product), `search_term` (zoals op 2dehands: "droogrek"), `meaning` (wat het in de praktijk betekent), prijsindicatie (`once`, `per_use`, `per_year`), `place` (welke soort plaats we in de buurt zoeken, bv. `wassalon`) en `shop_types` (bij een ander product: waar het nieuw ligt) | vraag 3, het advies en zoeken in de buurt |
| `co2_kg`, `exit_tip` | advies (bij "niet kopen" en "nieuw kopen") |
| `shop_types`: OSM-winkeltypes waar het nieuw te koop is | zoeken in de buurt |

`insights.advice_alternatives(per_jaar, jaren)` zet de alternatieven om naar de `Alternative`s van `calc/advice.py`: huren en lenen met hun prijs per keer (een abonnement verrekend over het gebruik), tweedehands met de aankoopprijs, zonder afstand. Een wassalon is "huren". Een ander product laat het weg, want daar is nog geen regel voor.

Kies je een alternatief, dan stelt `alternative_details()` een **tweede, kleine vraag**: `AlternativeDetails` met `steps` (hoe begin je eraan), `pros` en `cons`. De prompt krijgt de prijsindicatie van vraag 3 mee, zodat de uitleg niet met een andere prijs komt. `insights.alternative(naam)` zoekt het gekozen alternatief op (anders het beste), `insights.rates()` geeft alle extra kosten samen als (per keer, per jaar).

Een alternatief kan een ander product zijn (tuinslang + borstel), een dienst (wassalon in plaats van wasmachine) of een manier (huren, lenen). Het scherm rekent met `Suggestion.total_cost()` uit wat het kost over dezelfde gebruiksduur als kopen: "12 keer in 4 jaar: €25 · kopen: €207,40".

- `model_config = ConfigDict(extra="forbid")` maakt het schema strikt (een test controleert dat).
- `place` is een `Literal` (vaste keuzelijst `AlternativePlace` uit `nearby.py`): in het JSON-schema wordt dat een `enum`, dus het LLM kan geen soort plaats verzinnen die we niet kunnen zoeken.
- `product_insights(product)` ruimt vergissingen van het LLM op: negatieve bedragen weg, hoogstens 4 kosten en 3 alternatieven, enkel winkeltypes uit `SHOP_TYPES`. Dat laatste is ook veiligheid: die tekst komt in de Overpass-query.
- `SHOP_TYPES` in `nearby.py` geeft per winkeltype een korte Belgische uitleg met ketens ("warenhuis (Inno, HEMA): mode, cosmetica, kleine huishoudspullen, geen groot huishoudtoestel"). Die gaat mee in de prompt. Zonder die uitleg koos het model "warenhuis" voor een wasmachine, en dacht het dat Inno witgoed verkoopt. **Ontbreekt een winkeltype, dan zoeken we er niet naar**: zonder `motorcycle` koos het model "sportwinkel" voor een motorfiets, en vonden we de Suzuki-dealer in Gent niet. Daarom staan er ook types voor grotere aankopen in (motorzaak, autodealer, muziekinstrumenten, beddenzaak …). Past er geen enkel type, dan geeft het model een lege lijst en zoeken we geen nieuwe winkels, liever dan verkeerde.
- De systeemprompt zegt ook dat het om Belgisch-Nederlands gaat: een droogkast is een wasdroger (het model dacht eerst dat dat iets anders was).
- `insights.costs()` geeft stroom en water (door ons omgerekend) plus de andere extra kosten; `insights.extra_cost(per_jaar, jaren)` telt ze op via `calc/cost.py`.
- De opdracht zegt uitdrukkelijk: wat bij elk gebruik terugkomt staat per keer, niet per jaar (een model zette wasmiddel "per jaar voor 4 wasbeurten per week"), en enkel alternatieven die een gewone Vlaming echt zou overwegen (een model stelde "handwas met emmer" voor).

### `src/needful/alternatives/nearby.py`

Zoekt plaatsen binnen 5 km van postcode + gemeente. Elke plaats (`Place`) krijgt een tag per mogelijkheid: `kopen`, `huren`, `lenen`, `tweedehands`, `herstellen`, `alternatief`.

| Bron | Hoe | Wat |
|------|-----|-----|
| **Nominatim** (OpenStreetMap) | API | postcode + gemeente → punt op de kaart |
| **Overpass** (OpenStreetMap) | API, open data (ODbL) | doe-het-zelf-, tuin- en andere winkels (`shop=...`), tweedehands en Kringwinkel, verhuur, herstellers, uitleenpunten (op tag of naam: "gereedschapsbib", "uitleendienst" …) |
| **repaircafe.org** | scraping met httpx + BeautifulSoup | alle Repair Cafés: de bezoekpagina bevat ze als drie JavaScript-lijsten (`locations`, `titles`, `markers_content`). `js_list()` haalt ze eruit met een reguliere expressie, BeautifulSoup leest link en adres uit de HTML-popup |

- `tags_for(osm_tags, winkeltypes, alternatieven)` beslist de tags uit de echte data: een doe-het-zelfzaak met `rental=...` krijgt `kopen` én `huren`, een winkel met `second_hand=only` is geen `kopen`, een wassalon (`shop=laundry`) is een `alternatief` als het LLM een wassalon voorstelde.
- `ALTERNATIVE_PLACES` koppelt elke soort plaats voor een alternatief aan een OSM-tag: `wassalon` → `shop=laundry`, `carwash` → `amenity=car_wash`, `fietsverhuur` → `amenity=bicycle_rental` … Enkel die tags komen in de query, nooit tekst van het LLM.
- **Wat de tags níet weten:** OSM zegt welk soort winkel het is, niet wat er in de rekken ligt. Oxfam is `shop=charity` en Boels `shop=rental`, maar voor een wasmachine heb je er niets aan. Daarom krijgt elke plaats ook `about` (bv. `shop=charity, brand=Oxfam, branch=wereldwinkel`) en kijkt `relevance.py` de lijst na.
- `grouped()` zet alles op een rij: per soort (nieuw kopen, huren, lenen, tweedehands, herstellen, alternatief) de 5 dichtste plaatsen. Een plaats met twee tags (Hubo: kopen én huren) staat in twee groepen. Hoogstens 5 per soort, want Antwerpen heeft tientallen wassalons en honderden Velo-stations.
- `alternative_tags(soorten_plaatsen, winkels)` maakt de OSM-tags van de alternatieven: `wassalon` → `shop=laundry`, en voor een ander product (droogrek) de winkels waar het ligt (`shop=houseware`).
- `second_hand_url(product, postcode)` bouwt een zoekopdracht op 2dehands binnen 10 km: `https://www.2dehands.be/q/wasmachine/#postcode:2000|distanceMeters:10000`. Dat is **enkel een link**, we scrapen 2dehands niet. Het formaat (filters achter `#`, `sleutel:waarde`, gescheiden door `|`) komt uit de eigen JavaScript van 2dehands.
- Overpass zoekt in een rechthoek (`bbox()`, sneller dan een cirkel); `parse_osm()` gooit wat in de hoeken buiten 5 km valt weg.
- Elk antwoord blijft **één dag in het geheugen** (`fresh()`): de publieke Overpass-server is gratis en vaak druk (dan 20 à 60 s), de Repair Café-pagina is ± 3 MB.
- Antwoordt Overpass met 429, 502, 503 of 504 ("druk"), dan wacht `osm_places()` 3 s en probeert het nog één keer. De publieke reserveservers (kumi, private.coffee, mail.ru) antwoordden in onze tests niet, daarom staan ze er niet in.
- `search()` vraagt beide bronnen **tegelijk** en geeft elke bron terug zodra ze klaar is. Faalt er één, dan logt hij een WARNING en gaan de andere resultaten gewoon door.
- Niet gebruikt, bewust: Brico en Gamma blokkeren scrapers (403 en een browsercheck), en een centrale lijst van uitleendiensten vonden we niet voor Vlaanderen. De meeste staan wel op OpenStreetMap, als winkel of met hun naam.

### `src/needful/alternatives/relevance.py`

`check_places(product, plaatsen, alternatieven)` laat het taalmodel de gevonden plaatsen nakijken: past deze plaats bij **dit** product?

- De prompt toont de 40 dichtste plaatsen genummerd, met wat we weten (`about`) en onze tags. Per plaats geeft het model eerst een korte reden (`reason`, ook in de DEBUG-log), dan de tags die echt kloppen. Eerst de reden, dan pas de tags: zo denkt het model na vóór het beslist.
- `apply()` houdt enkel bevestigde plaatsen en tags over, en **het model kan enkel weghalen, nooit bijverzinnen**: een tag die wij niet hadden, telt niet.
- Geen antwoord van het LLM → `None`, en het scherm toont de plaatsen zoals ze zijn, met "Niet nagekeken op …: het taalmodel is niet bereikbaar."
- De prompt bevat ook een **legende** (`legend()`): de Belgische uitleg van elk winkeltype dat in de lijst voorkomt (uit `SHOP_TYPES` en `OTHER_SHOPS`), bv. "charity: liefdadigheidswinkel (Oxfam): vooral kleding, boeken, fairtrade-voeding".
- Getest op een wasmachine in Antwerpen: Oxfam, een kledingboetiek, een kassazaak (MyPOS), fietsverhuur en een gsm-hersteller vallen weg, de Kringwinkels blijven (met `claude-haiku-5.5`). Met de legende vallen ook Inno en HEMA weg ("warenhuis zonder grote huishoudtoestellen").

### `src/needful/ui/theme.py`

De huisstijl uit het prototype, op één plek:

- **Kleuren als constanten** (`INK`, `PAPER`, `YELLOW`, `GREEN` …).
- **CSS-klassen** die met `nf-` beginnen: tekststijlen (`nf-h1`, `nf-display`, `nf-lead`, `nf-body`, `nf-big`, `nf-mono`), kleuren (`nf-muted`, `nf-faint`, `nf-soft`), knoppen (`nf-btn`, `nf-dark`, `nf-yellow`, `nf-choice`), en per scherm wat extra (kaart en pinnen, nu niet in gebruik; kaders en "Alles op een rij" op het advies (`nf-advised`, `nf-chosen`); tags `nf-tag-kopen` … `nf-tag-laten` bij alles op een rij en zoeken in de buurt).
- `apply_theme(background)` voegt lettertypes, CSS en achtergrondkleur toe aan de huidige pagina.

**Afspraak:** schermen bevatten geen kleurcodes of vaste px-maten, alleen klassenamen. Enige uitzondering: waarden die uit de data komen (de positie van een pin op de kaart, de kleur van een balkje in de voortgangsbalk). Sommige klassen eindigen op de soort (`nf-row-lenen`, `nf-pin-huren`), zodat een scherm de naam rechtstreeks uit de data kan bouwen: `f"nf-row-{alt.kind}"`.

De Google Fonts worden nu online geladen. Voor een PWA die offline werkt moeten ze later in het project zelf komen.

### `src/needful/ui/components.py`

Bouwstenen die op meerdere schermen terugkomen:

- `screen(naam, achtergrond)`: past het thema toe, logt "scherm geopend" en geeft de smalle kolom (max. 430 px, telefoonbreedte) terug. Elk scherm begint met `with screen("vraag 1"):`.
- `logo()`, `header(stap)` (logo, "VRAAG n/3" en de voortgangsbalk), `button(tekst, actie, stijl)` en `nav(terug, volgende)` (de "← Terug / Volgende →"-rij onderaan; met `on_next` doet de knop eerst iets, bv. bewaren).
- `options_overview(mogelijkheden, antwoorden, advised, chosen, compact, title)`: mogelijkheden op een rij op een donkere kaart, met als titel "Alles op een rij", "Vergelijking" of "Jouw keuze". Per mogelijkheid een label (nieuw, tweedehands, huren, lenen, ander product, niet kopen), de naam, het totaal en de prijs per keer, met "★ ONS ADVIES" en "JOUW KEUZE" erbij. `chosen_names()` vertaalt de keuze van vraag 3 naar die namen.
- `show_details(uitleg)`: de stappen, voordelen en aandachtspunten van het taalmodel over een gekozen alternatief.
- `example_note()`: het labeltje "voorbeeld · taalmodel niet bereikbaar".
- `waiting(tekst)`: een spinner mét uitleg ("Nog aan het zoeken bij OpenStreetMap. Dat kan tot een halve minuut duren."). Wie ziet waarop hij wacht, haakt minder snel af. Overal waar we op het LLM of een bron wachten.
- `alternative_card(alternatief, antwoorden, kopen_totaal, on_choose, chosen)`: één alternatief met prijsindicatie, uitleg en vergelijking met kopen; met `on_choose` staat er een knop "Kies dit alternatief →" onder (vraag 3).
- `alternative_verdict(alternatief, antwoorden, inzichten)`: "Je bespaart €… tegenover kopen" (of "Kopen is €… goedkoper") en vanaf hoeveel keer per jaar zelf kopen loont, via `buying_pays_off_from()` uit `calc/cost.py`.

### `src/needful/ui/storage.py`

Bewaart de antwoorden **per browser** in `app.storage.user` (NiceGUI koppelt die aan een cookie). Ze blijven bewaard bij herladen en werken met de terugknop van de telefoon.

- `start_new(product)`: de Start-knop zet álle antwoorden op het voorbeeld, met het gekozen product, en wist het bewaarde LLM-antwoord.
- `load_answers()`: leest de antwoorden; ontbreekt er iets, dan een WARNING met de veldnamen.
- `save_answer(veld, waarde)`: bewaart één antwoord meteen bij elke wijziging en logt het.
- `load_insights(product)`: het LLM-antwoord voor dit product. De eerste keer vraagt hij het (via `insights.py`) en bewaart hij het, daarna leest hij het. Vraag 2, 3, 4, het advies en de buurt kosten samen dus **één** LLM-vraag. Geeft ook terug of het het voorbeeld is.

### `src/needful/ui/screens/`

Eén bestand per scherm, elk met een `@ui.page`:

| Bestand | Route | Wat |
|---------|-------|-----|
| `start.py` | `/` | product invullen, Start |
| `q1.py` | `/vraag/1` | heb je het écht nodig? 4 keuzes, klikken = bewaren en door |
| `q2.py` | `/vraag/2` | gebruik per jaar, jaren, prijs → live "= €12,42 per gebruik". Daaronder "Extra kosten om mee rekening te houden" (stroom en water door ons berekend, de rest van het LLM) en "Met extra kosten: €17,28 per gebruik". Micknop staat er al, maar is uitgeschakeld (spraak = sprint 4) |
| `q3.py` | `/vraag/3` | moet het per se nieuw en van jou? de laatste vraag, hier beslis je ook. 4 keuzes ("Ja, nieuw en van mij", "Van mij, maar tweedehands mag", "Nee, lenen of huren is ook goed", "Zet alles op een rij"), klikken = bewaren en naar het advies. Bovenaan "Alternatieven": 1 tot 3 alternatieven van het LLM (niet altijd goedkoper, daarom niet "slimmere"), elk met prijsindicatie, wat het betekent, wat het kost tegenover kopen en een knop "Kies dit alternatief →" (bewaart `choice="alternatief"` en de naam). Onderaan "Toon mijn advies →": naar het advies met de keuze die er al staat (standaard `choice="alles"`) |
| `advies.py` | `/advies` | het advies op basis van de alternatieven van het taalmodel, bespaard bedrag en reden. Koos je "Zet alles op een rij", dan "Alles op een rij" (`insights.options()`): nieuw kopen (mét extra kosten en exit-strategie), elk alternatief (lenen, huren · wassalon, tweedehands, ander product zoals een droogrek) en niet kopen (bespaard € en CO2), met "★ ons advies". Bij een andere keuze een "Vergelijking": enkel nieuw kopen, je keuze ("jouw keuze") en wat de regels aanraden. Koos je een alternatief, dan gaat het er verder op in: wat het je bespaart, vanaf hoeveel keer per jaar kopen toch loont, en (van het LLM) hoe je eraan begint. "Zoek in mijn buurt", "← Terug" naar vraag 3, 👍/👎 |
| `buurt.py` | `/buurt` | `focus()` bepaalt volgens je keuze op vraag 3 wat we zoeken en tonen. "Zet alles op een rij": het product én alle alternatieven tegelijk (winkels van het product, wassalons, winkels voor een droogrek), alle soorten, en bovenaan alles op een rij (kort). Een gekozen ander product (droogrek): enkel dat, in zijn eigen winkels. "Lenen of huren" of een gekozen wassalon: enkel huren, lenen en die alternatieven. "Nieuw": enkel nieuw kopen. "Van mij, maar tweedehands mag" betekent nieuw én tweedehands: we zoeken en tonen allebei ("Nieuw kopen" met bv. de motordealers, en "Tweedehands"), en het advies markeert allebei als "jouw keuze". Kies je uitdrukkelijk een tweedehands alternatief, dan staan de gewone verkooppunten er als "Verkooppunten · vraag naar tweedehands" (een motordealer verkoopt vaak, niet altijd, occasies; OpenStreetMap noteert dat zelden). Bovenaan dan "Jouw keuze" met de prijs. Een knop "Bekijk tweedehands … op 2dehands ↗" per ding dat je volgens je keuze kunt kopen (niet bij huren, lenen of nieuw), met de postcode die er bij het klikken staat. Postcode + gemeente → de plaatsen per soort (nieuw kopen, tweedehands, huren, lenen, herstellen, alternatieven), per bron nagekeken door het LLM. `?terug=` mag enkel naar `/advies` |

Let op in `q1.py`, `q3.py` en `buurt.py`: `lambda need=need: choose(need)`. Zonder `=need` onthoudt elke knop pas bij het klikken welke `need` er is, en dan is de lus al voorbij: alle knoppen zouden de laatste waarde bewaren.

**Schermen die het LLM gebruiken zijn `async`.** Ze bouwen eerst de pagina (met een spinner), wachten dan met `await ui.context.client.connected()` tot de browser verbonden is, en vragen pas daarna het taalmodel. Zo zie je meteen iets, ook al duurt het LLM een paar seconden (NiceGUI wacht anders hoogstens 3 s op een pagina). Het advies vraagt pas na het verbinden de uitleg over een gekozen alternatief op, en kijkt dan eerst of dat stuk van de pagina nog bestaat (`is_deleted`).

NiceGUI laat je de UI in Python schrijven. Er is dus geen aparte JavaScript-frontend, dat was een bewuste keuze.

### Tests (`tests/`)

| Bestand | Wat |
|---------|-----|
| `test_cost.py` | kost per gebruik en `total_uses`, ook de foutgevallen; extra kosten en de echte kost per gebruik (pitch €58,40 → €17,28); `total_cost` (eenmalig, per keer, per jaar); stroom en water in euro (1 kWh → €0,30, 50 liter → €0,25); vanaf hoeveel keer per jaar kopen loont (wassalon → 27, ook net op de grens) |
| `test_format.py` | euro-, km-, kg-, kWh- en liternotatie, duizendtallen, `price_text` (ook "gratis") |
| `test_distance.py` | afstand 0, Antwerpen–Brussel ≈ 42 km, heen = terug |
| `test_score.py` | pitch = 62, alles ja = 100, alles nee = 0, naar beneden afronden, foute waarde |
| `test_advice.py` | elke regel, de volgorde, grensgevallen (2,0 vs 2,1 km; 24 vs 25 keer), zinnen zonder aan elkaar geplakte woorden; `allowed()` per antwoord op vraag 3, advies zonder score; lenen zonder gekende afstand, een wassalon als huren |
| `test_answers.py` | standaardwaarden, bewaren en terugladen, ontbrekende velden |
| `test_insights.py` | OpenRouter-antwoord lezen (goed, geen JSON, veld ontbreekt), geen sleutel = geen LLM, het schema is strikt, LLM-vergissingen opgeruimd (ook te veel alternatieven), kost van een alternatief, enkel gekende soorten plaatsen, stroom en water door ons berekend; het gekozen alternatief opzoeken, de tweede vraag (strikt schema, prijs in de prompt, te lange lijsten ingekort), Belgische uitleg bij winkeltypes |
| `test_relevance.py` | enkel bevestigde plaatsen en tags blijven, het LLM kan geen tags toevoegen, de prompt toont nummer en soort plaats en legt enkel de winkeltypes uit die voorkomen, zonder LLM niets nagekeken |
| `test_nearby.py` | tags per soort plaats (ook wassalon als alternatief), adressen, `about`, de bbox, hoogstens 5 alternatieven, de 2dehands-link, een tweede poging als Overpass druk is (nagemaakt netwerk), Overpass-antwoord en Repair Café-pagina lezen (met kleine nagemaakte voorbeelden, **geen internet**), een veranderde site geeft een duidelijke fout |
| `test_logging_setup.py` | niveau uit `LOG_LEVEL` |
| `test_ui_flow.py` | een gesimuleerde gebruiker klikt door de app: start → advies "lenen" (met €17,28, het alternatief en €207,40 bespaard), impulsaankoop → "laten", nieuw en van mij → "bewust kopen", exit-strategie, terugknoppen (ook op het advies), zoeken in de buurt met vervangen bronnen (ook de wachttekst terwijl een bron bezig is), "Zet alles op een rij" als vierde keuze, de vergelijking bij een eigen keuze, geen vraag 4 meer, een alternatief kiezen op vraag 3 en de verdere uitleg in het advies, het advies voor een droogkast (wassalon en droogrek, geen verhuurder van €25 per dag), de buurt per soort en met alle alternatieven bij "alles" (wassalons en winkels met droogrekken, 2dehands-knoppen voor droogkast en droogrek), en enkel het gekozen droogrek of enkel huren en lenen bij een eigen keuze, `?terug=` enkel naar eigen schermen, `/advies` rechtstreeks openen geeft een waarschuwing in de log |
| `conftest.py` | zet NiceGUI's `user`-testhulp aan, en zet in elke test de LLM-sleutel leeg (dus nooit een echte LLM-vraag) |

### `pyproject.toml`

De projectdefinitie: naam, Python ≥ 3.12, dependencies, dev-dependencies (pytest, pytest-asyncio, pytest-cov, ruff) en de configuratie van ruff (regellengte 100) en pytest (`tests/` als testmap, `asyncio_mode = "auto"` voor de `async`-UI-tests en `main_file` zodat de testgebruiker weet welke app hij moet starten). Een deel van de dependencies (SQLModel, Alembic, psycopg) wordt nog niet gebruikt, ze staan klaar voor latere sprints. httpx, BeautifulSoup en pydantic-settings zijn sinds het LLM en het zoeken in de buurt wel in gebruik.

### `uv.lock`

Legt exacte versies vast zodat iedereen dezelfde versies heeft. Niet met de hand aanpassen en wel committen.

### `Dockerfile` en `docker-compose.yml`

- `Dockerfile`: pakt `python:3.12-slim`, kopieert de code, installeert het project met `pip` en start `uvicorn` op poort 8080 met `--reload` (herstart bij codewijziging). Dit is een **ontwikkel**-image, geen productie-image.
- `docker-compose.yml`: twee services.
  - `db`: PostgreSQL 16 met gebruiker/wachtwoord/database `needful`. Data blijft bewaard in de volume `pgdata`.
  - `app`: bouwt het Dockerfile, leest `.env`, krijgt een `DATABASE_URL` die naar de `db`-service wijst en mount de projectmap (`.:/app`) zodat codewijzigingen direct zichtbaar zijn.
- `docker-compose.override.yml` staat **niet in git** (lokale aanpassing): zet de database-poort op 5433 om een conflict met een lokale Postgres te voorkomen.

### `.env.example` en `.env`

`.env.example` is de sjabloon (staat in git), `.env` is jouw eigen kopie met echte waarden (staat in `.gitignore`, **nooit committen**). Variabelen: `DATABASE_URL`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `OLLAMA_BASE_URL`, `APP_PORT`, `RATE_LIMIT_PER_MINUTE`, `LOG_LEVEL`. Op dit moment leest de code `LOG_LEVEL` (`logging_setup.py`) en de twee `OPENROUTER_`-variabelen (`settings.py`); de rest komt met de database en Ollama.

**LLM aanzetten:** maak een sleutel op openrouter.ai, zet die in `.env` bij `OPENROUTER_API_KEY=` en herstart de app. Zonder sleutel werkt alles, maar zie je het voorbeeld van de hogedrukreiniger. Het model staat in `OPENROUTER_MODEL`: standaard `anthropic/claude-haiku-5.5`. We testten drie modellen op dezelfde wasmachine in Antwerpen (nov. 2026; kost per product = productinzichten + buurt nakijken):

| Model | Kost | Oordeel |
|-------|------|---------|
| `anthropic/claude-haiku-5.5` | ± $0,0026 | juist: Oxfam en kassazaak weg, Kringwinkels blijven; zinnige alternatieven (wassalon ± €7 per keer) |
| `openai/gpt-oss-120b` | ± $0,0011 | te streng (alle Kringwinkels weg), wassalon "€0,30 per keer", "handwas met emmer" |
| `google/gemini-2.5-flash-lite` | ± $0,0011 | te mild: Oxfam en een kassazaak blijven staan |

Haiku is ruim 2× duurder, maar duizend producten kosten nog altijd maar ± $2,60.

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
3. **Vraag 2**: `cost_per_use(149, 3, 4)` uit `calc/` toont meteen "= €12,42 per gebruik". Daarna vraagt `load_insights()` het taalmodel naar de extra kosten (zonder sleutel: het voorbeeld), `energy_cost(1.5)` en `water_cost(350)` maken er €0,45 en €1,75 per keer van, en het scherm toont "Met extra kosten: €17,28 per gebruik". Elke wijziging wordt meteen bewaard.
4. **Vraag 3**: de alternatieven komen uit het bewaarde LLM-antwoord, dus zonder nieuwe vraag. Tuinslang + borstel: "12 keer in 4 jaar: €25 · kopen: €207,40". "Nee, lenen of huren is ook goed" → `save_answer("choice", "delen")` → naar `/advies`. (Of "Zet alles op een rij": `choice="alles"`.)
5. **Advies** (`advies.py`): leest alle antwoorden, filtert de alternatieven met `allowed(..., "toegang")`, roept `decide(...)` aan en logt elke gecontroleerde regel (DEBUG) en het advies (INFO). Regel 2 past (gratis lenen bij de buren, 12 keer ≤ 24) → "Lenen is de slimste keuze.", €149 bespaard. Daaronder de vergelijking: nieuw kopen €207,40, lenen gratis (★ ons advies, jouw keuze) en huren €300 (jouw keuze). Met "Zet alles op een rij" staan ook de tuinslang (€25) en niet kopen ("Je bespaart €207,40 en ± 40 kg CO2.") erbij.
6. **In jouw buurt** (`buurt.py`, via de knop op het advies): bovenaan je keuze met prijs. Postcode + gemeente → `nearby.geocode()` → `nearby.search()` met wat `focus()` voor je keuze kiest; bij "lenen of huren" de winkels van het product (ook die verhuren) en de soorten plaatsen van de huur- en leenalternatieven. Elke bron die binnenkomt, gaat eerst langs `relevance.check_places()` en verschijnt dan. De Repair Cafés staan er meestal eerst (cache), de winkels van OpenStreetMap volgen. De plaatsen staan per soort; boven de lijst staan de knoppen naar 2dehands.

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

- Tests staan in `tests/` en draaien met `uv run pytest` (166 tests, ± 7 seconden). Ze gebruiken nooit internet: het LLM staat uit (`conftest.py`) en de bronnen van `nearby.py` worden vervangen of krijgen nagemaakte voorbeelddata.
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
| `ui/` kaart | Echte OpenStreetMap-kaart met de plaatsen uit `/buurt` (postcode → coördinaten bestaat al, `nearby.geocode()`) | 3 |
| `db/` | SQLModel-modellen, Alembic-migraties, admin-gegevens, cache (de LLM- en buurtantwoorden staan nu per browser of één dag in het geheugen) | 1–3 |
| `alternatives/` | Ollama als lokaal LLM; afstanden uit het zoeken in de buurt meegeven aan het advies (nu kent het advies enkel de alternatieven, niet waar ze zijn) | 3 |
| verlanglijstje | 30-dagenregel ("Op mijn verlanglijstje", bv. als keuze op vraag 3; staat er nu niet) | versie 2 |
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
| **OpenStreetMap (OSM)** | Vrije wereldkaart die iedereen kan aanvullen. Elke plaats heeft *tags*, bv. `shop=doityourself`. |
| **Nominatim / Overpass** | Gratis diensten op OSM: Nominatim zoekt een adres of gemeente op, Overpass zoekt plaatsen met bepaalde tags. |
| **JSON-schema** | Beschrijving van de vorm van JSON (welke velden, welk type). We sturen het mee zodat het LLM in die vorm antwoordt. |
| **Token** | Stukje tekst (± ¾ woord) waarmee een LLM rekent, en waarvoor je betaalt. |
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

**Wat gebeurt er als het LLM niet antwoordt of onzin terugstuurt?**
`llm.ask()` geeft dan `None` en de schermen tonen het voorbeeld met "voorbeeld · taalmodel niet bereikbaar". Onzin houdt Pydantic tegen (verkeerde vorm), en `product_insights()` ruimt de rest op (negatieve kosten, onbekende winkeltypes).

**Waarom scrapen jullie Brico of Gamma niet?**
Ze blokkeren scrapers. OpenStreetMap geeft dezelfde winkels als open data, met adres, en dat mag je gebruiken als je de bron vermeldt (staat onder de resultaten). Repair Cafés staan niet op OSM, die scrapen we van repaircafe.org.

**Waarom mag het LLM bij het nakijken enkel tags weghalen?**
Wat er staat, komt uit echte data (OpenStreetMap). Het LLM weet beter wat een winkel verkoopt (Oxfam geen wasmachines), maar kan zich ook vergissen. Mag het alleen weghalen, dan kan het nooit een winkel of mogelijkheid verzinnen die er niet is; in het slechtste geval tonen we iets te weinig.

**Waarom laten jullie het LLM geen euro's voor stroom en water geven?**
Omdat het zich verrekent: 1 kWh aan €0,30 werd "€0,90". Het LLM geeft kWh en liter, `calc/cost.py` rekent om met vaste richtprijzen en tests.

**Waarom duurt zoeken in de buurt soms een halve minuut?**
De publieke Overpass-server is gratis en vaak druk. Daarom tonen we elke bron zodra ze klaar is en bewaren we elk antwoord een dag.

**Waarom zijn er dependencies die nog niet gebruikt worden?**
We hebben de stack vooraf gekozen en in één keer vastgezet. Ze worden in sprint 1–3 gebruikt (database, scraping).
