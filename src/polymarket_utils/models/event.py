from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .market import Market


class Event(BaseModel):
    """An event represents a question that may have multiple markets."""

    id: str
    title: str
    slug: str
    description: Optional[str] = None
    end_date: Optional[datetime] = Field(None, alias="endDate")
    start_date: Optional[datetime] = Field(None, alias="startDate")
    active: bool = True
    closed: bool = False
    volume: float = 0
    volume_24hr: float = Field(0, alias="volume24hr")
    liquidity: float = 0
    open_interest: float = Field(0, alias="openInterest")
    category: Optional[str] = None
    markets: list[Market] = Field(default_factory=list)

    model_config = {"populate_by_name": True}

    @property
    def is_active(self) -> bool:
        """Check if event is still active (not closed and not ended)."""
        if self.closed:
            return False
        if self.end_date and self.end_date < datetime.now(self.end_date.tzinfo):
            return False
        return True

    @property
    def market_count(self) -> int:
        """Number of markets in this event."""
        return len(self.markets)
