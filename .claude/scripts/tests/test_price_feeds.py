"""Tests for price_feeds — all HTTP calls mocked."""
from unittest.mock import patch, MagicMock
import pytest

from price_feeds import (
    binance_futures_price,
    okx_swap_price,
    twelvedata_price,
    price_for,
    PriceFeedError,
)


@patch("price_feeds.requests.get")
def test_binance_futures_price(mock_get):
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {"symbol": "BTCUSDT", "price": "77521.50"},
    )
    mock_get.return_value.raise_for_status = lambda: None

    price = binance_futures_price("BTCUSDT")
    assert price == 77521.50
    mock_get.assert_called_once()
    assert "fapi.binance.com" in mock_get.call_args[0][0]


@patch("price_feeds.requests.get")
def test_binance_raises_on_http_error(mock_get):
    mock_get.return_value.raise_for_status.side_effect = Exception("503")
    with pytest.raises(PriceFeedError):
        binance_futures_price("BTCUSDT")


@patch("price_feeds.requests.get")
def test_okx_swap_price(mock_get):
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {"code": "0", "data": [{"last": "77500.1"}]},
    )
    mock_get.return_value.raise_for_status = lambda: None

    price = okx_swap_price("BTC-USDT-SWAP")
    assert price == 77500.1


@patch.dict("os.environ", {"TWELVEDATA_API_KEY": "test"})
@patch("price_feeds.requests.get")
def test_twelvedata_price(mock_get):
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {"price": "1.17150"},
    )
    mock_get.return_value.raise_for_status = lambda: None

    price = twelvedata_price("EUR/USD")
    assert price == 1.17150


def test_price_for_unknown_profile_asset_raises():
    with pytest.raises(PriceFeedError):
        price_for("retail", "UNKNOWN_ASSET")


@patch("price_feeds.binance_futures_price", return_value=77521.0)
def test_price_for_dispatches_retail_to_binance(mock_binance):
    assert price_for("retail", "BTCUSDT.P") == 77521.0
    mock_binance.assert_called_once_with("BTCUSDT")
