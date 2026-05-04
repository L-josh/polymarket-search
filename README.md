# polymarket-search

[![CI](https://github.com/L-josh/polymarket-search/actions/workflows/ci.yml/badge.svg)](https://github.com/L-josh/polymarket-search/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/L-josh/polymarket-search/branch/main/graph/badge.svg)](https://codecov.io/gh/L-josh/polymarket-search)
[![GitHub tag](https://img.shields.io/github/v/tag/L-josh/polymarket-search?label=version)](https://github.com/L-josh/polymarket-search/tags)

`polymarket-search` is a CLI and Python library that makes it easy to find, explore, and analyse [Polymarket](https://polymarket.com) prediction markets via the [Gamma API](https://gamma-api.polymarket.com).

The Gamma API exposes all public market data but has no keyword search — to find events you have to page through everything. `polymarket-search` handles that: it fetches and caches the full event catalogue locally so you can search and filter instantly, and gives you clean access to live market prices and details.

## Installation

**CLI tool** — puts `pms` in your PATH, no repo needed:

```bash
# with uv (recommended)
uv tool install git+https://github.com/L-josh/polymarket-search

# with pipx
pipx install git+https://github.com/L-josh/polymarket-search
```

**Python library** — add to an existing project:

```bash
# with uv
uv add git+https://github.com/L-josh/polymarket-search

# with pip
pip install git+https://github.com/L-josh/polymarket-search
```

**Development** — clone and work on the source:

```bash
git clone https://github.com/L-josh/polymarket-search
cd polymarket-search
uv sync
```

## CLI (`pms`)

### Search events

```bash
# Search active events by keyword, sorted by volume
pms event search "bitcoin"

# Require multiple keywords (all must appear in title)
pms event search "bitcoin above"

# Include ended/closed events
pms event search "election" --all

# Bypass the local cache and fetch fresh data
pms event search "bitcoin" --fresh

# Minimum volume filter (USD)
pms event search "bitcoin" --min-volume 100000
```

### Event and market details

```bash
# Full event details with all its markets and current prices
pms event info <event_id>

# Details for a single market
pms market info <market_id>
```

### Cache management

Events are cached at `~/.cache/polymarket-search/` and auto-refresh after 1 hour. The cache strips nested market data to keep it lean (~40 MB for ~10k active events).

```bash
pms cache refresh          # Refresh active events
pms cache refresh --all    # Include closed events
```

### Configuration

```bash
pms config init   # Create a config file with defaults
pms config edit   # Open config in $EDITOR
pms config show   # Show active configuration
pms config path   # Show config file location
```

Config lives at `~/.config/polymarket-search/config.toml` and lets you set default volume filters, date filters, and cache TTL.

## Python library

```python
from polymarket_search.client import GammaClient

with GammaClient() as client:
    # Search events by keyword
    events = client.get_events(active_only=True)
    bitcoin_events = [e for e in events if "bitcoin" in e.title.lower()]

    # Full event details including all markets and current prices
    event = client.get_event("424475")
    for market in event.markets:
        prices = dict(zip(market.outcomes, market.outcome_prices))
        print(f"{market.question}: {prices}")

    # Single market lookup
    market = client.get_market("2097944")
    print(f"Yes: {market.outcome_prices[0]:.1%}")
```

See [examples/](examples/) for more, including how to find the nearest-expiry Bitcoin Up/Down markets.

## Agent usage (Claude Code skill)

`polymarket-search` is straightforward to use from AI agents. See [examples/skills/](examples/skills/) for a ready-to-use Claude Code skill that gives Claude the ability to search and analyse Polymarket markets on your behalf.

## Development

```bash
just install    # Install dependencies
just fmt        # Format code (black + ruff)
just types      # Type check (mypy)
just test       # Run tests
just check      # Run all checks
```

```bash
uv run pytest --cov=polymarket_search --cov-report=term-missing
```

## License

MIT
