import json
from typing import get_args

import httpx
import pytest

from needful.alternatives import nearby
from needful.alternatives.nearby import (
    ALTERNATIVE_PLACES,
    AlternativePlace,
    Place,
    about,
    address,
    alternative_tags,
    bbox,
    grouped,
    overpass_query,
    parse_osm,
    parse_repair_cafes,
    second_hand_url,
    tags_for,
)
from needful.calc.distance import distance_km

ANTWERPEN = (51.2211, 4.3997)
DIY = {"doityourself", "hardware"}


def test_diy_shop_that_rents_gets_buy_and_rent():
    assert tags_for({"shop": "doityourself", "rental": "tools"}, DIY) == ("kopen", "huren")


def test_kringwinkel_is_second_hand():
    assert tags_for({"shop": "second_hand", "brand": "De Kringwinkel"}, DIY) == ("tweedehands",)


def test_tool_library_found_by_name():
    assert tags_for({"name": "Gereedschapsbib Berchem"}, DIY) == ("lenen",)


def test_shop_with_only_second_hand_is_not_buy_new():
    osm = {"shop": "electronics", "second_hand": "only"}
    assert tags_for(osm, {"electronics"}) == ("tweedehands",)


def test_repair_shop_is_repair():
    assert tags_for({"craft": "electronics_repair"}, DIY) == ("herstellen",)


def test_shop_that_does_not_sell_the_product_gets_no_tags():
    # een fietsenwinkel verkoopt geen hogedrukreinigers
    assert tags_for({"shop": "bicycle"}, DIY) == ()


def test_full_address():
    osm = {
        "addr:street": "Bredabaan",
        "addr:housenumber": "397",
        "addr:postcode": "2170",
        "addr:city": "Antwerpen",
    }
    assert address(osm) == "Bredabaan 397, 2170 Antwerpen"


def test_street_without_city():
    assert address({"addr:street": "Kroonstraat", "addr:housenumber": "8"}) == "Kroonstraat 8"


def test_no_address():
    assert address({"name": "Gamma"}) is None


def test_house_number_without_street_is_no_address():
    assert address({"addr:housenumber": "31"}) is None


def test_bbox_reaches_5_km_in_every_direction():
    south, west, north, east = bbox(ANTWERPEN)
    lat, lon = ANTWERPEN
    for edge in [(south, lon), (north, lon), (lat, west), (lat, east)]:
        assert distance_km(ANTWERPEN, edge) == 5.0


def test_query_asks_for_the_product_shops_in_the_bbox():
    query = overpass_query(ANTWERPEN, ["doityourself"])
    assert '"shop"~"^(charity|doityourself|rental|repair|second_hand)$"' in query
    assert "[bbox:51.1762,4.328,51.266,4.4714]" in query


OVERPASS = {
    "elements": [
        {
            "type": "node",
            "id": 1,
            "lat": 51.2300,
            "lon": 4.4100,
            "tags": {"name": "De Kringwinkel Antwerpen", "shop": "second_hand"},
        },
        {
            "type": "way",
            "id": 2,
            "center": {"lat": 51.2211, "lon": 4.4000},
            "tags": {"name": "Hubo", "shop": "doityourself", "rental": "tools"},
        },
        {"type": "node", "id": 3, "lat": 51.22, "lon": 4.40, "tags": {"shop": "hardware"}},
        {"type": "node", "id": 4, "lat": 51.22, "lon": 4.40, "tags": {"name": "Fietsen Jan"}},
        # in de hoek van de bbox: 6,3 km ver
        {
            "type": "node",
            "id": 5,
            "lat": 51.26,
            "lon": 4.46,
            "tags": {"name": "Brico", "shop": "doityourself"},
        },
    ]
}


def test_parse_osm_keeps_named_places_with_a_tag_within_5_km():
    places = parse_osm(OVERPASS, ANTWERPEN, DIY)
    # zonder naam (3), zonder iets wat je er kunt (4) en te ver (5) vallen weg
    assert [place.name for place in places] == ["De Kringwinkel Antwerpen", "Hubo"]
    hubo = places[1]
    assert hubo.tags == ("kopen", "huren")
    assert hubo.distance_km == 0
    assert hubo.url == "https://www.openstreetmap.org/way/2"
    assert hubo.address is None


def popup(url: str, where: str) -> str:
    return f'<div class="members-map-pin-popup"><a href="{url}">x</a><p>{where}</p></div>'


# Zo staan de Repair Cafés in de bezoekpagina van repaircafe.org (ingekort tot twee)
LOCATIONS = [[51.2050, 4.4330], [48.8566, 2.3522]]
TITLES = ["Repair Café Arthur - Antwerpen", "Repair Café Paris"]
POPUPS = [
    popup("https://www.repaircafe.org/cafe/arthur/", "Solvynsstraat 80, 2018 Antwerpen"),
    popup("https://www.repaircafe.org/cafe/paris/", "Paris"),
]
REPAIR_PAGE = f"""<script>
var locations = {json.dumps(LOCATIONS)};
var titles = {json.dumps(TITLES)};
var markers_content = {json.dumps(POPUPS)};
</script>"""


def test_repair_cafes_nearby_are_scraped():
    places = parse_repair_cafes(REPAIR_PAGE, ANTWERPEN)
    # Parijs ligt verder dan 5 km
    assert len(places) == 1
    arthur = places[0]
    assert arthur.name == "Repair Café Arthur - Antwerpen"
    assert arthur.address == "Solvynsstraat 80, 2018 Antwerpen"
    assert arthur.url == "https://www.repaircafe.org/cafe/arthur/"
    assert arthur.tags == ("herstellen",)
    assert 2 < arthur.distance_km < 3


