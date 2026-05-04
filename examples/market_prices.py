"""Find the nearest-expiry Bitcoin Up/Down 15-minute markets and show current prices.

"Bitcoin Up or Down" markets resolve based on whether BTC moves up or down over a
time window encoded in the title (e.g. "12:15AM-12:30AM ET" = 15 minutes).
This example finds the soonest-expiring open 15-minute markets.
"""

import re
from datetime import datetime, timedelta, timezone

from polymarket_search.client import GammaClient
from polymarket_search.models import Event, Market


def _window_minutes(title: str) -> int | None:
    """Parse the time window duration in minutes from an event title.

    Handles titles like 'Bitcoin Up or Down - May 4, 12:15AM-12:30AM ET'.
    Returns None if no time range is found.
    """
    match = re.search(r"(\d+:\d+[AP]M)-(\d+:\d+[AP]M)", title)
    if not match:
        return None
    start = datetime.strptime(match.group(1), "%I:%M%p")
    end = datetime.strptime(match.group(2), "%I:%M%p")
    delta = (end - start).total_seconds() / 60
    # Handle midnight rollover (e.g. 11:55PM-12:00AM)
    if delta < 0:
        delta += 24 * 60
    return int(delta)


def get_nearest_btc_updown_markets(window_minutes: int = 15, n: int = 5) -> list[tuple[Event, Market]]:
    """Return the n nearest-expiry active Bitcoin Up/Down markets for a given window size."""
    now = datetime.now(timezone.utc)

    with GammaClient() as client:
        events = client.get_events(active_only=True)

        candidates = [
            e for e in events
            if "bitcoin up or down" in e.title.lower()
            and e.end_date is not None
            and e.end_date > now
            and _window_minutes(e.title) == window_minutes
        ]
        candidates.sort(key=lambda e: e.end_date)  # type: ignore[arg-type]

        results = []
        for event in candidates:
            if len(results) >= n:
                break
            full = client.get_event(event.id)
            for market in full.markets:
                if market.is_active and market.outcomes:
                    results.append((event, market))

    return results


if __name__ == "__main__":
    markets = get_nearest_btc_updown_markets(window_minutes=15, n=5)

    if not markets:
        print("No active 15-minute Bitcoin Up/Down markets found.")
    else:
        print(f"{'Expires (UTC)':<22} {'Window':>8} {'Up':>6} {'Down':>6}  Market")
        print("-" * 85)
        for event, market in markets:
            expiry = event.end_date.strftime("%Y-%m-%d %H:%M") if event.end_date else "N/A"
            window = _window_minutes(event.title)
            prices = dict(zip(market.outcomes, market.outcome_prices))
            up = prices.get("Up", 0)
            down = prices.get("Down", 0)
            print(f"{expiry:<22} {f'{window}m':>8} {up:>5.1%} {down:>6.1%}  {event.title}")
