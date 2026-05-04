"""Gamma API client for Polymarket."""

import asyncio
import json
import time
from pathlib import Path
from typing import Callable, Optional

import httpx
from platformdirs import user_cache_dir

from polymarket_utils.models import Event, Market

BASE_URL = "https://gamma-api.polymarket.com"
DEFAULT_CACHE_DIR = Path(user_cache_dir("polymarket-utils"))
DEFAULT_CACHE_TTL = 3600  # 1 hour in seconds
_FETCH_PAGE_SIZE = 500
_FETCH_CONCURRENCY = 50


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
        slim = []
        for e in events:
            entry = {k: v for k, v in e.items() if k != "markets"}
            entry["marketCount"] = len(e.get("markets") or [])
            slim.append(entry)
        data = {"cached_at": time.time(), "events": slim}
        with open(self._cache_file(active_only), "w") as f:
            json.dump(data, f)

    async def _fetch_all_events_async(
        self,
        active_only: bool = True,
        on_progress: Optional[Callable[[int], None]] = None,
    ) -> list[dict]:
        params: dict = {"limit": _FETCH_PAGE_SIZE}
        if active_only:
            params["closed"] = "false"

        all_events: list[dict] = []
        offset = 0

        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            while True:
                offsets = [offset + i * _FETCH_PAGE_SIZE for i in range(_FETCH_CONCURRENCY)]
                responses = await asyncio.gather(*[
                    client.get("/events", params={**params, "offset": o})
                    for o in offsets
                ])

                done = False
                for resp in responses:
                    resp.raise_for_status()
                    batch = resp.json()
                    all_events.extend(batch)
                    if on_progress:
                        on_progress(len(all_events))
                    if len(batch) < _FETCH_PAGE_SIZE:
                        done = True
                        break

                if done:
                    break
                offset += _FETCH_CONCURRENCY * _FETCH_PAGE_SIZE

        return all_events

    def _fetch_all_events(
        self,
        active_only: bool = True,
        on_progress: Optional[Callable[[int], None]] = None,
    ) -> list[dict]:
        return asyncio.run(self._fetch_all_events_async(active_only, on_progress))

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
