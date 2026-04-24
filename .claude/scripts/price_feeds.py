"""HTTP price feeds — no credentials required for public endpoints.

Providers:
- Binance Futures (fapi.binance.com) — BTCUSDT perpetual
- OKX swap (okx.com) — backup for BTC
- TwelveData (api.twelvedata.com) — EUR/USD, GBP/USD, indices. Free tier 800 req/day.

Asset-symbol mapping per profile in ASSET_MAP.
"""
from __future__ import annotations

import os
import requests
from typing import Callable

DEFAULT_TIMEOUT = 5  # seconds


class PriceFeedError(RuntimeError):
    pass


def _get_json(url: str, params: dict | None = None) -> dict:
    try:
        r = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise PriceFeedError(f"GET {url} failed: {e}") from e


def binance_futures_price(symbol: str) -> float:
    data = _get_json(
        "https://fapi.binance.com/fapi/v1/ticker/price",
        {"symbol": symbol},
    )
    return float(data["price"])


def okx_swap_price(instId: str) -> float:
    data = _get_json(
        "https://www.okx.com/api/v5/market/ticker",
        {"instId": instId},
    )
    if data.get("code") != "0" or not data.get("data"):
        raise PriceFeedError(f"OKX error: {data}")
    return float(data["data"][0]["last"])


def twelvedata_price(symbol: str) -> float:
    api_key = os.environ.get("TWELVEDATA_API_KEY")
    if not api_key:
        raise PriceFeedError(
            "TWELVEDATA_API_KEY not set — add to .claude/.env. "
            "Signup free: twelvedata.com (800 req/day tier)"
        )
    data = _get_json(
        "https://api.twelvedata.com/price",
        {"symbol": symbol, "apikey": api_key},
    )
    if "price" not in data:
        raise PriceFeedError(f"TwelveData unexpected response: {data}")
    return float(data["price"])


# (profile, asset) -> callable
ASSET_MAP: dict[tuple[str, str], Callable[[], float]] = {
    ("retail", "BTCUSDT.P"): lambda: binance_futures_price("BTCUSDT"),
    ("retail-bingx", "BTCUSDT.P"): lambda: binance_futures_price("BTCUSDT"),
    # ftmo uses MT5 symbols; fapi prefix as proxy for retail monitoring
    ("ftmo", "BTCUSD"): lambda: binance_futures_price("BTCUSDT"),
    ("ftmo", "ETHUSD"): lambda: binance_futures_price("ETHUSDT"),
    ("ftmo", "EURUSD"): lambda: twelvedata_price("EUR/USD"),
    ("ftmo", "GBPUSD"): lambda: twelvedata_price("GBP/USD"),
    ("ftmo", "NAS100"): lambda: twelvedata_price("NDX"),
    ("ftmo", "SPX500"): lambda: twelvedata_price("SPX"),
    # fotmarkets (same mapping as ftmo)
    ("fotmarkets", "BTCUSD"): lambda: binance_futures_price("BTCUSDT"),
    ("fotmarkets", "ETHUSD"): lambda: binance_futures_price("ETHUSDT"),
    ("fotmarkets", "EURUSD"): lambda: twelvedata_price("EUR/USD"),
    ("fotmarkets", "GBPUSD"): lambda: twelvedata_price("GBP/USD"),
    ("fotmarkets", "USDJPY"): lambda: twelvedata_price("USD/JPY"),
    ("fotmarkets", "XAUUSD"): lambda: twelvedata_price("XAU/USD"),
    ("fotmarkets", "NAS100"): lambda: twelvedata_price("NDX"),
    ("fotmarkets", "SPX500"): lambda: twelvedata_price("SPX"),
}


def price_for(profile: str, asset: str) -> float:
    """Dispatch to the right feed. Raises PriceFeedError if unknown."""
    key = (profile, asset)
    if key not in ASSET_MAP:
        raise PriceFeedError(f"No price feed mapping for ({profile!r}, {asset!r})")
    return ASSET_MAP[key]()
