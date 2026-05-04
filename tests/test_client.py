"""Tests for GammaClient."""

import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from polymarket_search.client import GammaClient


@pytest.fixture
def client(tmp_path):
    return GammaClient(cache_dir=tmp_path, cache_ttl=3600)


def _make_async_http(events: list[dict]) -> MagicMock:
    """Build a patched httpx.AsyncClient that returns `events` for any GET."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = events

    mock = AsyncMock()
    mock.__aenter__.return_value = mock
    mock.get = AsyncMock(return_value=resp)
    return mock


class TestCacheBehavior:
    def test_fetches_from_api_on_cache_miss(self, client, sample_event_api):
        mock_http = _make_async_http([sample_event_api])
        with patch("polymarket_search.client.httpx.AsyncClient", return_value=mock_http):
            events = client.get_events()
        assert len(events) == 1
        assert events[0].id == "424475"

    def test_uses_cache_on_second_call(self, client, sample_event_api):
        mock_http = _make_async_http([sample_event_api])
        with patch("polymarket_search.client.httpx.AsyncClient", return_value=mock_http):
            client.get_events()
            client.get_events()
        # Both calls share one AsyncClient instantiation per _fetch_all_events call;
        # second get_events() should not call AsyncClient at all.
        assert mock_http.get.call_count == 50  # one wave of 50 concurrent requests

    def test_strips_markets_from_cache(self, client, sample_event_api):
        mock_http = _make_async_http([sample_event_api])
        with patch("polymarket_search.client.httpx.AsyncClient", return_value=mock_http):
            client.get_events()

        cache_file = client._cache_file(active_only=True)
        data = json.loads(cache_file.read_text())
        cached_event = data["events"][0]

        assert "markets" not in cached_event
        assert cached_event["marketCount"] == 1

    def test_preserves_market_count_through_cache(self, client, sample_event_api):
        mock_http = _make_async_http([sample_event_api])
        with patch("polymarket_search.client.httpx.AsyncClient", return_value=mock_http):
            client.get_events()  # populate cache

        # Read back from cache
        with patch("polymarket_search.client.httpx.AsyncClient") as mock_cls:
            events = client.get_events()

        mock_cls.assert_not_called()
        assert events[0].market_count == 1

    def test_force_refresh_bypasses_cache(self, client, sample_event_api):
        mock_http = _make_async_http([sample_event_api])
        with patch("polymarket_search.client.httpx.AsyncClient", return_value=mock_http):
            client.get_events()
            client.get_events(force_refresh=True)
        # Two fetches → two sets of 50 concurrent requests
        assert mock_http.get.call_count == 100

    def test_stale_cache_triggers_refetch(self, client, sample_event_api, tmp_path):
        # Write a cache file with an old timestamp
        stale = {"cached_at": time.time() - 7200, "events": []}
        cache_file = client._cache_file(active_only=True)
        cache_file.write_text(json.dumps(stale))

        mock_http = _make_async_http([sample_event_api])
        with patch("polymarket_search.client.httpx.AsyncClient", return_value=mock_http):
            events = client.get_events()

        assert len(events) == 1

    def test_corrupted_cache_triggers_refetch(self, client, sample_event_api):
        cache_file = client._cache_file(active_only=True)
        client._ensure_cache_dir()
        cache_file.write_text("not valid json{{{")

        mock_http = _make_async_http([sample_event_api])
        with patch("polymarket_search.client.httpx.AsyncClient", return_value=mock_http):
            events = client.get_events()

        assert len(events) == 1


class TestGetEvent:
    def test_returns_event_with_markets(self, client, sample_event_api):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = sample_event_api

        with patch.object(client._http, "get", return_value=mock_resp) as mock_get:
            event = client.get_event("424475")

        mock_get.assert_called_once_with("/events/424475")
        assert event.id == "424475"
        assert len(event.markets) == 1
        assert event.markets[0].outcomes == ["Yes", "No"]

    def test_raises_on_http_error(self, client):
        import httpx

        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=MagicMock()
        )
        with patch.object(client._http, "get", return_value=mock_resp):
            with pytest.raises(httpx.HTTPStatusError):
                client.get_event("nonexistent")


class TestGetMarket:
    def test_returns_market(self, client, sample_market_api):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = sample_market_api

        with patch.object(client._http, "get", return_value=mock_resp) as mock_get:
            market = client.get_market("2097944")

        mock_get.assert_called_once_with("/markets/2097944")
        assert market.id == "2097944"
        assert market.outcome_prices == [0.58, 0.42]

    def test_yes_no_prices_sum_to_one(self, client, sample_market_api):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = sample_market_api

        with patch.object(client._http, "get", return_value=mock_resp):
            market = client.get_market("2097944")

        total = sum(market.outcome_prices)
        assert abs(total - 1.0) < 0.01


class TestRefreshCache:
    def test_returns_event_count(self, client, sample_event_api):
        mock_http = _make_async_http([sample_event_api, sample_event_api])
        with patch("polymarket_search.client.httpx.AsyncClient", return_value=mock_http):
            count = client.refresh_cache()
        assert count == 2

    def test_overwrites_existing_cache(self, client, sample_event_api, tmp_path):
        old = {"cached_at": time.time(), "events": [{"id": "old"}]}
        cache_file = client._cache_file(active_only=True)
        client._ensure_cache_dir()
        cache_file.write_text(json.dumps(old))

        mock_http = _make_async_http([sample_event_api])
        with patch("polymarket_search.client.httpx.AsyncClient", return_value=mock_http):
            client.refresh_cache()

        data = json.loads(cache_file.read_text())
        assert data["events"][0]["id"] == "424475"


class TestOnProgress:
    def test_progress_callback_called(self, client, sample_event_api):
        mock_http = _make_async_http([sample_event_api])
        progress_calls = []
        with patch("polymarket_search.client.httpx.AsyncClient", return_value=mock_http):
            client.get_events(on_progress=progress_calls.append)
        assert len(progress_calls) > 0
        assert progress_calls[-1] == 1


class TestMultiWaveFetch:
    def test_fires_second_wave_when_first_is_full(self, client, sample_event_api):
        from polymarket_search.client import _FETCH_PAGE_SIZE, _FETCH_CONCURRENCY

        full_page = [sample_event_api] * _FETCH_PAGE_SIZE
        empty_page = []

        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            # First wave: all full pages; second wave: all empty
            resp.json.return_value = full_page if call_count <= _FETCH_CONCURRENCY else empty_page
            return resp

        mock_http = AsyncMock()
        mock_http.__aenter__.return_value = mock_http
        mock_http.get = mock_get

        with patch("polymarket_search.client.httpx.AsyncClient", return_value=mock_http):
            events = client.get_events()

        assert len(events) == _FETCH_PAGE_SIZE * _FETCH_CONCURRENCY
        assert call_count > _FETCH_CONCURRENCY


class TestContextManager:
    def test_enter_returns_self(self, client):
        assert client.__enter__() is client

    def test_exit_closes_http(self, client):
        with patch.object(client._http, "close") as mock_close:
            client.__exit__(None, None, None)
        mock_close.assert_called_once()

    def test_used_as_context_manager(self, tmp_path):
        from polymarket_search.client import GammaClient
        with GammaClient(cache_dir=tmp_path) as c:
            assert isinstance(c, GammaClient)
