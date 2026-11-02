"""FastAPI-routes. Voorlopig enkel een health-check en de kost-per-gebruik."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from needful.calc.cost import cost_per_use, total_uses

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


class CostRequest(BaseModel):
    price: float = Field(gt=0, description="Nieuwprijs in euro")
    uses_per_year: int = Field(gt=0)
    years: int = Field(gt=0)


class CostResponse(BaseModel):
    cost_per_use: float
    total_uses: int


@router.post("/cost-per-use", response_model=CostResponse)
def cost(req: CostRequest) -> CostResponse:
    total = total_uses(req.uses_per_year, req.years)
    return CostResponse(
        cost_per_use=cost_per_use(req.price, req.uses_per_year, req.years),
        total_uses=total,
    )
