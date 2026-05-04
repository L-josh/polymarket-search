"""Tests for config loading."""

import sys
from datetime import date

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[import-not-found,no-redef]
from pathlib import Path
from unittest.mock import patch

import pytest

from polymarket_search.config import load_config


def write_config(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_defaults_when_no_file(tmp_path):
    config_file = tmp_path / "config.toml"
    with patch("polymarket_search.config.CONFIG_FILE", config_file):
        config = load_config()
    assert config.filters.active_only is True
    assert config.filters.min_volume == 10_000
    assert config.cache.ttl == 3600


def test_loads_filter_settings(tmp_path):
    config_file = tmp_path / "config.toml"
    write_config(config_file, """
[filters]
active_only = false
min_volume = 50000
end_date_min = "2027-06-01"
""")
    with patch("polymarket_search.config.CONFIG_FILE", config_file):
        config = load_config()
    assert config.filters.active_only is False
    assert config.filters.min_volume == 50_000
    assert config.filters.end_date_min == date(2027, 6, 1)


def test_loads_cache_settings(tmp_path):
    config_file = tmp_path / "config.toml"
    write_config(config_file, f"""
[cache]
ttl = 7200
dir = "{tmp_path}/mycache"
""")
    with patch("polymarket_search.config.CONFIG_FILE", config_file):
        config = load_config()
    assert config.cache.ttl == 7200
    assert config.cache.dir == tmp_path / "mycache"


def test_end_date_min_none(tmp_path):
    config_file = tmp_path / "config.toml"
    # TOML doesn't have null, but our parser handles date objects from tomllib
    # Test via date object path by writing a TOML date literal
    write_config(config_file, """
[filters]
end_date_min = 2026-03-15
""")
    with patch("polymarket_search.config.CONFIG_FILE", config_file):
        config = load_config()
    assert config.filters.end_date_min == date(2026, 3, 15)


def test_returns_defaults_on_corrupted_file(tmp_path):
    config_file = tmp_path / "config.toml"
    write_config(config_file, "not valid toml ][[[")
    with patch("polymarket_search.config.CONFIG_FILE", config_file):
        config = load_config()
    assert config.cache.ttl == 3600


def test_partial_config_uses_defaults_for_missing(tmp_path):
    config_file = tmp_path / "config.toml"
    write_config(config_file, """
[filters]
min_volume = 999
""")
    with patch("polymarket_search.config.CONFIG_FILE", config_file):
        config = load_config()
    assert config.filters.min_volume == 999
    assert config.filters.active_only is True  # default preserved
    assert config.cache.ttl == 3600  # default preserved
