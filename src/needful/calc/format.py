"""Getallen tonen komma als decimaalteken en punt als duizendtallen."""


def _belgian(value: float, decimals: int) -> str:
    """Formatteer een getal volgens Belgische conventies."""
    if value == int(value):
        decimals = 0
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def euro(amount: float) -> str:
    """Formatteer een bedrag in euro."""
    return f"€{_belgian(amount, 2)}"


def km(amount: float) -> str:
    """Formatteer een afstand in kilometer."""
    return f"{_belgian(amount, 1)} km"


def kg(amount: float) -> str:
    """Formatteer een gewicht in kilogram."""
    return f"{_belgian(amount, 1)} kg"


def price_text(once: float = 0, per_use: float = 0, per_year: float = 0) -> str:
    """'€25', '€0,45 per keer' of '€6 per keer + €10 per jaar'. Niets = 'gratis'."""
    parts = []
    if once:
        parts.append(euro(once))
    if per_use:
        parts.append(f"{euro(per_use)} per keer")
    if per_year:
        parts.append(f"{euro(per_year)} per jaar")
    return " + ".join(parts) or "gratis"


def kwh(amount: float) -> str:
    """Formatteer stroomverbruik: '1,5 kWh'."""
    return f"{_belgian(amount, 1)} kWh"


def liters(amount: float) -> str:
    """Formatteer waterverbruik: '350 liter'."""
    return f"{_belgian(amount, 0)} liter"
