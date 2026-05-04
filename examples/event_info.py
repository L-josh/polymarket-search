"""Fetch and display full event details including all markets."""

from polymarket_search.client import GammaClient


def show_event(event_id: str) -> None:
    with GammaClient() as client:
        event = client.get_event(event_id)

    print(f"Event:    {event.title}")
    print(f"ID:       {event.id}")
    print(f"Volume:   ${event.volume:,.0f}")
    print(f"Category: {event.category or 'N/A'}")
    print(f"End Date: {event.end_date.strftime('%Y-%m-%d') if event.end_date else 'N/A'}")
    print(f"Active:   {event.is_active}")

    if event.description:
        print(f"\nDescription:\n{event.description[:300]}")

    print(f"\nMarkets ({event.market_count}):")
    print("-" * 80)
    for market in event.markets:
        prices = "  |  ".join(
            f"{outcome}: {price:.0%}"
            for outcome, price in zip(market.outcomes, market.outcome_prices)
        )
        status = "open" if market.is_active else "closed"
        print(f"  [{market.id}] {market.question}")
        print(f"         {prices}  ({status}, vol ${market.volume:,.0f})")


if __name__ == "__main__":
    # Bitcoin above ___ on May 4?
    show_event("424475")
