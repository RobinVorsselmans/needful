"""In jouw buurt: waar kun je het lenen, huren, tweedehands of nieuw kopen, of laten herstellen?

Twee bronnen, die we tegelijk bevragen:
- OpenStreetMap (open data, ODbL): Nominatim zet postcode + gemeente om naar een punt op de
  kaart, Overpass geeft de winkels en uitleenpunten in een straal rond dat punt.
- repaircafe.org (scraping): de kaart op de bezoekpagina bevat alle Repair Cafés als
  JavaScript-lijsten. Die lezen we uit met een reguliere expressie en BeautifulSoup.

Elke plaats krijgt één tag per mogelijkheid, uit de echte data: een doe-het-zelfzaak met
verhuur (OSM-tag rental=...) krijgt "kopen" én "huren". Die tags zeggen enkel welk soort winkel
het is; relevance.py laat het taalmodel nakijken of ze ook voor dít product kloppen.
Niet gebruikt: Brico en Gamma blokkeren scrapers, en een centrale lijst van uitleendiensten
bestaat niet. 2dehands scrapen we niet: we linken naar hun zoekopdracht (second_hand_url).
"""

import asyncio
import json
import logging
import math
import re
import time
from collections.abc import AsyncIterator, Coroutine
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import quote, quote_plus

import httpx
from bs4 import BeautifulSoup

from needful.calc.distance import distance_km

log = logging.getLogger(__name__)

Tag = Literal["kopen", "huren", "lenen", "tweedehands", "herstellen", "alternatief"]
TAGS: tuple[Tag, ...] = ("kopen", "huren", "lenen", "tweedehands", "herstellen", "alternatief")
Point = tuple[float, float]  # (breedte, lengte)

RADIUS_KM = 5
PER_TAG = 5  # alles op een rij: per soort de 5 dichtste (Antwerpen heeft honderden Velo-stations)
SECOND_HAND_KM = 10  # tweedehands op 2dehands: verder rijden mag
# Nominatim en Overpass vragen een herkenbare User-Agent (gebruiksvoorwaarden)
HEADERS = {
    "User-Agent": "needful/0.1 (schoolproject; +https://github.com/RobinVorsselmans/needful)"
}

SOURCES = ("OpenStreetMap", "Repair Café")  # zo heten ze in search() en op het scherm
NOMINATIM = "https://nominatim.openstreetmap.org/search"
OVERPASS = "https://overpass-api.de/api/interpreter"
REPAIR_CAFES = "https://www.repaircafe.org/nl/bezoeken/"
# Overpass is gratis en vaak druk (dan 30 s of meer), de Repair Café-pagina is ± 3 MB:
# elk antwoord één dag in het geheugen houden
CACHE_S = 24 * 3600
OVERPASS_TIMEOUT_S = 60
BUSY = (429, 502, 503, 504)  # Overpass is druk: na een korte pauze nog één keer proberen
RETRY_PAUSE_S = 3

# OpenStreetMap-winkeltypes (shop=...) waar iets nieuw te koop kan zijn. Het LLM kiest hieruit.
# De uitleg met Belgische ketens gaat mee in de prompts: zonder die uitleg dacht het model dat
# een warenhuis (Inno) wasmachines verkoopt. Ontbreekt een type, dan zoeken we er niet naar:
# zonder "motorcycle" koos het model "sports" voor een motorfiets en vonden we geen enkele dealer.
SHOP_TYPES = {
    "doityourself": "doe-het-zelfzaak (Brico, Gamma, Hubo): gereedschap, bouw, verf, tuin",
    "hardware": "ijzerwinkel: gereedschap, bevestiging, kleine huishoudspullen",
    "garden_centre": "tuincentrum: planten en tuingerief",
    "electronics": "elektronicazaak (MediaMarkt, Vanden Borre, Krëfel): ook huishoudtoestellen",
    "appliance": "elektrozaak voor huishoudtoestellen: wasmachine, droogkast, koelkast",
    "computer": "computerwinkel",
    "mobile_phone": "gsm-winkel: enkel gsm's en toebehoren",
    "furniture": "meubelzaak (IKEA)",
    "houseware": "huishoudwinkel: keukengerei, potten en pannen",
    "kitchen": "keukenzaak: inbouwkeukens",
    "sports": "sportwinkel (Decathlon)",
    "outdoor": "outdoorwinkel: kamperen, wandelen",
    "bicycle": "fietsenwinkel",
    "motorcycle": "motorzaak of motordealer (Suzuki, Yamaha, BMW): motorfietsen en scooters",
    "car": "autodealer of garage die auto's verkoopt",
    "car_parts": "auto-onderdelen en -accessoires",
    "toys": "speelgoedwinkel (Dreamland)",
    "baby_goods": "babywinkel (Dreambaby)",
    "clothes": "kledingwinkel",
    "shoes": "schoenenwinkel",
    "books": "boekhandel (Standaard Boekhandel)",
    "music": "platen- en cd-winkel",
    "musical_instrument": "muziekinstrumentenwinkel",
    "hifi": "hifi- en audiozaak",
    "video_games": "gamewinkel",
    "bed": "beddenzaak: matrassen en bedden",
    "lighting": "verlichtingswinkel",
    "pet": "dierenwinkel",
    "photo": "fotozaak",
    "department_store": "warenhuis (Inno, HEMA): mode, cosmetica, kleine huishoudspullen, "
    "geen groot huishoudtoestel",
}
# de andere winkeltypes die we zoeken, met uitleg voor het nakijken (relevance.py)
OTHER_SHOPS = {
    "second_hand": "tweedehandswinkel; een kringwinkel (De Kringwinkel) heeft van alles, "
    "ook toestellen",
    "charity": "liefdadigheidswinkel (Oxfam): vooral kleding, boeken, fairtrade-voeding",
    "rental": "verhuurzaak: van feestmateriaal en fietsen tot bouwmachines (Boels)",
    "repair": "herstelzaak",
}
SECOND_HAND_SHOPS = ("second_hand", "charity")
LEND_AMENITIES = ("toy_library", "tool_library", "library_of_things")
# uitleenpunten staan zelden met een eigen tag op de kaart, wel met zo'n naam
LEND_NAMES = r"gereedschapsbib|deelbib|uitleendienst|werkkot|toolbib|bib van dingen|leenbib"

