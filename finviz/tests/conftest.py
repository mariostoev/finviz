"""
Pytest configuration and shared fixtures for finviz tests.

These tests make real HTTP requests to finviz.com.
Use appropriate rate limiting and be respectful of the service.
"""

import time
from typing import Generator

import pytest

# Test tickers - using well-known, stable stocks
TEST_TICKERS = {
    "large_cap": "AAPL",      # Apple - large cap, lots of data
    "mid_cap": "ETSY",        # Etsy - mid cap
    "volatile": "GME",        # GameStop - volatile, lots of news
    "dividend": "JNJ",        # Johnson & Johnson - dividend stock
    "tech": "NVDA",           # NVIDIA - tech sector
    "finance": "JPM",         # JPMorgan - financial sector
}

# Rate limiting between tests to avoid overwhelming finviz
REQUEST_DELAY = 0.5  # seconds between test functions


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "network: marks tests that make real network requests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests that are slow (> 5 seconds)"
    )


@pytest.fixture(scope="session")
def test_ticker() -> str:
    """Primary test ticker - Apple Inc."""
    return TEST_TICKERS["large_cap"]


@pytest.fixture(scope="session")
def test_tickers() -> dict:
    """Dictionary of test tickers for different scenarios."""
    return TEST_TICKERS


@pytest.fixture(autouse=True)
def rate_limit() -> Generator:
    """Apply rate limiting between tests to be respectful to finviz."""
    yield
    time.sleep(REQUEST_DELAY)


@pytest.fixture(scope="session")
def stock_data(test_ticker: str) -> dict:
    """
    Cached stock data for the session.
    Fetched once and reused across tests to minimize requests.
    """
    from finviz import get_stock
    return get_stock(test_ticker)


@pytest.fixture(scope="session")
def news_data(test_ticker: str) -> list:
    """Cached news data for the session."""
    from finviz import get_news
    return get_news(test_ticker)


@pytest.fixture(scope="session")
def insider_data(test_ticker: str) -> list:
    """Cached insider data for the session."""
    from finviz import get_insider
    return get_insider(test_ticker)


@pytest.fixture(scope="session")
def analyst_data(test_ticker: str) -> list:
    """Cached analyst price targets for the session."""
    from finviz import get_analyst_price_targets
    return get_analyst_price_targets(test_ticker)
