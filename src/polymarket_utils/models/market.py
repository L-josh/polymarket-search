from datetime import datetime
from typing import Optional
import json

from pydantic import BaseModel, Field, field_validator


class Market(BaseModel):
    """A market represents a specific outcome within an event."""

    id: str
    question: str
    slug: str
    end_date: Optional[datetime] = Field(None, alias="endDate")
    outcomes: list[str] = Field(default_factory=list)
    outcome_prices: list[float] = Field(default_factory=list, alias="outcomePrices")
    volume: float = Field(0, alias="volumeNum")
    liquidity: float = Field(0, alias="liquidityNum")
    active: bool = True
    closed: bool = False
    category: Optional[str] = None
    description: Optional[str] = None
    clob_token_ids: list[str] = Field(default_factory=list, alias="clobTokenIds")

    model_config = {"populate_by_name": True}

    @field_validator("clob_token_ids", mode="before")
    @classmethod
    def parse_clob_token_ids(cls, v: str | list[str] | None) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("outcomes", mode="before")
    @classmethod
    def parse_outcomes(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("outcome_prices", mode="before")
    @classmethod
    def parse_outcome_prices(cls, v: str | list | None) -> list[float]:
        if v is None:
            return []
        if isinstance(v, str):
            return [float(p) for p in json.loads(v)]
        return [float(p) for p in v]

    @property
    def is_active(self) -> bool:
        """Check if market is still active (not closed and not ended)."""
        if self.closed:
            return False
        if self.end_date and self.end_date < datetime.now(self.end_date.tzinfo):
            return False
        return True
