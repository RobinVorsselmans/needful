from typing import Literal

Rating = Literal["ja", "deels", "nee"]

POINTS: dict[str, int] = {"ja": 100, "deels": 50, "nee": 0}


def durability_score(
    lifespan: Rating, repairability: Rating, recyclability: Rating, warranty: Rating
) -> int:
    """Bereken de duurzaamheidsscore op basis van de vier criteria."""
    ratings = [lifespan, repairability, recyclability, warranty]
    for rating in ratings:
        if rating not in POINTS:
            raise ValueError(f"Onbekende waarde: {rating}, verwacht 'ja', 'deels' of 'nee'")
    return int(sum(POINTS[rating] for rating in ratings) / len(ratings))