# Soorten plaatsen voor een alternatief (vraag 3): een wassalon in plaats van een wasmachine.
# Het LLM kiest hieruit; de OSM-tag (sleutel, waarde) gebruiken we om ze in de buurt te zoeken.
AlternativePlace = Literal[
    "geen", "wassalon", "carwash", "copyshop", "fietsverhuur", "autodelen", "bibliotheek", "fitness"
]
ALTERNATIVE_PLACES: dict[str, tuple[str, str]] = {
    "wassalon": ("shop", "laundry"),
    "carwash": ("amenity", "car_wash"),
    "copyshop": ("shop", "copyshop"),
    "fietsverhuur": ("amenity", "bicycle_rental"),
    "autodelen": ("amenity", "car_sharing"),
    "bibliotheek": ("amenity", "library"),
    "fitness": ("leisure", "fitness_centre"),
}
# wat het taalmodel over een plaats te zien krijgt (zie relevance.py)
ABOUT_KEYS = ("shop", "amenity", "craft", "leisure", "brand", "branch", "rental", "second_hand")


@dataclass(frozen=True)
class Place:
    name: str
    address: str | None  # None: staat niet in de bron, de link toont het op de kaart
    distance_km: float
    tags: tuple[Tag, ...]
    url: str
    source: str
    about: str = ""  # wat de bron weet over het soort plaats, bv. "shop=charity, brand=Oxfam"


def tags_for(
    osm: dict[str, str], new_shops: set[str], alternatives: frozenset[tuple[str, str]] = frozenset()
) -> tuple[Tag, ...]:
    """Wat kun je hier? Op basis van de OSM-tags van één plaats, in de vaste volgorde van TAGS.
    `alternatives` zijn de OSM-tags van de alternatieven, bv. {("shop", "laundry")}."""
    shop = osm.get("shop")
    found: set[Tag] = set()
    if any(osm.get(key) == value for key, value in alternatives):
        found.add("alternatief")
    if shop in new_shops and osm.get("second_hand") != "only":
        found.add("kopen")
    if shop in SECOND_HAND_SHOPS or osm.get("second_hand") in ("yes", "only"):
        found.add("tweedehands")
    if shop == "rental" or "rental" in osm:
        found.add("huren")
    if osm.get("amenity") in LEND_AMENITIES or re.search(
        LEND_NAMES, osm.get("name", ""), re.IGNORECASE
    ):
        found.add("lenen")
    if shop == "repair" or osm.get("craft") == "electronics_repair" or osm.get("repair") == "yes":
        found.add("herstellen")
    return tuple(tag for tag in TAGS if tag in found)


def address(osm: dict[str, str]) -> str | None:
    """'Bredabaan 397, 2170 Antwerpen', of None als OSM geen adres heeft."""
    street = osm.get("addr:street", "")
    # een huisnummer zonder straat ("31") zegt niets
    if street and osm.get("addr:housenumber"):
        street += f" {osm['addr:housenumber']}"
    city = " ".join(filter(None, (osm.get("addr:postcode"), osm.get("addr:city"))))
    return ", ".join(filter(None, (street, city))) or None


def about(osm: dict[str, str]) -> str:
    """'shop=charity, brand=Oxfam, branch=wereldwinkel': genoeg voor het taalmodel om te zien
    wat voor plaats het is, zonder adressen of telefoonnummers."""
    return ", ".join(f"{key}={osm[key]}" for key in ABOUT_KEYS if key in osm)


