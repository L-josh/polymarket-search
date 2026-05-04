"""Shared fixtures for tests."""

import pytest


SAMPLE_MARKET_API = {
    "id": "2097944",
    "question": "Will the price of Bitcoin be above $80,000 on May 4?",
    "slug": "btc-above-80k-may-4",
    "conditionId": "0xabc123",
    "resolutionSource": "Binance",
    "endDate": "2026-05-04T16:00:00Z",
    "startDate": "2026-04-01T00:00:00Z",
    "description": "Resolves YES if BTC/USDT close price exceeds $80,000.",
    "outcomes": '["Yes", "No"]',
    "outcomePrices": '["0.58", "0.42"]',
    "volume": "1800000",
    "volumeNum": 1800000.0,
    "liquidityNum": 50000.0,
    "active": True,
    "closed": False,
    "category": "Crypto",
    "clobTokenIds": '["token_yes_001", "token_no_002"]',
    "spread": 0.02,
    "lastTradePrice": 0.58,
}

SAMPLE_EVENT_API = {
    "id": "424475",
    "title": "Bitcoin above ___ on May 4?",
    "slug": "bitcoin-above-may-4",
    "description": "Markets resolve YES if BTC/USDT close price exceeds the stated price.",
    "endDate": "2026-05-04T16:00:00Z",
    "startDate": "2026-04-01T00:00:00Z",
    "active": True,
    "closed": False,
    "volume": 1800000.0,
    "volume24hr": 25000.0,
    "liquidity": 50000.0,
    "openInterest": 75000.0,
    "category": "Crypto",
    "markets": [SAMPLE_MARKET_API],
}


@pytest.fixture
def sample_market_api():
    return dict(SAMPLE_MARKET_API)


@pytest.fixture
def sample_event_api():
    return {**SAMPLE_EVENT_API, "markets": [dict(SAMPLE_MARKET_API)]}
