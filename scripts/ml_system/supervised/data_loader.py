"""Descarga histórico OHLCV de Binance (sin API key, endpoints públicos).

Binance devuelve máx 1000 velas por request. Paginamos hacia atrás en el tiempo
y guardamos a disco en formato parquet/csv para reuso.
"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared.config import BINANCE_KLINES_URL, DATA_DIR, SYMBOL, PRIMARY_TF

# Tamaño de barra por timeframe (ms)
_TF_MS = {
    "1m": 60_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "4h": 14_400_000,
    "1d": 86_400_000,
}

_COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume",
    "close_time", "quote_volume", "trades",
    "taker_buy_base", "taker_buy_quote", "ignore",
]


def fetch_klines(
    symbol: str = SYMBOL,
    interval: str = PRIMARY_TF,
    start_ms: Optional[int] = None,
    end_ms: Optional[int] = None,
    limit: int = 1000,
) -> pd.DataFrame:
    """Una sola llamada paginada (hasta 1000 velas)."""
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
    }
    if start_ms is not None:
        params["startTime"] = start_ms
    if end_ms is not None:
        params["endTime"] = end_ms

    r = requests.get(BINANCE_KLINES_URL, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    if not data:
        return pd.DataFrame(columns=_COLUMNS)

    df = pd.DataFrame(data, columns=_COLUMNS)
    num_cols = ["open", "high", "low", "close", "volume", "quote_volume",
                "taker_buy_base", "taker_buy_quote"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
    return df


def download_history(
    symbol: str = SYMBOL,
    interval: str = PRIMARY_TF,
    days: int = 365,
    verbose: bool = True,
) -> pd.DataFrame:
    """Descarga `days` días de velas `interval` paginando hacia atrás."""
    if interval not in _TF_MS:
        raise ValueError(f"Timeframe no soportado: {interval}")

    bar_ms = _TF_MS[interval]
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_ms = now_ms - days * 86_400_000

    all_df = []
    cursor = start_ms
    iteration = 0

    while cursor < now_ms:
        df = fetch_klines(symbol, interval, start_ms=cursor, limit=1000)
        if df.empty:
            break
        all_df.append(df)
        last_ms = int(df["close_time"].iloc[-1].timestamp() * 1000)
        if last_ms <= cursor:
            break
        cursor = last_ms + 1
        iteration += 1
        if verbose and iteration % 5 == 0:
            last_date = df["close_time"].iloc[-1].strftime("%Y-%m-%d %H:%M")
            print(f"  [{iteration}] fetched up to {last_date} ({sum(len(d) for d in all_df)} rows)")
        # Rate limit courteous pause
        time.sleep(0.05)

    if not all_df:
        return pd.DataFrame(columns=_COLUMNS)

    result = pd.concat(all_df, ignore_index=True)
    result = result.drop_duplicates(subset=["open_time"]).sort_values("open_time").reset_index(drop=True)
    return result


def cached_history(
    symbol: str = SYMBOL,
    interval: str = PRIMARY_TF,
    days: int = 365,
    refresh: bool = False,
    verbose: bool = True,
) -> pd.DataFrame:
    """Lee de cache local si existe, sino descarga y guarda."""
    cache_file = DATA_DIR / f"{symbol}_{interval}_{days}d.parquet"
    if cache_file.exists() and not refresh:
        if verbose:
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            print(f"[cache] {cache_file.name} ({age.total_seconds()/3600:.1f}h old)")
        try:
            return pd.read_parquet(cache_file)
        except Exception:
            pass  # Fall through to re-download

    if verbose:
        print(f"[download] {symbol} {interval} últimos {days} días...")
    df = download_history(symbol, interval, days=days, verbose=verbose)
    if not df.empty:
        try:
            df.to_parquet(cache_file, index=False)
            if verbose:
                print(f"[save] {cache_file} ({len(df)} rows)")
        except Exception as e:
            # Fallback a CSV si parquet falla (no pyarrow)
            csv_file = cache_file.with_suffix(".csv")
            df.to_csv(csv_file, index=False)
            if verbose:
                print(f"[save] parquet failed ({e}); saved as {csv_file}")
    return df


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", default=SYMBOL)
    p.add_argument("--interval", default=PRIMARY_TF)
    p.add_argument("--days", type=int, default=365)
    p.add_argument("--refresh", action="store_true")
    args = p.parse_args()

    df = cached_history(args.symbol, args.interval, days=args.days, refresh=args.refresh)
    print(f"\nShape: {df.shape}")
    print(f"Range: {df['open_time'].min()} → {df['open_time'].max()}")
    print(df.head(3))
    print("...")
    print(df.tail(3))