def alternative_tags(places: list[str], shops: list[str] = ()) -> frozenset[tuple[str, str]]:
    """De OSM-tags van de alternatieven: soorten plaatsen (["wassalon", "geen"] → shop=laundry)
    en de winkels voor een ander product (["houseware"] → shop=houseware, voor een droogrek).
    Onbekende namen vallen weg."""
    found = {ALTERNATIVE_PLACES[place] for place in places if place in ALTERNATIVE_PLACES}
    return frozenset(found | {("shop", shop) for shop in shops if shop in SHOP_TYPES})


def bbox(origin: Point) -> tuple[float, float, float, float]:
    """Rechthoek (zuid, west, noord, oost) rond de cirkel van RADIUS_KM. Overpass zoekt in een
    rechthoek veel sneller dan in een cirkel; wat in de hoeken valt, filtert parse_osm weg."""
    lat, lon = origin
    dlat = RADIUS_KM / 111.32  # 1 breedtegraad ≈ 111,32 km
    dlon = RADIUS_KM / (111.32 * math.cos(math.radians(lat)))  # lengtegraden worden smaller
    return (round(lat - dlat, 4), round(lon - dlon, 4), round(lat + dlat, 4), round(lon + dlon, 4))


def overpass_query(
    origin: Point, new_shops: list[str], alternatives: frozenset[tuple[str, str]] = frozenset()
) -> str:
    shops = "|".join(sorted({*new_shops, *SECOND_HAND_SHOPS, "rental", "repair"}))
    # enkel tags uit ALTERNATIVE_PLACES, dus geen tekst van het LLM in de query
    extra = "".join(f'nwr["{key}"="{value}"];' for key, value in sorted(alternatives))
    return (
        f"[out:json][timeout:25][bbox:{','.join(map(str, bbox(origin)))}];("
        f'nwr["shop"~"^({shops})$"];'
        f'nwr["amenity"~"^({"|".join(LEND_AMENITIES)})$"];'
        f'nwr["name"~"{LEND_NAMES}",i];'
        'nwr["craft"="electronics_repair"];'
        f"{extra});out tags center;"
    )


def parse_osm(
    data: dict[str, Any],
    origin: Point,
    new_shops: set[str],
    alternatives: frozenset[tuple[str, str]] = frozenset(),
) -> list[Place]:
    """Overpass-antwoord → plaatsen. Zonder naam, zonder tag of te ver laten we een plaats weg."""
    places = []
    for element in data.get("elements", []):
        osm = element.get("tags", {})
        tags = tags_for(osm, new_shops, alternatives)
        # een punt (node) heeft lat/lon, een gebouw (way) of groep (relation) een middelpunt
        point = element if "lat" in element else element.get("center")
        if not osm.get("name") or not tags or point is None:
            continue
        km = distance_km(origin, (point["lat"], point["lon"]))
        if km > RADIUS_KM:
            continue
        places.append(
            Place(
                osm["name"],
                address(osm),
                km,
                tags,
                f"https://www.openstreetmap.org/{element['type']}/{element['id']}",
                "OpenStreetMap",
                about(osm),
            )
        )
    return places


def js_list(html: str, name: str) -> list[Any]:
    """Lees `var <name> = [...];` uit de pagina. Die lijsten zijn geldige JSON."""
    match = re.search(rf"var {name} = (\[.*?\]);\s*\n", html, re.DOTALL)
    if match is None:
        raise ValueError(f"lijst {name!r} niet gevonden, is repaircafe.org veranderd?")
    return json.loads(match.group(1))


def parse_repair_cafes(html: str, origin: Point) -> list[Place]:
    """De drie lijsten horen bij elkaar: plaats i staat op positie i in elke lijst."""
    locations = js_list(html, "locations")  # [[breedte, lengte], ...]
    titles = js_list(html, "titles")  # ["Repair Café Berchem", ...]
    popups = js_list(html, "markers_content")  # HTML met link en adres
    places = []
    for (lat, lon), title, popup in zip(locations, titles, popups, strict=True):
        km = distance_km(origin, (float(lat), float(lon)))
        if km > RADIUS_KM:
            continue
        # enkel de popups in de buurt parsen: er zijn er duizenden
        soup = BeautifulSoup(popup, "html.parser")
        link, where = soup.find("a", href=True), soup.find("p")
        places.append(
            Place(
                title,
                where.get_text(strip=True) if where else None,
                km,
                ("herstellen",),
                link["href"] if link else REPAIR_CAFES,
                "Repair Café",
                "Repair Café: vrijwilligers herstellen gratis wat je meebrengt",
            )
        )
    return places


