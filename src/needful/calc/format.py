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
