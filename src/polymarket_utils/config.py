"""Configuration management for polymarket-utils."""

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

import sys

# Use tomllib (3.11+) or fall back to tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[import-not-found,no-redef]

CONFIG_DIR = Path.home() / ".config" / "polymarket-utils"
CONFIG_FILE = CONFIG_DIR / "config.toml"


@dataclass
class FilterConfig:
    """Filter configuration for event searches."""

    active_only: bool = True
    min_volume: float = 10_000  # $10k default
    end_date_min: Optional[date] = field(default_factory=lambda: date(2026, 1, 1))


@dataclass
class CacheConfig:
    """Cache configuration."""

    ttl: int = 3600  # 1 hour in seconds
    dir: Path = field(
        default_factory=lambda: Path.home() / ".cache" / "polymarket-utils"
    )


@dataclass
class Config:
    """Main configuration."""

    filters: FilterConfig = field(default_factory=FilterConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)


def load_config() -> Config:
    """Load configuration from file, using defaults for missing values."""
    config = Config()

    if not CONFIG_FILE.exists():
        return config

    try:
        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return config

    # Parse filters section
    if "filters" in data:
        filters = data["filters"]
        if "active_only" in filters:
            config.filters.active_only = bool(filters["active_only"])
        if "min_volume" in filters:
            config.filters.min_volume = float(filters["min_volume"])
        if "end_date_min" in filters:
            val = filters["end_date_min"]
            if isinstance(val, date):
                config.filters.end_date_min = val
            elif isinstance(val, str):
                config.filters.end_date_min = date.fromisoformat(val)
            elif val is None:
                config.filters.end_date_min = None

    # Parse cache section
    if "cache" in data:
        cache_data = data["cache"]
        if "ttl" in cache_data:
            config.cache.ttl = int(cache_data["ttl"])
        if "dir" in cache_data:
            config.cache.dir = Path(cache_data["dir"]).expanduser()

    return config


# Default config template for users
DEFAULT_CONFIG_TEMPLATE = """\
# polymarket-utils configuration
# Location: ~/.config/polymarket-utils/config.toml

[filters]
# Only show active (non-closed) events by default
active_only = true

# Minimum volume filter (in USD)
min_volume = 10000

# Minimum end date filter (YYYY-MM-DD format, or remove line for no limit)
end_date_min = "2026-01-01"

[cache]
# Cache time-to-live in seconds (3600 = 1 hour)
ttl = 3600

# Cache directory (default: ~/.cache/polymarket-utils)
# dir = "~/.cache/polymarket-utils"
"""
