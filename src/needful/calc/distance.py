"""Afstand in vogelvlucht tussen twee punten op de kaart (breedte, lengte)."""

import math

EARTH_RADIUS_KM = 6371


def distance_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Haversine-formule: de afstand over het aardoppervlak, afgerond op 0,1 km."""
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return round(2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h)), 1)
