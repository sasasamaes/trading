#!/usr/bin/env python3
"""Sentiment Aggregator — ensamblado NLP multi-fuente para BTC.

Fuentes y pesos:
  - Fear & Greed Index ....... 35%  (señal mainstream confiable)
  - Reddit VADER (3 subs) .... 20%  (sentiment retail)
  - News RSS VADER (3 feeds).. 30%  (noticias crypto)
  - Funding rate contrarian .. 15%  (posicionamiento derivados)

Output:
  - final_score: 0-100
  - interpretación + sesgo recomendado
  - breakdown por fuente + samples

Uso:
  python3 aggregator.py             # output humano
  python3 aggregator.py --json      # JSON estructurado
  python3 aggregator.py --quiet     # solo score final entero
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict

from sources import (
    fetch_fear_greed,
    fetch_reddit_sentiment,
    fetch_news_sentiment,
    fetch_funding_sentiment,
)

WEIGHTS = {
    "fear_greed": 0.35,
    "reddit": 0.20,
    "news": 0.30,
    "funding": 0.15,
}


def _interpret(score: int) -> Dict[str, str]:
    if score < 20:
        return {
            "label": "EXTREME FEAR",
            "emoji": "🔴",
            "bias": "Contrarian BULLISH — mercado capitulando; setups long de reversión tienen edge.",
            "action": "Si régimen = RANGE y técnico 4/4 LONG → aumentar convicción. EVITAR shorts.",
        }
    if score < 35:
        return {
            "label": "FEAR",
            "emoji": "🟠",
            "bias": "Ligero contrarian bullish — precaución con shorts.",
            "action": "Sesgo leve long. Setups short requieren confluencia extra.",
        }
    if score < 55:
        return {
            "label": "NEUTRAL-FEAR",
            "emoji": "🟡",
            "bias": "Sin sesgo fuerte — operar técnico puro.",
            "action": "Seguir 4 filtros mecánicamente sin sobreajustar por sentiment.",
        }
    if score < 70:
        return {
            "label": "NEUTRAL-GREED",
            "emoji": "🟢",
            "bias": "Sin sesgo fuerte — operar técnico puro.",
            "action": "Seguir 4 filtros mecánicamente sin sobreajustar por sentiment.",
        }
    if score < 85:
        return {
            "label": "GREED",
            "emoji": "🟢",
            "bias": "Ligero contrarian bearish — precaución con longs tardíos.",
            "action": "Longs nuevos requieren confluencia extra; shorts en resistencia ganan edge.",
        }
    return {
        "label": "EXTREME GREED",
        "emoji": "🔴",
        "bias": "Contrarian BEARISH — mercado eufórico; setups short en resistencia tienen edge.",
        "action": "Si régimen = RANGE y técnico 4/4 SHORT → aumentar convicción. EVITAR longs nuevos.",
    }


def aggregate() -> Dict[str, Any]:
    fg_score, fg_note = fetch_fear_greed()
    reddit_score, reddit_n, reddit_top = fetch_reddit_sentiment()
    news_score, news_n, news_top = fetch_news_sentiment()
    funding_score, funding_note = fetch_funding_sentiment()

    components: Dict[str, Any] = {
        "fear_greed": {"score": fg_score, "note": fg_note, "weight": WEIGHTS["fear_greed"]},
        "reddit": {"score": reddit_score, "samples": reddit_n, "weight": WEIGHTS["reddit"]},
        "news": {"score": news_score, "samples": news_n, "weight": WEIGHTS["news"]},
        "funding": {"score": funding_score, "note": funding_note, "weight": WEIGHTS["funding"]},
    }

    # Weighted average, ignorando fuentes que fallaron
    total_w = 0.0
    weighted_sum = 0.0
    active_sources = []
    for name, comp in components.items():
        if comp.get("score") is not None:
            total_w += comp["weight"]
            weighted_sum += comp["weight"] * comp["score"]
            active_sources.append(name)

    if total_w == 0:
        final_score = None
        interpretation = {"label": "UNAVAILABLE", "emoji": "⚪", "bias": "Sin datos", "action": "Reintenta"}
    else:
        final_score = round(weighted_sum / total_w)
        interpretation = _interpret(final_score)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol": "BTC",
        "final_score": final_score,
        "active_sources": active_sources,
        "coverage_pct": round(100 * total_w / sum(WEIGHTS.values()), 1),
        "interpretation": interpretation,
        "components": components,
        "reddit_top": reddit_top,
        "news_top": news_top,
    }


def _format_human(result: Dict[str, Any]) -> str:
    out = []
    out.append("")
    out.append("════════════════════════════════════════════════════")
    out.append(f" 🌡️  SENTIMENT AGGREGATOR — BTC")
    out.append(f" ⏰ {result['timestamp']}")
    out.append("════════════════════════════════════════════════════")
    out.append("")

    if result["final_score"] is None:
        out.append(" ⚠️  Sin datos — todas las fuentes fallaron")
        return "\n".join(out)

    interp = result["interpretation"]
    out.append(f" {interp['emoji']}  FINAL SCORE: {result['final_score']}/100 — {interp['label']}")
    out.append(f"     coverage: {result['coverage_pct']}% de fuentes activas")
    out.append("")
    out.append(f" 📍 Sesgo: {interp['bias']}")
    out.append(f" 🎯 Acción: {interp['action']}")
    out.append("")
    out.append(" ── Breakdown por fuente ────────────────────────────")

    comps = result["components"]
    fg = comps["fear_greed"]
    if fg["score"] is not None:
        out.append(f"   F&G Index:    {fg['score']:>3}  ({fg['note']})")
    else:
        out.append(f"   F&G Index:    N/A  ({fg['note']})")

    reddit = comps["reddit"]
    if reddit["score"] is not None:
        out.append(f"   Reddit VADER: {reddit['score']:>3}  (n={reddit['samples']} posts BTC)")
    else:
        out.append(f"   Reddit VADER: N/A  (sin posts)")

    news = comps["news"]
    if news["score"] is not None:
        out.append(f"   News VADER:   {news['score']:>3}  (n={news['samples']} items)")
    else:
        out.append(f"   News VADER:   N/A  (sin feeds)")

    funding = comps["funding"]
    if funding["score"] is not None:
        out.append(f"   Funding:      {funding['score']:>3}  ({funding['note']})")
    else:
        out.append(f"   Funding:      N/A  ({funding['note']})")

    out.append("")

    if result["reddit_top"]:
        out.append(" 📌 Top Reddit (por intensidad):")
        for title, s in result["reddit_top"][:3]:
            arrow = "📈" if s > 0.1 else ("📉" if s < -0.1 else "➖")
            out.append(f"   {arrow} [{s:+.2f}] {title}")
        out.append("")

    if result["news_top"]:
        out.append(" 📰 Top News (por intensidad):")
        for title, s in result["news_top"][:3]:
            arrow = "📈" if s > 0.1 else ("📉" if s < -0.1 else "➖")
            out.append(f"   {arrow} [{s:+.2f}] {title}")
        out.append("")

    out.append("════════════════════════════════════════════════════")
    return "\n".join(out)


def main() -> int:
    result = aggregate()

    if "--json" in sys.argv:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif "--quiet" in sys.argv:
        if result["final_score"] is not None:
            print(result["final_score"])
        else:
            return 1
    else:
        print(_format_human(result))

    return 0 if result["final_score"] is not None else 2


if __name__ == "__main__":
    sys.exit(main())
