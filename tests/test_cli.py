"""Tests for CLI commands using Click's test runner."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from polymarket_search.cli import main
from polymarket_search.models import Event, Market


@pytest.fixture
def runner():
    return CliRunner()


def _mock_client(events=None, event=None, market=None, refresh_count=0):
    """Build a mock GammaClient context manager."""
    client = MagicMock()
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)
    if events is not None:
        client.get_events.return_value = events
    if event is not None:
        client.get_event.return_value = event
    if market is not None:
        client.get_market.return_value = market
    client.refresh_cache.return_value = refresh_count
    return client


@pytest.fixture
def sample_event(sample_event_api):
    return Event.model_validate(sample_event_api)


@pytest.fixture
def sample_market(sample_market_api):
    return Market.model_validate(sample_market_api)


class TestEventSearch:
    def test_finds_matching_event(self, runner, sample_event):
        with patch("polymarket_search.cli._get_client", return_value=_mock_client(events=[sample_event])):
            result = runner.invoke(main, ["event", "search", "bitcoin"])
        assert result.exit_code == 0
        assert "424475" in result.output
        assert "Bitcoin" in result.output

    def test_no_results_message(self, runner, sample_event):
        with patch("polymarket_search.cli._get_client", return_value=_mock_client(events=[sample_event])):
            result = runner.invoke(main, ["event", "search", "zzznomatch"])
        assert result.exit_code == 0
        assert "No events found" in result.output

    def test_keyword_filter_is_case_insensitive(self, runner, sample_event):
        with patch("polymarket_search.cli._get_client", return_value=_mock_client(events=[sample_event])):
            result = runner.invoke(main, ["event", "search", "BITCOIN"])
        assert result.exit_code == 0
        assert "424475" in result.output

    def test_min_volume_filter(self, runner, sample_event):
        with patch("polymarket_search.cli._get_client", return_value=_mock_client(events=[sample_event])):
            result = runner.invoke(main, ["event", "search", "bitcoin", "--min-volume", "999999999"])
        assert result.exit_code == 0
        assert "No events found" in result.output

    def test_fresh_flag_passes_force_refresh(self, runner, sample_event):
        mock_client = _mock_client(events=[sample_event])
        with patch("polymarket_search.cli._get_client", return_value=mock_client):
            runner.invoke(main, ["event", "search", "bitcoin", "--fresh"])
        mock_client.__enter__.return_value.get_events.assert_called_once_with(
            active_only=True, force_refresh=True, on_progress=mock_client.__enter__.return_value.get_events.call_args[1]["on_progress"]
        )


class TestEventInfo:
    def test_shows_event_details(self, runner, sample_event):
        with patch("polymarket_search.cli._get_client", return_value=_mock_client(event=sample_event)):
            result = runner.invoke(main, ["event", "info", "424475"])
        assert result.exit_code == 0
        assert "Bitcoin above" in result.output
        assert "424475" in result.output

    def test_shows_markets(self, runner, sample_event):
        with patch("polymarket_search.cli._get_client", return_value=_mock_client(event=sample_event)):
            result = runner.invoke(main, ["event", "info", "424475"])
        assert "2097944" in result.output
        assert "Yes" in result.output

    def test_error_on_missing_event(self, runner):
        mock_client = _mock_client()
        mock_client.__enter__.return_value.get_event.side_effect = Exception("not found")
        with patch("polymarket_search.cli._get_client", return_value=mock_client):
            result = runner.invoke(main, ["event", "info", "bad_id"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "bad_id" in result.output


class TestMarketInfo:
    def test_shows_market_details(self, runner, sample_market):
        with patch("polymarket_search.cli._get_client", return_value=_mock_client(market=sample_market)):
            result = runner.invoke(main, ["market", "info", "2097944"])
        assert result.exit_code == 0
        assert "2097944" in result.output
        assert "Bitcoin" in result.output

    def test_shows_outcome_prices(self, runner, sample_market):
        with patch("polymarket_search.cli._get_client", return_value=_mock_client(market=sample_market)):
            result = runner.invoke(main, ["market", "info", "2097944"])
        assert "Yes" in result.output
        assert "No" in result.output


class TestCacheRefresh:
    def test_refresh_reports_count(self, runner):
        with patch("polymarket_search.cli._get_client", return_value=_mock_client(refresh_count=9878)):
            result = runner.invoke(main, ["cache", "refresh"])
        assert result.exit_code == 0
        assert "9878" in result.output

    def test_refresh_all_flag(self, runner):
        mock_client = _mock_client(refresh_count=25000)
        with patch("polymarket_search.cli._get_client", return_value=mock_client):
            result = runner.invoke(main, ["cache", "refresh", "--all"])
        assert result.exit_code == 0
        mock_client.__enter__.return_value.refresh_cache.assert_called_once_with(
            active_only=False, on_progress=mock_client.__enter__.return_value.refresh_cache.call_args[1]["on_progress"]
        )


class TestConfigShow:
    def test_shows_config(self, runner):
        result = runner.invoke(main, ["config", "show"])
        assert result.exit_code == 0
        assert "active_only" in result.output
        assert "ttl" in result.output
