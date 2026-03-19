"""Tests for get_crypto (live Finviz crypto performance table)."""

import pytest

from finviz.main_func import get_crypto


class TestGetCrypto:
    @pytest.mark.network
    def test_ethusd(self):
        row = get_crypto("ethusd")
        assert row["Ticker"] == "ETHUSD"
        assert float(row["Price"]) > 0
        assert "Perf Day" in row

    @pytest.mark.network
    def test_unknown_pair(self):
        with pytest.raises(KeyError, match="not found"):
            get_crypto("NOTAREALPAIR999")
