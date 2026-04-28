#!/usr/bin/env python3
"""
Out-of-sample backtest helper — detector de overfitting.

El PDF (PIEZA 02 página 69) advierte: "PROBAR CON OTRO CONJUNTO DE DATOS — Esto puede
hacer que estés en un OVERFITTING". Esta utilidad aplica split temporal 70/30 y reporta
degradación entre train (in-sample) y test (out-of-sample).

Uso programático (importable):
    from backtest_split import temporal_split, report_oos

    train_bars, test_bars = temporal_split(bars, train_ratio=0.7)
    train_metrics = run_backtest(train_bars, params)
    test_metrics  = run_backtest(test_bars,  params)
    print(report_oos(train_metrics, test_metrics))

Uso CLI (para validar resultados ya computados):
    python3 backtest_split.py --train '{"wr":80,"pf":2.5,"ret":12,"dd":3,"n":10}' \\
                              --test  '{"wr":50,"pf":1.1,"ret":2,"dd":8,"n":4}'

Métricas esperadas en cada dict:
  n   = número de trades
  wr  = win rate (%)
  pf  = profit factor
  ret = retorno % sobre capital
  dd  = max drawdown %
  expectancy (opcional, calculada si falta) = (wr/100)*avg_win - ((100-wr)/100)*avg_loss
"""
from __future__ import annotations
import argparse
import json
import sys


# Thresholds para clasificar degradación
WR_DEGRADATION_WARN = 10   # pp
WR_DEGRADATION_FAIL = 20   # pp
PF_DEGRADATION_WARN = 0.30  # pf train * 0.7
PF_DEGRADATION_FAIL = 0.50  # pf train * 0.5
RET_FLIP_FAIL = True       # train +, test - = fail directo


def temporal_split(bars: list, train_ratio: float = 0.7) -> tuple[list, list]:
    """
    Split temporal SECUENCIAL (NO shuffle — los datos de mercado tienen orden).
    Train = primeros train_ratio. Test = el resto.
    """
    if not 0.5 <= train_ratio <= 0.9:
        raise ValueError("train_ratio debe estar en [0.5, 0.9]")
    n = len(bars)
    if n < 50:
        raise ValueError(f"Mínimo 50 bars para split fiable, got {n}")
    cut = int(n * train_ratio)
    return bars[:cut], bars[cut:]


def degradation_flag(train: dict, test: dict) -> tuple[str, list[str]]:
    """
    Returns (overall_status, [reasons]).
    Status: PASS | WARN | FAIL.
    """
    reasons: list[str] = []
    fail = False
    warn = False

    # n trades en test (muestra mínima)
    if test.get("n", 0) < 3:
        warn = True
        reasons.append(f"⚠️ test n={test.get('n',0)} <3 trades, muestra ínfima")

    # WR degradation
    wr_t = train.get("wr", 0)
    wr_o = test.get("wr", 0)
    wr_diff = wr_t - wr_o
    if wr_diff >= WR_DEGRADATION_FAIL:
        fail = True
        reasons.append(f"❌ WR cayó {wr_diff:.1f}pp ({wr_t}→{wr_o}) [overfit fuerte]")
    elif wr_diff >= WR_DEGRADATION_WARN:
        warn = True
        reasons.append(f"⚠️ WR cayó {wr_diff:.1f}pp ({wr_t}→{wr_o})")

    # PF degradation
    pf_t = train.get("pf", 0)
    pf_o = test.get("pf", 0)
    if pf_t > 0:
        pf_drop = (pf_t - pf_o) / pf_t
        if pf_drop >= PF_DEGRADATION_FAIL:
            fail = True
            reasons.append(f"❌ PF cayó {pf_drop*100:.0f}% ({pf_t:.2f}→{pf_o:.2f})")
        elif pf_drop >= PF_DEGRADATION_WARN:
            warn = True
            reasons.append(f"⚠️ PF cayó {pf_drop*100:.0f}% ({pf_t:.2f}→{pf_o:.2f})")

    # Return sign flip (gana en train, pierde en test)
    if RET_FLIP_FAIL:
        ret_t = train.get("ret", 0)
        ret_o = test.get("ret", 0)
        if ret_t > 0 and ret_o < 0:
            fail = True
            reasons.append(f"❌ Retorno se invirtió: train {ret_t:+.1f}% → test {ret_o:+.1f}%")

    # DD explosivo en test
    dd_t = train.get("dd", 0)
    dd_o = test.get("dd", 0)
    if dd_o > dd_t * 2 and dd_o > 5:
        warn = True
        reasons.append(f"⚠️ DD se duplicó: {dd_t:.1f}% → {dd_o:.1f}%")

    if fail:
        return "FAIL", reasons
    if warn:
        return "WARN", reasons
    return "PASS", reasons or ["✅ Métricas estables train→test"]


def report_oos(train: dict, test: dict, label: str = "") -> str:
    """Markdown report comparing in-sample (train) vs out-of-sample (test)."""
    status, reasons = degradation_flag(train, test)
    header = f"## OOS Validation{(' — '+label) if label else ''}"
    table = (
        "| Métrica | Train (IS) | Test (OOS) | Δ |\n"
        "|---|---|---|---|\n"
        f"| Trades | {train.get('n','-')} | {test.get('n','-')} | — |\n"
        f"| Win Rate | {train.get('wr','-')}% | {test.get('wr','-')}% "
        f"| {train.get('wr',0)-test.get('wr',0):+.1f}pp |\n"
        f"| Profit Factor | {train.get('pf','-')} | {test.get('pf','-')} "
        f"| {train.get('pf',0)-test.get('pf',0):+.2f} |\n"
        f"| Return | {train.get('ret','-')}% | {test.get('ret','-')}% "
        f"| {train.get('ret',0)-test.get('ret',0):+.1f}pp |\n"
        f"| Max DD | {train.get('dd','-')}% | {test.get('dd','-')}% "
        f"| {test.get('dd',0)-train.get('dd',0):+.1f}pp |\n"
    )
    verdict = {
        "PASS": "✅ **PASS** — sin overfit detectado",
        "WARN": "⚠️ **WARN** — degradación notable, validar con más data",
        "FAIL": "❌ **FAIL** — overfitting probable, NO operar esta config",
    }[status]
    reasons_md = "\n".join(f"- {r}" for r in reasons)
    return f"{header}\n\n{table}\n{verdict}\n\n{reasons_md}\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True, help='JSON metrics dict for train, e.g. \'{"wr":80,...}\'')
    ap.add_argument("--test", required=True, help='JSON metrics dict for test')
    ap.add_argument("--label", default="", help="Label for this validation (e.g. strategy name)")
    args = ap.parse_args()

    try:
        train = json.loads(args.train)
        test = json.loads(args.test)
    except json.JSONDecodeError as e:
        print(f"ERROR parsing JSON: {e}", file=sys.stderr)
        return 2

    print(report_oos(train, test, args.label))
    return 0


if __name__ == "__main__":
    sys.exit(main())
