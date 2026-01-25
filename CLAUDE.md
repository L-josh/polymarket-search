# CLAUDE.md

This file provides context for AI assistants working on this codebase.

## Project Overview

`polymarket-utils` is a CLI tool for interacting with Polymarket's Gamma API. It provides utilities for searching events, viewing event/market details, with local caching to minimize API calls.

## Architecture

### Module Structure

```
src/polymarket_utils/
├── __init__.py
├── cli.py          # Click command groups and subcommands
├── client.py       # GammaClient class - API interaction + caching
├── models/         # Pydantic models (Event, Market)
└── utils/          # Helpers (table formatting, etc.)
```

### CLI Command Structure

```
polymarket event search <keyword>   # Search events by keyword, sorted by volume
polymarket event info <event_id>    # Show event details + all its markets
polymarket market info <market_id>  # Show details for a specific market
polymarket cache refresh            # Manually refresh the event cache
```

### Key Design Decisions

1. **Caching**: JSON file at `~/.cache/polymarket-utils/events.json`
   - TTL-based (default 1 hour)
   - `--fresh` flag bypasses cache
   - Manual refresh via `polymarket cache refresh`

2. **Event Search**: No native API search, so we:
   - Fetch all events with pagination
   - Cache locally
   - Filter by keyword in Python
   - Default to active events only (`--all` flag for ended events)
   - Sort by lifetime volume descending

3. **Output**: Simple table format for terminal display

4. **Extensibility**: Click command groups allow easy addition of new subcommands

## Gamma API Reference

**Base URL**: `https://gamma-api.polymarket.com`

### Key Endpoints

- `GET /events` - List events (supports `limit`, `offset` for pagination)
- `GET /events/{id}` - Get single event by ID
- `GET /markets/{id}` - Get single market by ID

### Event Object (key fields)

```python
{
    "id": "2890",                    # Unique identifier
    "title": "...",                  # Event title (searchable)
    "slug": "...",                   # URL-friendly identifier
    "description": "...",
    "endDate": "2021-12-04T00:00:00Z",
    "active": true,
    "closed": true,                  # Whether trading is closed
    "volume": 1335.05,               # Lifetime volume (USD)
    "volume24hr": 0,
    "liquidity": 0,
    "openInterest": 0,
    "category": "Sports",
    "markets": [...]                 # Nested market objects
}
```

### Market Object (key fields)

```python
{
    "id": "239826",
    "question": "...",               # Market question
    "slug": "...",
    "endDate": "...",
    "outcomes": "[\"Yes\", \"No\"]", # JSON string
    "outcomePrices": "[\"0.5\", \"0.5\"]",  # JSON string
    "volume": "1335.045385",         # String
    "volumeNum": 1335.05,            # Number
    "active": true,
    "closed": true
}
```

## Development

### Commands (via justfile)

```bash
just install    # uv sync
just fmt        # Black + Ruff formatting
just types      # mypy type checking
just test       # pytest
just check      # Run all checks
just run        # Run the CLI
```

### Dependencies

- **click**: CLI framework
- **httpx**: HTTP client (async-capable)
- **pydantic**: Data validation and models

### Testing

Tests go in `tests/`. Use pytest fixtures for mocking API responses.

## Implementation Notes

- Gamma API is public, no auth required
- Pagination: use `limit` + `offset` parameters
- Events include nested `markets` array
- Volume fields are numbers on events, strings on markets (use `volumeNum` on markets)
- `closed=true` means trading ended, `active` is separate from closed
- Filter active events by checking `endDate > now` and `closed=false`
