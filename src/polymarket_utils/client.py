"""Gamma API client for Polymarket."""

import json
import time
from pathlib import Path
from typing import Callable, Optional

import httpx

from polymarket_utils.models import Event, Market

BASE_URL = "https://gamma-api.polymarket.com"
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "polymarket-utils"
DEFAULT_CACHE_TTL = 3600  # 1 hour in seconds


class GammaClient:
    """Client for interacting with Polymarket's Gamma API."""

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        cache_ttl: int = DEFAULT_CACHE_TTL,
    ):
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.cache_ttl = cache_ttl
        self._http = httpx.Client(base_url=BASE_URL, timeout=30.0)

    def _cache_file(self, active_only: bool = True) -> Path:
        suffix = "active" if active_only else "all"
        return self.cache_dir / f"events_{suffix}.json"

    def _ensure_cache_dir(self) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _is_cache_valid(self, active_only: bool = True) -> bool:
        """Check if cache exists and is not stale."""
        cache_file = self._cache_file(active_only)
        if not cache_file.exists():
            return False
        try:
            with open(cache_file) as f:
                data = json.load(f)
            cached_at = data.get("cached_at", 0)
            return (time.time() - cached_at) < self.cache_ttl
        except (json.JSONDecodeError, OSError):
            return False

    def _read_cache(self, active_only: bool = True) -> list[dict]:
        """Read events from cache file."""
        with open(self._cache_file(active_only)) as f:
            data = json.load(f)
        return data.get("events", [])

    def _write_cache(self, events: list[dict], active_only: bool = True) -> None:
        """Write events to cache file."""
        self._ensure_cache_dir()
        data = {
            "cached_at": time.time(),
            "events": events,
        }
        with open(self._cache_file(active_only), "w") as f:
            json.dump(data, f)

    def _fetch_all_events(
        self,
        active_only: bool = True,
        on_progress: Optional[Callable[[int], None]] = None,
    ) -> list[dict]:
        """Fetch all events from API with pagination.

        Args:
            active_only: If True, only fetch non-closed events.
            on_progress: Optional callback called with event count after each batch.
        """
        events = []
        limit = 500
        offset = 0

        params: dict = {"limit": limit}
        if active_only:
            params["closed"] = "false"

        while True:
            params["offset"] = offset
            response = self._http.get("/events", params=params)
            response.raise_for_status()
            batch = response.json()

            if not batch:
                break

            events.extend(batch)
            if on_progress:
                on_progress(len(events))
            offset += limit

            if len(batch) < limit:
                break

        return events

    def get_events(
        self,
        active_only: bool = True,
        force_refresh: bool = False,
        on_progress: Optional[Callable[[int], None]] = None,
    ) -> list[Event]:
        """Get events, using cache if valid.

        Args:
            active_only: If True, only return non-closed events (faster).
            force_refresh: Bypass cache and fetch from API.
            on_progress: Optional callback called with event count during fetch.

        Returns:
            List of Event objects.
        """
        if not force_refresh and self._is_cache_valid(active_only):
            raw_events = self._read_cache(active_only)
        else:
            raw_events = self._fetch_all_events(
                active_only=active_only, on_progress=on_progress
            )
            self._write_cache(raw_events, active_only)

        return [Event.model_validate(e) for e in raw_events]

    def refresh_cache(
        self,
        active_only: bool = True,
        on_progress: Optional[Callable[[int], None]] = None,
    ) -> int:
        """Force refresh the cache.

        Args:
            active_only: If True, only cache non-closed events.
            on_progress: Optional callback called with event count during fetch.

        Returns:
            Number of events cached.
        """
        raw_events = self._fetch_all_events(
            active_only=active_only, on_progress=on_progress
        )
        self._write_cache(raw_events, active_only)
        return len(raw_events)

    def get_event(self, event_id: str) -> Event:
        """Get a single event by ID.

        Args:
            event_id: The event ID.

        Returns:
            Event object.

        Raises:
            httpx.HTTPStatusError: If event not found.
        """
        response = self._http.get(f"/events/{event_id}")
        response.raise_for_status()
        return Event.model_validate(response.json())

    def get_market(self, market_id: str) -> Market:
        """Get a single market by ID.

        Args:
            market_id: The market ID.

        Returns:
            Market object.

        Raises:
            httpx.HTTPStatusError: If market not found.
        """
        response = self._http.get(f"/markets/{market_id}")
        response.raise_for_status()
        return Market.model_validate(response.json())

    def close(self) -> None:
        """Close the HTTP client."""
        self._http.close()

    def __enter__(self) -> "GammaClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()
