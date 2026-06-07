"""
api.py

FastAPI backend that serves articles from MongoDB to the frontend.

Usage:
    cd src/
    uvicorn api:app --reload --port 8000
"""

import json
import os
import re
import time
from datetime import datetime, timezone

import yfinance as yf
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient


app = FastAPI(title="Australian Market Intelligence API")

# Allow the frontend (any origin) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

from dotenv import load_dotenv
load_dotenv()

client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
collection = client["australian_market_intelligence"]["articles"]


# Category fallback images (high-quality Unsplash photos, stable IDs)
CATEGORY_FALLBACK_IMAGES = {
    "Technology":     "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1200&h=400&fit=crop&auto=format",
    "Funding":        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200&h=400&fit=crop&auto=format",
    "Energy":         "https://images.unsplash.com/photo-1509391366360-2e959784a276?w=1200&h=400&fit=crop&auto=format",
    "Retail":         "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=1200&h=400&fit=crop&auto=format",
    "Property":       "https://images.unsplash.com/photo-1486325212027-8081e485255e?w=1200&h=400&fit=crop&auto=format",
    "Policy_Economy": "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=1200&h=400&fit=crop&auto=format",
}
DEFAULT_FALLBACK = "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1200&h=400&fit=crop&auto=format"


# Maps category_requested values to frontend display values
CATEGORY_MAP = {
    "Technology":     {"key": "technology", "label": "Technology",       "dot": "dot-tech"},

    "Energy":         {"key": "energy",     "label": "Energy",           "dot": "dot-energy"},
    "Retail":         {"key": "retail",     "label": "Retail",           "dot": "dot-retail"},
    "Property":       {"key": "property",   "label": "Property",         "dot": "dot-property"},
    "Policy_Economy": {"key": "policy",     "label": "Policy & Economy", "dot": "dot-policy"},
}


def time_ago(date_str: str) -> str:
    """Convert a published_date string into a human-readable 'Xd ago' string."""
    if not date_str or date_str == "nan":
        return "Recently"
    try:
        for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"]:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                break
            except ValueError:
                continue
        else:
            return "Recently"

        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        diff = now - dt
        days = diff.days
        hours = diff.seconds // 3600

        if days == 0:
            return f"{hours}h ago" if hours > 0 else "Just now"
        elif days == 1:
            return "1d ago"
        else:
            return f"{days}d ago"
    except Exception:
        return "Recently"


def parse_json_list(value) -> list:
    """Safely parse a JSON-encoded list field from MongoDB."""
    if not value or str(value).strip() in ("nan", "[]", "", "None"):
        return []
    try:
        parsed = json.loads(str(value))
        if isinstance(parsed, list):
            return [str(x).strip() for x in parsed if x and str(x).strip()]
        return []
    except Exception:
        return []


def first_money_amount(value) -> str:
    """Return the first money amount from a JSON list, or N/A."""
    amounts = parse_json_list(value)
    return amounts[0] if amounts else "N/A"


def format_location(value) -> str:
    """Return the first two real-looking locations joined by a comma."""
    locs = parse_json_list(value)
    # Filter out things that are clearly not locations (e.g. "AI", "nan")
    skip = {"AI", "nan", "None", ""}
    real = [l for l in locs if l not in skip and len(l) > 2]
    return ", ".join(real[:2]) if real else "Australia"


def build_tags(doc: dict) -> list:
    """Build a short tag list from event_type, category, and top organisations."""
    tags = []

    event_type = str(doc.get("event_type", "")).strip()
    if event_type and event_type != "nan":
        tags.append(event_type)

    category = str(doc.get("category_requested", "")).strip()
    if category and category != "nan":
        tags.append(category.replace("_", " & "))

    orgs = parse_json_list(doc.get("organisations"))
    for org in orgs[:3]:
        if org not in tags:
            tags.append(org)

    return tags[:5]


def clean(value) -> str:
    """Return a clean string, replacing nan/None with empty string."""
    s = str(value).strip()
    return "" if s in ("nan", "None") else s


