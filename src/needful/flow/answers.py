"""De antwoorden van  één gebruiker op de drie vragen. Geen NiceGUI hier.

De standaardwaarden zijn het voorbeeld uit de pitch (hogedrukreiniger).
"""

from dataclasses import asdict, dataclass, fields
from typing import Any, Literal

from needful.calc.advice import Access, Need
from needful.calc.cost import total_uses

# vraag 3: wat koos je? "alles" = de knop "Zet alles op een rij" (geen eigen keuze)
Choice = Literal["alles", "nieuw", "tweedehands", "delen", "alternatief"]


@dataclass
class Answers:
    product: str = "hogedrukreiniger"
    need: Need = "handig"
    uses_per_year: int = 3
    years: int = 4
    price: float = 149.0
    choice: Choice = "alles"
    alternative: str = (
        ""  # naam van het alternatief dat je koos op vraag 3 (bij choice="alternatief")
    )
    postcode: str = "2000"
    gemeente: str = "Antwerpen"

    @property
    def total_uses(self) -> int:
        return total_uses(self.uses_per_year, self.years)

    @property
    def access(self) -> Access:
        """Wat de adviesregels moeten weten: moet het nieuw (of toch van jou) zijn?"""
        if self.choice == "nieuw":
            return "nieuw"
        if self.choice == "tweedehands":
            return "tweedehands"
        return "toegang"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> tuple["Answers", list[str]]:
        """Bouw een object uit opgeslagen data met deze method, geeft ook terug wat ontbreekt"""
        names = [field.name for field in fields(cls)]
        known = {name: data[name] for name in names if name in data}
        missing = [name for name in names if name not in data]
        return cls(**known), missing
