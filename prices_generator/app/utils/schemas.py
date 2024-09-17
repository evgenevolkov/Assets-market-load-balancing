from pydantic import BaseModel, Field
from typing import List
from uuid import UUID, uuid4

class Asset(BaseModel):
    name: str
    market: str


class PriceBase(BaseModel):
    price: float = Field(gt=0)
    spread: float = Field(gt=0)


class AssetPrice(PriceBase, Asset):
    pass


class PriceQuoteOut(AssetPrice):
    price_quote_id: UUID = Field(default_factory=uuid4)


class PriceConfig(BaseModel):
    assets: List[str]
    markets: List[str]
    price_min: float = Field(gt=0)
    price_max: float = Field(gt=0)
    spread_min: float = Field(ge=0)
    spread_max: float = Field(gt=0)
    price_change_max: float = Field(gt=0)