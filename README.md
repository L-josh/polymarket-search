# polymarket-utils

CLI utilities for searching and exploring Polymarket events and markets via the Gamma API.

## Installation

```bash
# Clone and install with uv
git clone <repo-url>
cd polymarket-utils
uv sync
```

## Usage

### Search Events

Search for events containing a keyword, sorted by volume:

```bash
# Search active events only (default)
polymarket event search "election"

# Include ended events
polymarket event search "election" --all

# Bypass cache and fetch fresh data
polymarket event search "bitcoin" --fresh
```

### Event Details

Get details about a specific event and its markets:

```bash
polymarket event info <event_id>
```

### Market Details

Get details about a specific market:

```bash
polymarket market info <market_id>
```

### Cache Management

The tool caches events locally to avoid repeated API calls. Cache is stored at `~/.cache/polymarket-utils/events.json` and auto-refreshes after 1 hour.

```bash
# Manually refresh the cache
polymarket cache refresh
```

## Development

```bash
just install    # Install dependencies
just fmt        # Format code
just types      # Type check
just test       # Run tests
just check      # Run all checks
```

## License

MIT
