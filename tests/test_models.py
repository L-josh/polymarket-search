"""Tests for Event and Market models."""

from datetime import datetime, timezone

import pytest

from polymarket_search.models import Event, Market


class TestMarket:
    def test_parses_json_string_fields(self, sample_market_api):
        m = Market.model_validate(sample_market_api)
        assert m.outcomes == ["Yes", "No"]
        assert m.outcome_prices == [0.58, 0.42]
        assert m.clob_token_ids == ["token_yes_001", "token_no_002"]

    def test_parses_native_list_fields(self, sample_market_api):
        sample_market_api["outcomes"] = ["Yes", "No"]
        sample_market_api["outcomePrices"] = ["0.58", "0.42"]
        sample_market_api["clobTokenIds"] = ["token_yes_001", "token_no_002"]
        m = Market.model_validate(sample_market_api)
        assert m.outcomes == ["Yes", "No"]
        assert m.outcome_prices == [0.58, 0.42]

    def test_outcome_prices_coerced_to_float(self, sample_market_api):
        sample_market_api["outcomePrices"] = '["0.9999", "0.0001"]'
        m = Market.model_validate(sample_market_api)
        assert isinstance(m.outcome_prices[0], float)
        assert abs(m.outcome_prices[0] - 0.9999) < 1e-9

    def test_null_clob_token_ids(self, sample_market_api):
        sample_market_api["clobTokenIds"] = None
        m = Market.model_validate(sample_market_api)
        assert m.clob_token_ids == []

    def test_is_active_open_market(self, sample_market_api):
        m = Market.model_validate(sample_market_api)
        assert m.is_active is True

    def test_is_active_false_when_closed(self, sample_market_api):
        sample_market_api["closed"] = True
        m = Market.model_validate(sample_market_api)
        assert m.is_active is False

    def test_is_active_false_when_expired(self, sample_market_api):
        sample_market_api["endDate"] = "2020-01-01T00:00:00Z"
        m = Market.model_validate(sample_market_api)
        assert m.is_active is False

    def test_volume_mapped_from_volumenum(self, sample_market_api):
        m = Market.model_validate(sample_market_api)
        assert m.volume == 1800000.0

    def test_outcome_prices_as_plain_float_list(self, sample_market_api):
        sample_market_api["outcomePrices"] = [0.7, 0.3]
        m = Market.model_validate(sample_market_api)
        assert m.outcome_prices == [0.7, 0.3]

    def test_populate_by_name(self):
        m = Market.model_validate({
            "id": "1",
            "question": "Q?",
            "slug": "q",
            "outcome_prices": [0.5, 0.5],
            "outcomes": ["Yes", "No"],
        })
        assert m.outcome_prices == [0.5, 0.5]


class TestEvent:
    def test_market_count_from_markets_list(self, sample_event_api):
        e = Event.model_validate(sample_event_api)
        assert e.market_count == 1

    def test_market_count_from_cached_field(self):
        """Events loaded from cache have no markets array, only marketCount."""
        slim = {
            "id": "1",
            "title": "T",
            "slug": "t",
            "marketCount": 11,
        }
        e = Event.model_validate(slim)
        assert e.markets == []
        assert e.market_count == 11

    def test_market_count_zero_when_no_data(self):
        e = Event.model_validate({"id": "1", "title": "T", "slug": "t"})
        assert e.market_count == 0

    def test_is_active_open_event(self, sample_event_api):
        e = Event.model_validate(sample_event_api)
        assert e.is_active is True

    def test_is_active_false_when_closed(self, sample_event_api):
        sample_event_api["closed"] = True
        e = Event.model_validate(sample_event_api)
        assert e.is_active is False

    def test_is_active_false_when_expired(self, sample_event_api):
        sample_event_api["endDate"] = "2020-01-01T00:00:00Z"
        e = Event.model_validate(sample_event_api)
        assert e.is_active is False

    def test_nested_markets_parsed(self, sample_event_api):
        e = Event.model_validate(sample_event_api)
        assert len(e.markets) == 1
        assert e.markets[0].id == "2097944"
        assert e.markets[0].outcomes == ["Yes", "No"]

    def test_optional_fields_default(self):
        e = Event.model_validate({"id": "1", "title": "T", "slug": "t"})
        assert e.description is None
        assert e.category is None
        assert e.volume == 0
        assert e.closed is False
