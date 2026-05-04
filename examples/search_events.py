"""Search for events by keyword and print a summary table."""

from polymarket_search.client import GammaClient
from polymarket_search.models import Event


def search(keyword: str, min_volume: float = 0) -> list[Event]:
    with GammaClient() as client:
        events = client.get_events(active_only=True)

    matches = [e for e in events if keyword.lower() in e.title.lower()]
    if min_volume:
        matches = [e for e in matches if e.volume >= min_volume]
    matches.sort(key=lambda e: e.volume, reverse=True)
    return matches


def search_multi(keywords: list[str], min_volume: float = 0) -> list[Event]:
    """Return events that contain ALL of the given keywords (case-insensitive)."""
    with GammaClient() as client:
        events = client.get_events(active_only=True)

    def matches_all(event: Event) -> bool:
        title = event.title.lower()
        return all(kw.lower() in title for kw in keywords)

    matches = [e for e in events if matches_all(e)]
    if min_volume:
        matches = [e for e in matches if e.volume >= min_volume]
    matches.sort(key=lambda e: e.volume, reverse=True)
    return matches


if __name__ == "__main__":
    print("=== Single keyword: 'bitcoin' ===")
    for event in search("bitcoin", min_volume=100_000)[:5]:
        print(f"  [{event.id}] {event.title}  (${event.volume:,.0f}, {event.market_count} markets)")

    print()
    print("=== Multi-keyword: ['bitcoin', 'above'] ===")
    for event in search_multi(["bitcoin", "above"])[:5]:
        print(f"  [{event.id}] {event.title}  (${event.volume:,.0f}, {event.market_count} markets)")
