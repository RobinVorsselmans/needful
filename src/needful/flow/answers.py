"""De antwoorden van  één gebruiker op de vier vragen. Geen NiceGUI hier.

De standaardwaarden zijn het voorbeeld uit de pitch (hogedrukreiniger).
"""

from dataclasses import asdict, dataclass, fields
from typing import Any

from needful.calc.advice import Need
from needful.calc.cost import total_uses
from needful.calc.score import Rating


@dataclass
class Answers:
    product: str = "hogedrukreiniger"
    need: Need = "handig"
    uses_per_year: int = 3
    years: int = 4
    price: float = 149.0
    postcode: str = "2000 Antwerpen"
    lifespan: Rating = "ja"
    repairable: Rating = "deels"
    recyclable: Rating = "nee"
    review: Rating = "ja"

    @property
    def total_uses(self) -> int:
        return total_uses(self.uses_per_year, self.years)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> tuple["Answers", list[str]]:
        """Bouw een object uit opgeslagen data met deze method, geeft ook terug wat ontbreekt"""
        names = [field.name for field in fields(cls)]
        known = {name: data[name] for name in names if name in data}
        missing = [name for name in names if name not in data]
        return cls(**known), missing
