"""Fuentes de datos para el agregador de sentimiento.

Cada función retorna (score_0_100, sample_count, top_items) o (None, 0, []) si falla.
El score 0-100 mapea:
  0  = extreme fear / muy bearish
  50 = neutral
  100= extreme greed / muy bullish
"""
import re
from typing import List, Tuple, Optional

import requests
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_BTC_PATTERN = re.compile(r"\b(btc|bitcoin)\b", re.IGNORECASE)
_UA = {"User-Agent": "trading-sentiment-bot/1.0 (personal research)"}

_analyzer = SentimentIntensityAnalyzer()


def _vader_to_100(compound: float) -> int:
    """Mapea VADER compound [-1, 1] a [0, 100]."""
    return round((compound + 1) * 50)


def fetch_fear_greed() -> Tuple[Optional[int], str]:
    """Fear & Greed Index (alternative.me) — ya es 0-100."""
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=2", timeout=10)
        r.raise_for_status()
        data = r.json()["data"]
        current = int(data[0]["value"])
        classification = data[0]["value_classification"]
        prev = int(data[1]["value"]) if len(data) > 1 else current
        return current, f"{classification} (prev {prev}, Δ {current - prev:+d})"
    except Exception as e:
        return None, f"error: {e}"


def fetch_reddit_sentiment(
    subreddits: Optional[List[str]] = None,
    posts_per_sub: int = 40,
) -> Tuple[Optional[int], int, List[Tuple[str, float]]]:
    """Reddit VADER sentiment over hot posts filtrados por BTC/Bitcoin.

    Usa JSON público (no PRAW, no auth required).
    """
    if subreddits is None:
        subreddits = ["CryptoMarkets", "Bitcoin", "CryptoCurrency"]

    scores: List[float] = []
    items: List[Tuple[str, float]] = []

    for sub in subreddits:
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit={posts_per_sub}"
        try:
            r = requests.get(url, headers=_UA, timeout=15)
            if r.status_code != 200:
                continue
            for child in r.json().get("data", {}).get("children", []):
                d = child.get("data", {})
                title = d.get("title", "") or ""
                selftext = d.get("selftext", "") or ""
                text = f"{title}. {selftext}"
                if not _BTC_PATTERN.search(text):
                    continue
                s = _analyzer.polarity_scores(text)["compound"]
                scores.append(s)
                items.append((title[:100], s))
        except Exception:
            continue

    if not scores:
        return None, 0, []

    avg = sum(scores) / len(scores)
    top = sorted(items, key=lambda x: abs(x[1]), reverse=True)[:5]
    return _vader_to_100(avg), len(scores), top


def fetch_news_sentiment() -> Tuple[Optional[int], int, List[Tuple[str, float]]]:
    """News RSS VADER sentiment (CoinTelegraph, CoinDesk, Decrypt)."""
    feeds = [
        "https://cointelegraph.com/rss/tag/bitcoin",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://decrypt.co/feed",
    ]
    scores: List[float] = []
    items: List[Tuple[str, float]] = []

    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:30]:
                title = entry.get("title", "") or ""
                summary = entry.get("summary", "") or ""
                # Limpieza mínima de HTML
                summary_clean = re.sub(r"<[^>]+>", " ", summary)
                text = f"{title}. {summary_clean}"
                if not _BTC_PATTERN.search(text):
                    continue
                s = _analyzer.polarity_scores(text)["compound"]
                scores.append(s)
                items.append((title[:100], s))
        except Exception:
            continue

    if not scores:
        return None, 0, []

    avg = sum(scores) / len(scores)
    top = sorted(items, key=lambda x: abs(x[1]), reverse=True)[:5]
    return _vader_to_100(avg), len(scores), top


def fetch_funding_sentiment() -> Tuple[Optional[int], str]:
    """Funding rate como proxy de posicionamiento (no es sentiment textual pero correlaciona).

    Funding negativo sostenido = shorts pagan = setup short squeeze (bullish contrarian).
    Funding muy positivo = longs pagan = riesgo long squeeze (bearish contrarian).
    Mapeo: funding 0 = 50, funding -0.05% = 80 (bullish contrarian), funding +0.05% = 20.
    """
    try:
        r = requests.get(
            "https://www.okx.com/api/v5/public/funding-rate",
            params={"instId": "BTC-USDT-SWAP"},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json().get("data", [])
        if not data:
            return None, "no data"
        fr = float(data[0]["fundingRate"])
        fr_pct = fr * 100
        # Mapeo contrarian: funding negativo → bullish sentiment score
        # clamp [-0.05%, +0.05%] → [80, 20]
        score = 50 - (fr_pct / 0.05) * 30
        score = max(0, min(100, round(score)))
        return score, f"funding {fr_pct:+.4f}% → contrarian score"
    except Exception as e:
        return None, f"error: {e}"