@app.get("/api/articles")
def get_articles():
    """Return all articles from MongoDB transformed for the frontend."""
    raw_docs = list(collection.find({}, {"_id": 0}))

    # Deduplicate by URL (keep first occurrence)
    seen_urls = set()
    unique_docs = []
    for doc in raw_docs:
        url = clean(doc.get("url", ""))
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_docs.append(doc)

    # Sort newest first by published_date
    def parse_date(doc):
        date_str = clean(doc.get("published_date", ""))
        for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"]:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except (ValueError, AttributeError):
                continue
        return datetime.min.replace(tzinfo=timezone.utc)

    unique_docs.sort(key=parse_date, reverse=True)

    articles = []
    for i, doc in enumerate(unique_docs):
        cat_raw = clean(doc.get("category_requested", "Technology"))
        cat = CATEGORY_MAP.get(cat_raw, CATEGORY_MAP["Technology"])

        sentiment = clean(doc.get("sentiment", "neutral")).lower()
        if sentiment not in ("positive", "negative", "neutral"):
            sentiment = "neutral"

        # Prefer polished_summary; fall back to raw summary
        summary = clean(doc.get("polished_summary", "")) or clean(doc.get("summary", ""))

        stock_symbol = clean(doc.get("stock_symbol", ""))

        # Always return a Clearbit logo URL — regenerate if stored URL is still the old placeholder
        raw_logo = clean(doc.get("company_logo_url", ""))
        if not raw_logo or "logo.dev" in raw_logo or "YOUR_API_KEY" in raw_logo:
            company_name = clean(doc.get("primary_company", ""))
            slug = re.sub(r"[^a-z0-9]+", "", company_name.lower())
            logo = f"https://logo.clearbit.com/{slug}.com" if slug else ""
        else:
            logo = raw_logo

        articles.append({
            "id":                   i + 1,
            "category":             cat["key"],
            "categoryLabel":        cat["label"],
            "dot":                  cat["dot"],
            "source":               clean(doc.get("source", "")),
            "timeAgo":              time_ago(clean(doc.get("published_date", ""))),
            "title":                clean(doc.get("title", "")),
            "summary":              summary,
            "company":              clean(doc.get("primary_company", "N/A")),
            "sector":               cat_raw.replace("_", " & "),
            "eventType":            clean(doc.get("event_type", "General")),
            "investmentAmount":     first_money_amount(doc.get("money_amounts")),
            "location":             format_location(doc.get("locations")),
            "sentiment":            sentiment,
            "relevanceScore":       int(float(doc.get("relevance_score", 3) or 3)),
            "keyInsight":           clean(doc.get("key_insight", "")),
            "whyItMatters":         clean(doc.get("strategic_importance", "")),
            "tags":                 build_tags(doc),
            "url":                  clean(doc.get("url", "")),
            # Company enrichment fields
            "logo":                 logo,
            "stockSymbol":          stock_symbol,
            "stockChartAvailable":  stock_symbol != "",
            # Hero image: company Wikipedia image → category fallback → default
            "heroImage": (
                clean(doc.get("company_hero_image_url", ""))
                or CATEGORY_FALLBACK_IMAGES.get(cat_raw, DEFAULT_FALLBACK)
            ),
            "companyWikipediaUrl": clean(doc.get("company_wikipedia_url", "")),
        })

    return articles


# ─────────────────────────────────────────────
# In-memory stock cache (15-minute TTL)
# ─────────────────────────────────────────────
_stock_cache: dict = {}
STOCK_CACHE_TTL = 900  # 15 minutes


@app.get("/api/stock/{symbol}")
def get_stock(symbol: str):
    """
    Fetch real-time stock data for a given ticker symbol via Yahoo Finance.
    Results are cached for 15 minutes to avoid rate limiting.

    Supports ASX tickers (e.g. MQG.AX, TLS.AX) and US tickers (MSFT, META, GOOGL).
    """
    now = time.time()

    # Return cached data if still fresh
    if symbol in _stock_cache:
        cached_data, cached_at = _stock_cache[symbol]
        if now - cached_at < STOCK_CACHE_TTL:
            return cached_data

    try:
        ticker = yf.Ticker(symbol)
        info   = ticker.info

        # Current price — yfinance field name varies by market
        price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("postMarketPrice")
        )

        prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
        change     = round(price - prev_close, 2) if price and prev_close else 0
        change_pct = round(change / prev_close * 100, 2) if prev_close else 0

        # 30-day daily close prices for sparkline
        hist   = ticker.history(period="30d", interval="1d")
        prices = [round(float(p), 2) for p in hist["Close"].tolist()] if not hist.empty else []
        dates  = [str(d.date()) for d in hist.index.tolist()]          if not hist.empty else []

        data = {
            "symbol":      symbol,
            "price":       round(price, 2) if price else None,
            "change":      change,
            "changePct":   change_pct,
            "currency":    info.get("currency", ""),
            "exchange":    info.get("exchange", ""),
            "companyName": info.get("shortName", ""),
            "marketCap":   info.get("marketCap"),
            "volume":      info.get("regularMarketVolume"),
            "prices":      prices,
            "dates":       dates,
            "error":       None,
        }

    except Exception as e:
        data = {
            "symbol": symbol, "price": None, "change": 0, "changePct": 0,
            "currency": "", "exchange": "", "companyName": "", "marketCap": None,
            "volume": None, "prices": [], "dates": [], "error": str(e),
        }

    _stock_cache[symbol] = (data, now)
    return data
