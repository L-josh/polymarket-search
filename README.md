# polymarket-search

[![CI](https://github.com/L-josh/polymarket-search/actions/workflows/ci.yml/badge.svg)](https://github.com/L-josh/polymarket-search/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/L-josh/polymarket-search/branch/main/graph/badge.svg)](https://codecov.io/gh/L-josh/polymarket-search)

CLI and Python library for searching and exploring [Polymarket](https://polymarket.com) events and markets via the Gamma API.

## Installation

```bash
git clone https://github.com/L-josh/polymarket-search
cd polymarket-search
uv sync
```

## CLI Usage

### Search Events

```bash
# Search active events by keyword, sorted by volume
pms event search "bitcoin"

# Multiple keywords (both must appear in title)
pms event search "bitcoin above"

# Include ended events
pms event search "election" --all

# Bypass cache and fetch fresh data
pms event search "bitcoin" --fresh

# Filter by minimum volume
pms event search "bitcoin" --min-volume 100000
```

### Event Details

```bash
pms event info <event_id>
```

### Market Details

```bash
pms market info <market_id>
```

### Cache Management

Events are cached locally at `~/.cache/polymarket-search/` and auto-refresh after 1 hour.

```bash
pms cache refresh          # Refresh active events
pms cache refresh --all    # Include closed events
```

### Configuration

```bash
pms config show      # Show current config
pms config path      # Show config file location
pms config init      # Create a default config file
pms config edit      # Open config in $EDITOR
```

## Python Library Usage

```python
from polymarket_search.client import GammaClient

with GammaClient() as client:
    # Search events by keyword
    events = client.get_events(active_only=True)
    bitcoin_events = [e for e in events if "bitcoin" in e.title.lower()]

    # Get full event details (with markets)
    event = client.get_event("424475")
    for market in event.markets:
        prices = dict(zip(market.outcomes, market.outcome_prices))
        print(f"{market.question}: {prices}")

    # Get a single market
    market = client.get_market("2097944")
    print(f"Yes: {market.outcome_prices[0]:.1%}")
```

See [examples/](examples/) for more.

## Development

```bash
just install    # Install dependencies
just fmt        # Format code (black + ruff)
just types      # Type check (mypy)
just test       # Run tests
just check      # Run all checks
```

Run tests with coverage:

```bash
uv run pytest --cov=polymarket_search --cov-report=term-missing
```

## License

MIT
