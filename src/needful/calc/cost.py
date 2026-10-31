"""Rekenkern: pure Python, geen I/O, volledig getest.

Voorbeeld uit de pitch: €149 · 3× per jaar · 4 jaar → €12,42 per gebruik.
"""


def total_uses(uses_per_year: int, years: int) -> int:
    """Totaal aantal gebruiken."""
    return uses_per_year * years

def cost_per_use(price: float, uses_per_year: int, years: int) -> float:
    """Kost per gebruik in euro, afgerond op 2 cijfers."""
    if price <= 0:
        raise ValueError("prijs moet groter zijn dan 0")
    uses = total_uses(uses_per_year, years)
    if uses <= 0:
        raise ValueError("aantal gebruiken moet groter zijn dan 0")
    return round(price / uses, 2)