def test_changed_repair_cafe_page_gives_a_clear_error():
    with pytest.raises(ValueError, match="locations"):
        parse_repair_cafes("<html>nieuwe site</html>", ANTWERPEN)


def test_grouped_shows_the_nearest_per_kind_in_a_fixed_order():
    hubo = Place("Hubo", None, 2, ("kopen", "huren"), "", "test")
    kringwinkel = Place("Kringwinkel", None, 1, ("tweedehands",), "", "test")
    brico = Place("Brico", None, 1, ("kopen",), "", "test")
    groups = grouped([hubo, kringwinkel, brico])
    # volgorde van TAGS: kopen, huren, lenen, tweedehands …; Hubo staat in twee groepen
    assert list(groups) == ["kopen", "huren", "tweedehands"]
    assert [place.name for place in groups["kopen"]] == ["Brico", "Hubo"]
    assert groups["huren"] == [hubo]


LAUNDRY = frozenset({("shop", "laundry")})


def test_laundromat_is_an_alternative_for_a_washing_machine():
    assert tags_for({"shop": "laundry", "name": "Wassalon"}, DIY, LAUNDRY) == ("alternatief",)


def test_laundromat_is_nothing_without_that_alternative():
    assert tags_for({"shop": "laundry", "name": "Wassalon"}, DIY) == ()


def test_alternative_tags_skip_unknown_and_none():
    assert alternative_tags(["wassalon", "geen", "kasteel"]) == LAUNDRY


def test_every_alternative_place_has_an_osm_tag():
    # de keuzes voor het LLM (AlternativePlace) en de tabel moeten gelijk blijven
    assert set(get_args(AlternativePlace)) == {"geen", *ALTERNATIVE_PLACES}


def test_query_also_asks_for_the_alternatives():
    assert 'nwr["shop"="laundry"];' in overpass_query(ANTWERPEN, ["appliance"], LAUNDRY)


def test_about_shows_what_kind_of_place_it_is_without_address():
    osm = {"shop": "charity", "brand": "Oxfam", "branch": "wereldwinkel", "phone": "03 123"}
    assert about(osm) == "shop=charity, brand=Oxfam, branch=wereldwinkel"


def test_parse_osm_gives_the_llm_something_to_check():
    kringwinkel = parse_osm(OVERPASS, ANTWERPEN, DIY)[0]
    assert kringwinkel.about == "shop=second_hand"


def test_grouped_keeps_at_most_5_per_kind():
    velo = [Place(f"Velo {i}", None, i / 10, ("alternatief",), "", "") for i in range(10)]
    hubo = Place("Hubo", None, 3, ("kopen", "huren"), "", "")
    groups = grouped([*velo, hubo])
    assert len(groups["alternatief"]) == 5
    assert groups["kopen"] == [hubo]


def test_alternative_tags_also_take_shops_for_another_product():
    # droogrek als alternatief: winkels met huishoudgerief tellen als alternatief
    assert alternative_tags(["wassalon"], ["houseware", "ruimteschip"]) == LAUNDRY | {
        ("shop", "houseware")
    }


def test_second_hand_link_searches_around_the_postcode():
    url = second_hand_url("Wasmachine", "2000")
    assert url == "https://www.2dehands.be/q/wasmachine/#postcode:2000|distanceMeters:10000"


def test_second_hand_link_with_two_words():
    assert second_hand_url("hoge drukreiniger", "").endswith("/q/hoge+drukreiniger/")


def test_second_hand_link_ignores_a_postcode_that_is_not_a_number():
    assert "#" not in second_hand_url("wasmachine", "Antwerpen")


def fake_overpass(monkeypatch, *statuses: int) -> list[int]:
    """Vervang het netwerk: Overpass antwoordt met deze statuscodes na elkaar."""
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        status = statuses[len(calls)]
        calls.append(status)
        return httpx.Response(status, json=OVERPASS if status == 200 else None)

    real_client = httpx.AsyncClient
    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kwargs: real_client(transport=transport, **kwargs)
    )
    monkeypatch.setattr(nearby, "RETRY_PAUSE_S", 0)
    monkeypatch.setattr(nearby, "_cache", {})
    return calls


async def test_busy_overpass_gets_a_second_try(monkeypatch):
    calls = fake_overpass(monkeypatch, 502, 200)
    places = await nearby.osm_places(ANTWERPEN, ["doityourself"], frozenset())
    assert calls == [502, 200]
    assert "Hubo" in [place.name for place in places]


async def test_busy_twice_gives_up(monkeypatch):
    calls = fake_overpass(monkeypatch, 504, 504)
    with pytest.raises(httpx.HTTPStatusError):
        await nearby.osm_places(ANTWERPEN, ["doityourself"], frozenset())
    assert calls == [504, 504]


async def test_other_errors_get_no_second_try(monkeypatch):
    calls = fake_overpass(monkeypatch, 400)
    with pytest.raises(httpx.HTTPStatusError):
        await nearby.osm_places(ANTWERPEN, ["doityourself"], frozenset())
    assert calls == [400]


def test_motorcycle_dealer_is_a_place_to_buy_a_motorcycle():
    # Suzuki Motorcenter in Gent staat op OSM als shop=motorcycle
    osm = {"shop": "motorcycle", "name": "Suzuki Motorcenter Degezelle"}
    assert tags_for(osm, {"motorcycle"}) == ("kopen",)


def test_no_fitting_shop_type_means_no_new_shops_in_the_query():
    # vroeger zochten we dan doe-het-zelfzaken, wat voor een motorfiets niets oplevert
    query = overpass_query(ANTWERPEN, [])
    assert '"shop"~"^(charity|rental|repair|second_hand)$"' in query