def grouped(places: list[Place], per_tag: int = PER_TAG) -> dict[Tag, list[Place]]:
    """Alles op een rij: per soort (in de volgorde van TAGS) de dichtste plaatsen. Een plaats
    met twee tags (kopen én huren) staat in twee groepen; lege groepen vallen weg."""
    ordered = sorted(places, key=lambda place: place.distance_km)
    groups = {tag: [place for place in ordered if tag in place.tags][:per_tag] for tag in TAGS}
    return {tag: group for tag, group in groups.items() if group}


def second_hand_url(product: str, postcode: str) -> str:
    """Zoekopdracht op 2dehands rond de postcode: echte tweedehands toestellen met prijs.
    Enkel een link, we scrapen 2dehands niet. Filters staan achter # als sleutel:waarde,
    gescheiden door | (zo bouwt 2dehands ze zelf op)."""
    url = f"https://www.2dehands.be/q/{quote_plus(product.strip().lower())}/"
    if postcode.isdigit():
        url += f"#postcode:{quote(postcode)}|distanceMeters:{SECOND_HAND_KM * 1000}"
    return url


async def geocode(postcode: str, gemeente: str) -> Point | None:
    """Postcode + gemeente → punt op de kaart. None als we het niet vinden (of Nominatim faalt)."""
    params = {"postalcode": postcode, "city": gemeente, "countrycodes": "be", "format": "json"}
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            response = await client.get(
                NOMINATIM, params={key: value for key, value in params.items() if value}
            )
            response.raise_for_status()
            found = response.json()
    except (httpx.HTTPError, ValueError) as error:
        log.warning("gemeente opzoeken mislukt: %s", error)
        return None
    if not found:
        log.info("gemeente niet gevonden: %s %s", postcode, gemeente)
        return None
    return float(found[0]["lat"]), float(found[0]["lon"])


_cache: dict[str, tuple[float, Any]] = {}  # vraag → (opgehaald op, antwoord)


def fresh(key: str) -> Any | None:
    """Het bewaarde antwoord op deze vraag, als het jonger is dan CACHE_S."""
    found = _cache.get(key)
    return found[1] if found and time.time() - found[0] < CACHE_S else None


async def osm_places(
    origin: Point, new_shops: list[str], alternatives: frozenset[tuple[str, str]]
) -> list[Place]:
    # geen passend winkeltype (leeg)? Dan zoeken we geen nieuwe winkels, liever dan verkeerde
    shops = [shop for shop in new_shops if shop in SHOP_TYPES]
    query = overpass_query(origin, shops, alternatives)
    data = fresh(query)
    if data is None:
        async with httpx.AsyncClient(headers=HEADERS, timeout=OVERPASS_TIMEOUT_S) as client:
            response = await client.post(OVERPASS, data={"data": query})
            if response.status_code in BUSY:
                log.info("Overpass is druk (%s), nog één poging", response.status_code)
                await asyncio.sleep(RETRY_PAUSE_S)
                response = await client.post(OVERPASS, data={"data": query})
            response.raise_for_status()
        data = response.json()
        _cache[query] = (time.time(), data)
    return parse_osm(data, origin, set(shops), alternatives)


async def repair_cafes(origin: Point) -> list[Place]:
    html = fresh(REPAIR_CAFES)
    if html is None:
        async with httpx.AsyncClient(headers=HEADERS, timeout=60, follow_redirects=True) as client:
            response = await client.get(REPAIR_CAFES)
            response.raise_for_status()
        html = response.text
        _cache[REPAIR_CAFES] = (time.time(), html)
    return parse_repair_cafes(html, origin)


async def search(
    origin: Point,
    new_shops: list[str],
    alternative_places: list[str],
    alternative_shops: list[str],
) -> AsyncIterator[tuple[str, list[Place] | None]]:
    """Vraag alle bronnen tegelijk. Geef elke bron terug zodra ze klaar is (None = mislukt),
    zodat het scherm de snelle resultaten al toont terwijl de tragere bron nog laadt.
    `alternative_places`: soorten plaatsen uit ALTERNATIVE_PLACES, bv. ["wassalon"];
    `alternative_shops`: winkels voor een ander product, bv. ["houseware"] voor een droogrek."""

    async def run(
        source: str, job: Coroutine[Any, Any, list[Place]]
    ) -> tuple[str, list[Place] | None]:
        try:
            return source, await job
        except Exception as error:  # noqa: BLE001 (één bron die faalt, mag de rest niet stoppen)
            # %r: ook het soort fout, want een timeout heeft geen tekst
            log.warning("zoeken via %s mislukt: %r", source, error)
            return source, None

    jobs = [
        run(
            SOURCES[0],
            osm_places(origin, new_shops, alternative_tags(alternative_places, alternative_shops)),
        ),
        run(SOURCES[1], repair_cafes(origin)),
    ]
    for done in asyncio.as_completed(jobs):
        yield await done
