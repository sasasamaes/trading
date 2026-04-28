#!/usr/bin/env python3
"""
Per-asset backtest helper — valida si Mean Reversion necesita thresholds distintos por símbolo.

El PDF (PIEZA 02 página 34) advierte: "Esta estrategia funciona bien en cualquier activo —
RED FLAG". Una config rentable en NAS100 puede ser horrible en oro. Este script itera
sobre los assets del profile y reporta tabla comparativa WR/PF/Ret/DD por símbolo.

Uso:
    # Crypto via Binance API (sin key):
    python3 per_asset_backtest.py --crypto BTCUSDT,ETHUSDT --tf 1h --bars 300

    # Custom JSON data (forex/indices — pasa una carpeta con un .json por asset):
    python3 per_asset_backtest.py --json-dir /tmp/bars_per_asset --tf 1h

    # Específico al profile activo:
    python3 per_asset_backtest.py --profile fotmarkets

Strategy probada: Mean Reversion mecánica básica (la afinación per-asset viene después
si la tabla muestra disparidad).

Output: tabla markdown + JSON con todas las métricas + flags overfit por asset.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from backtest_split import temporal_split, degradation_flag  # noqa: E402


def _maybe_reexec_venv():
    """Si el python actual NO es el venv pero el venv existe, re-ejecutar con el
    venv python (binary modules requieren versión exacta de Python).
    Solo se invoca desde __main__ — NO durante imports."""
    venv_python = HERE / ".venv" / "bin" / "python"
    if (
        venv_python.exists()
        and Path(sys.executable).resolve() != venv_python.resolve()
        and not os.environ.get("WALLY_VENV_REEXEC")
    ):
        os.environ["WALLY_VENV_REEXEC"] = "1"
        os.execv(str(venv_python), [str(venv_python), __file__, *sys.argv[1:]])


try:
    import yfinance as _yf  # type: ignore
    _YF_AVAILABLE = True
except ImportError:
    _YF_AVAILABLE = False


# Mapeo símbolos del sistema → ticker Yahoo Finance
YF_SYMBOL_MAP = {
    # Forex (Yahoo usa SUFFIX=X)
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "USDCAD=X",
    # Metals (futures)
    "XAUUSD": "GC=F",         # Gold futures
    "XAGUSD": "SI=F",         # Silver futures
    # Indices (Yahoo)
    "NAS100": "^NDX",          # NASDAQ-100
    "SPX500": "^GSPC",         # S&P 500
    "US30":   "^DJI",          # Dow Jones
    "GER40":  "^GDAXI",        # DAX
    "UK100":  "^FTSE",         # FTSE 100
    # Crypto via Yahoo (alternativa a Binance)
    "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD",
}

# Yahoo Finance soporta intervalos limitados según rango histórico
YF_INTERVAL_MAP = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "60m", "4h": "60m",  # 4h no existe en Yahoo, mejor 60m y agrega
    "1d": "1d",
}


FEE = 0.0005  # 0.1% round-trip


def fetch_yfinance(symbol: str, interval: str = "1h", bars: int = 300) -> list[dict]:
    """
    Pull bars from Yahoo Finance via yfinance.
    Yahoo retorna en daily/intraday — la función decide period según interval.
    Mapea símbolos del sistema (EURUSD → EURUSD=X) automáticamente.
    """
    if not _YF_AVAILABLE:
        raise RuntimeError(
            "yfinance no instalado. Corre: bash .claude/scripts/setup_venv.sh"
        )
    yf_symbol = YF_SYMBOL_MAP.get(symbol, symbol)
    yf_interval = YF_INTERVAL_MAP.get(interval, interval)

    # Yahoo limita el rango por intervalo:
    # 1m: 7 días | 5m,15m,30m: 60 días | 60m: 730 días | 1d: muchos años
    if yf_interval in ("1m",):
        period = "7d"
    elif yf_interval in ("5m", "15m", "30m"):
        period = "60d"
    elif yf_interval in ("60m", "1h"):
        period = "60d"
    else:
        period = "1y"

    df = _yf.download(
        yf_symbol, period=period, interval=yf_interval,
        progress=False, auto_adjust=False, threads=False,
    )
    if df is None or df.empty:
        raise RuntimeError(f"yfinance no devolvió data para {yf_symbol}")
    # Flatten multi-index si yfinance devuelve cols (ticker, field)
    if hasattr(df.columns, "levels"):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

    out = []
    for ts, row in df.iterrows():
        try:
            out.append({
                "t": int(ts.timestamp() * 1000),
                "o": float(row["Open"]),
                "h": float(row["High"]),
                "l": float(row["Low"]),
                "c": float(row["Close"]),
                "v": float(row.get("Volume", 0) or 0),
            })
        except (KeyError, ValueError, TypeError):
            continue
    if bars and len(out) > bars:
        out = out[-bars:]
    return out


def fetch_binance_klines(symbol: str, interval: str = "1h", limit: int = 300) -> list[dict]:
    """Pull klines from Binance public API (no key needed)."""
    qs = urllib.parse.urlencode({"symbol": symbol, "interval": interval, "limit": limit})
    url = f"https://api.binance.com/api/v3/klines?{qs}"
    with urllib.request.urlopen(url, timeout=15) as r:
        raw = json.loads(r.read())
    return [
        {"t": k[0], "o": float(k[1]), "h": float(k[2]),
         "l": float(k[3]), "c": float(k[4]), "v": float(k[5])}
        for k in raw
    ]


def load_json_bars(path: str) -> list[dict]:
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("bars") or data.get("data") or list(data.values())[0]
    return data


def sma(values: list[float], n: int) -> list[float]:
    out = []
    for i in range(len(values)):
        if i + 1 < n:
            out.append(None)
        else:
            out.append(sum(values[i + 1 - n:i + 1]) / n)
    return out


def stdev(values: list[float], n: int) -> list[float]:
    out = []
    for i in range(len(values)):
        if i + 1 < n:
            out.append(None)
            continue
        window = values[i + 1 - n:i + 1]
        m = sum(window) / n
        out.append((sum((x - m) ** 2 for x in window) / n) ** 0.5)
    return out


def rsi(closes: list[float], length: int = 14) -> list[float | None]:
    if len(closes) < length + 1:
        return [None] * len(closes)
    gains = [0.0]
    losses = [0.0]
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    avg_gain = sum(gains[1:length + 1]) / length
    avg_loss = sum(losses[1:length + 1]) / length
    out: list[float | None] = [None] * length
    rs = avg_gain / avg_loss if avg_loss > 0 else 999
    out.append(100 - (100 / (1 + rs)))
    for i in range(length + 1, len(closes)):
        avg_gain = (avg_gain * (length - 1) + gains[i]) / length
        avg_loss = (avg_loss * (length - 1) + losses[i]) / length
        rs = avg_gain / avg_loss if avg_loss > 0 else 999
        out.append(100 - (100 / (1 + rs)))
    return out


def atr(bars: list[dict], length: int = 14) -> list[float | None]:
    n = len(bars)
    if n < length + 1:
        return [None] * n
    trs = [0.0]
    for i in range(1, n):
        h, l, pc = bars[i]["h"], bars[i]["l"], bars[i - 1]["c"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    out: list[float | None] = [None] * length
    a = sum(trs[1:length + 1]) / length
    out.append(a)
    for i in range(length + 1, n):
        a = (a * (length - 1) + trs[i]) / length
        out.append(a)
    return out


def donchian(bars: list[dict], length: int = 15) -> tuple[list[float | None], list[float | None]]:
    highs = [b["h"] for b in bars]
    lows = [b["l"] for b in bars]
    hi: list[float | None] = []
    lo: list[float | None] = []
    for i in range(len(bars)):
        if i + 1 < length:
            hi.append(None); lo.append(None)
        else:
            hi.append(max(highs[i + 1 - length:i + 1]))
            lo.append(min(lows[i + 1 - length:i + 1]))
    return hi, lo


def simulate_mean_reversion(
    bars: list[dict],
    donchian_len: int = 15,
    rsi_os: float = 35,
    rsi_ob: float = 65,
    bb_len: int = 20,
    bb_mult: float = 2.0,
    atr_len: int = 14,
    sl_atr_mult: float = 1.5,
    tp_mults: tuple = (2.5, 4.0, 6.0),
    capital: float = 100.0,
) -> dict:
    """
    Mean Reversion mecánica con 4 filtros (Donchian + RSI + BB + close color).
    Position management: 40/40/20 split, SL→BE after TP1.
    """
    closes = [b["c"] for b in bars]
    rsi_vals = rsi(closes, 14)
    bb_mid = sma(closes, bb_len)
    bb_sd = stdev(closes, bb_len)
    atr_vals = atr(bars, atr_len)
    don_hi, don_lo = donchian(bars, donchian_len)

    equity = capital
    trades: list[dict] = []
    open_trade = None
    peak_equity = equity
    max_dd = 0.0

    for i in range(max(donchian_len, bb_len, atr_len) + 2, len(bars)):
        bar = bars[i]
        if any(x is None for x in (rsi_vals[i], bb_mid[i], bb_sd[i], atr_vals[i], don_hi[i], don_lo[i])):
            continue
        bb_up = bb_mid[i] + bb_mult * bb_sd[i]
        bb_lo = bb_mid[i] - bb_mult * bb_sd[i]

        # Manage open trade
        if open_trade:
            t = open_trade
            # Check SL
            if (t["side"] == "long" and bar["l"] <= t["sl"]) or \
               (t["side"] == "short" and bar["h"] >= t["sl"]):
                pnl = (t["sl"] - t["entry"]) * (1 if t["side"] == "long" else -1) * t["size_remaining"]
                pnl -= abs(t["entry"]) * t["size_remaining"] * FEE
                equity += pnl
                trades.append({**t, "exit": t["sl"], "exit_reason": "SL", "pnl": pnl})
                open_trade = None
            else:
                # Check TPs
                exited = False
                for tp_idx, (tp_pct, tp_size_pct) in enumerate(zip(t["tps"], [0.4, 0.4, 0.2])):
                    if t.get(f"tp{tp_idx+1}_hit"):
                        continue
                    hit = (t["side"] == "long" and bar["h"] >= tp_pct) or \
                          (t["side"] == "short" and bar["l"] <= tp_pct)
                    if hit:
                        size_to_close = t["size_initial"] * tp_size_pct
                        pnl = (tp_pct - t["entry"]) * (1 if t["side"] == "long" else -1) * size_to_close
                        pnl -= abs(t["entry"]) * size_to_close * FEE
                        equity += pnl
                        t[f"tp{tp_idx+1}_hit"] = True
                        t["size_remaining"] -= size_to_close
                        if tp_idx == 0:
                            t["sl"] = t["entry"]  # SL→BE after TP1
                        if tp_idx == len(t["tps"]) - 1 or t["size_remaining"] <= 0:
                            trades.append({**t, "exit": tp_pct, "exit_reason": f"TP{tp_idx+1}", "pnl": pnl})
                            open_trade = None
                            exited = True
                            break

        # Look for new entry
        if not open_trade:
            close_color = "green" if bar["c"] > bar["o"] else "red"
            # LONG setup
            long_sig = (
                bar["l"] <= don_lo[i] * 1.001 and
                rsi_vals[i] < rsi_os and
                bar["l"] <= bb_lo and
                close_color == "green"
            )
            short_sig = (
                bar["h"] >= don_hi[i] * 0.999 and
                rsi_vals[i] > rsi_ob and
                bar["h"] >= bb_up and
                close_color == "red"
            )
            if long_sig:
                entry = bar["c"]
                sl_dist = atr_vals[i] * sl_atr_mult
                sl = entry - sl_dist
                tps = [entry + sl_dist * m for m in tp_mults]
                size = (equity * 0.02) / sl_dist  # 2% risk
                open_trade = {"side": "long", "entry": entry, "sl": sl, "tps": tps,
                              "size_initial": size, "size_remaining": size, "open_bar": i}
            elif short_sig:
                entry = bar["c"]
                sl_dist = atr_vals[i] * sl_atr_mult
                sl = entry + sl_dist
                tps = [entry - sl_dist * m for m in tp_mults]
                size = (equity * 0.02) / sl_dist
                open_trade = {"side": "short", "entry": entry, "sl": sl, "tps": tps,
                              "size_initial": size, "size_remaining": size, "open_bar": i}

        peak_equity = max(peak_equity, equity)
        dd = (peak_equity - equity) / peak_equity * 100 if peak_equity > 0 else 0
        max_dd = max(max_dd, dd)

    # Force close any open trade at end-of-data (mark-to-market with last close)
    if open_trade:
        last = bars[-1]["c"]
        t = open_trade
        pnl = (last - t["entry"]) * (1 if t["side"] == "long" else -1) * t["size_remaining"]
        pnl -= abs(t["entry"]) * t["size_remaining"] * FEE
        equity += pnl
        trades.append({**t, "exit": last, "exit_reason": "FORCED_EOD", "pnl": pnl})

    n = len(trades)
    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    wr = (len(wins) / n * 100) if n else 0
    gross_win = sum(t["pnl"] for t in wins)
    gross_loss = abs(sum(t["pnl"] for t in losses)) or 1e-9
    pf = gross_win / gross_loss
    ret = (equity - capital) / capital * 100

    return {
        "n": n,
        "wr": round(wr, 1),
        "pf": round(pf, 2),
        "ret": round(ret, 2),
        "dd": round(max_dd, 2),
        "final_equity": round(equity, 2),
    }


def run_per_asset(asset_bars: dict[str, list[dict]], params: dict | None = None) -> dict:
    """
    Run backtest + OOS validation per asset.
    Returns dict {asset: {full, train, test, oos_status}}.
    """
    params = params or {}
    out = {}
    for asset, bars in asset_bars.items():
        full = simulate_mean_reversion(bars, **params)
        if len(bars) >= 50:
            try:
                train_bars, test_bars = temporal_split(bars, 0.7)
                train_m = simulate_mean_reversion(train_bars, **params)
                test_m = simulate_mean_reversion(test_bars, **params)
                oos_status, oos_reasons = degradation_flag(train_m, test_m)
            except ValueError as e:
                train_m = test_m = None
                oos_status = "SKIP"
                oos_reasons = [str(e)]
        else:
            train_m = test_m = None
            oos_status = "SKIP"
            oos_reasons = ["data insufficient for split"]

        out[asset] = {
            "bars_n": len(bars),
            "full": full,
            "train": train_m,
            "test": test_m,
            "oos_status": oos_status,
            "oos_reasons": oos_reasons,
        }
    return out


def render_table(results: dict) -> str:
    rows = ["| Asset | n | WR% | PF | Ret% | DD% | OOS |", "|---|---|---|---|---|---|---|"]
    for asset, r in results.items():
        f = r["full"]
        rows.append(
            f"| {asset} | {f['n']} | {f['wr']} | {f['pf']} | {f['ret']:+.1f} "
            f"| {f['dd']} | {r['oos_status']} |"
        )
    return "\n".join(rows)


def render_report(results: dict) -> str:
    lines = ["# Per-Asset Backtest Report\n", "## Resumen\n", render_table(results), "\n"]
    # Detect heterogeneity
    all_full = [r["full"] for r in results.values()]
    wrs = [m["wr"] for m in all_full if m["n"] > 0]
    if wrs and max(wrs) - min(wrs) > 30:
        lines.append("⚠️ **Disparidad alta entre assets** (WR difiere >30pp). "
                     "Considera tunear thresholds per-asset o excluir los peores.\n")
    fails = [a for a, r in results.items() if r["oos_status"] == "FAIL"]
    if fails:
        lines.append(f"❌ **OOS FAIL en**: {', '.join(fails)} — overfit detectado, NO operar estos assets.\n")
    return "\n".join(lines)


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crypto", help="Comma-separated symbols (Binance), e.g. BTCUSDT,ETHUSDT")
    ap.add_argument("--yf", help="Comma-separated symbols (Yahoo Finance), e.g. EURUSD,GBPUSD,NAS100,XAUUSD")
    ap.add_argument("--json-dir", help="Directory with one <ASSET>.json per asset (override)")
    ap.add_argument("--profile", choices=["retail", "ftmo", "fotmarkets"], help="Use profile defaults (auto-fetches all assets via Binance+Yahoo)")
    ap.add_argument("--tf", default="1h", help="Timeframe (1m/5m/15m/1h/4h/1d)")
    ap.add_argument("--bars", type=int, default=300, help="Bars per asset")
    ap.add_argument("--out", default=None, help="Write JSON results to file")
    return ap.parse_args()


PROFILE_DEFAULTS = {
    "retail": {"crypto": ["BTCUSDT"], "yf": []},
    "ftmo": {
        "crypto": ["BTCUSDT", "ETHUSDT"],
        "yf": ["EURUSD", "GBPUSD", "NAS100", "SPX500"],
    },
    "fotmarkets": {
        "crypto": ["BTCUSDT", "ETHUSDT"],
        "yf": ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "NAS100", "SPX500"],
    },
}


def main() -> int:
    args = parse_args()
    asset_bars: dict[str, list[dict]] = {}

    crypto_symbols: list[str] = []
    yf_symbols: list[str] = []
    json_dir: str | None = args.json_dir

    if args.profile:
        defaults = PROFILE_DEFAULTS[args.profile]
        crypto_symbols.extend(defaults.get("crypto", []))
        yf_symbols.extend(defaults.get("yf", []))
        if yf_symbols and not _YF_AVAILABLE and not json_dir:
            print(f"⚠️ Profile {args.profile} requiere yfinance para {yf_symbols}. "
                  "Corre: bash .claude/scripts/setup_venv.sh", file=sys.stderr)
            yf_symbols = []
    if args.crypto:
        crypto_symbols.extend(args.crypto.split(","))
    if args.yf:
        yf_symbols.extend(args.yf.split(","))
    crypto_symbols = list(dict.fromkeys(crypto_symbols))
    yf_symbols = list(dict.fromkeys(yf_symbols))

    for sym in crypto_symbols:
        try:
            print(f"[Binance] Fetching {sym} {args.tf} ({args.bars} bars)...", file=sys.stderr)
            asset_bars[sym] = fetch_binance_klines(sym, args.tf, args.bars)
        except Exception as e:
            print(f"  ERROR fetching {sym}: {e}", file=sys.stderr)

    for sym in yf_symbols:
        try:
            print(f"[Yahoo] Fetching {sym} ({YF_SYMBOL_MAP.get(sym, sym)}) {args.tf}...", file=sys.stderr)
            asset_bars[sym] = fetch_yfinance(sym, args.tf, args.bars)
        except Exception as e:
            print(f"  ERROR fetching {sym}: {e}", file=sys.stderr)

    if json_dir:
        for fname in sorted(os.listdir(json_dir)):
            if not fname.endswith(".json"):
                continue
            asset = fname[:-5]
            try:
                asset_bars[asset] = load_json_bars(os.path.join(json_dir, fname))
            except Exception as e:
                print(f"  ERROR loading {fname}: {e}", file=sys.stderr)

    if not asset_bars:
        print("No assets loaded. Use --crypto, --yf, --json-dir, or --profile.", file=sys.stderr)
        return 2

    results = run_per_asset(asset_bars)
    print(render_report(results))

    if args.out:
        with open(args.out, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nJSON written to {args.out}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    _maybe_reexec_venv()
    # If we got here, we're already in venv (or no venv exists) — re-import yfinance
    # in case the re-exec happened (in that case _YF_AVAILABLE was False at first import).
    if not _YF_AVAILABLE:
        try:
            import yfinance as _yf  # noqa: F811
            _YF_AVAILABLE = True
        except ImportError:
            pass
    sys.exit(main())
