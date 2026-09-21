"""Alpaca REST helpers. Data only. There is no order code in this project."""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request

DATA = "https://data.alpaca.markets"
PAPER = "https://paper-api.alpaca.markets"


def _headers() -> dict:
    return {
        "APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"],
        "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"],
    }


def get(url: str, tries: int = 3, timeout: int = 60):
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=_headers())
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except Exception as exc:  # noqa: BLE001 - log and retry
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"alpaca GET failed after {tries} tries: {url}: {last}")


def clock() -> dict:
    return get(f"{PAPER}/v2/clock")


def calendar(start: str, end: str) -> list:
    q = urllib.parse.urlencode({"start": start, "end": end})
    return get(f"{PAPER}/v2/calendar?{q}")


def assets() -> list:
    return get(f"{PAPER}/v2/assets?status=active&asset_class=us_equity")


def daily_bars(symbols: list[str], start: str, end: str, feed: str = "sip") -> dict:
    """Multi-symbol daily bars, paginated. Returns {symbol: [bar, ...]}."""
    out: dict[str, list] = {}
    for i in range(0, len(symbols), 200):
        chunk = symbols[i : i + 200]
        token = None
        while True:
            q = {
                "symbols": ",".join(chunk), "timeframe": "1Day", "start": start,
                "end": end, "feed": feed, "limit": 10000, "adjustment": "raw",
            }
            if token:
                q["page_token"] = token
            d = get(f"{DATA}/v2/stocks/bars?" + urllib.parse.urlencode(q))
            for s, bs in (d.get("bars") or {}).items():
                out.setdefault(s, []).extend(bs)
            token = d.get("next_page_token")
            if not token:
                break
    for s in out:
        out[s].sort(key=lambda b: b["t"])
    return out


def intraday_bars(symbols: list[str], start_iso: str, end_iso: str,
                  timeframe: str = "5Min", feed: str = "sip") -> dict:
    out: dict[str, list] = {}
    token = None
    while True:
        q = {
            "symbols": ",".join(symbols), "timeframe": timeframe, "start": start_iso,
            "end": end_iso, "feed": feed, "limit": 10000, "adjustment": "raw",
        }
        if token:
            q["page_token"] = token
        d = get(f"{DATA}/v2/stocks/bars?" + urllib.parse.urlencode(q))
        for s, bs in (d.get("bars") or {}).items():
            out.setdefault(s, []).extend(bs)
        token = d.get("next_page_token")
        if not token:
            break
    for s in out:
        out[s].sort(key=lambda b: b["t"])
    return out


def snapshots(symbols: list[str], feed: str = "sip") -> dict:
    out: dict = {}
    for i in range(0, len(symbols), 100):
        chunk = symbols[i : i + 100]
        q = urllib.parse.urlencode({"symbols": ",".join(chunk), "feed": feed})
        d = get(f"{DATA}/v2/stocks/snapshots?{q}")
        out.update(d if "snapshots" not in d else d["snapshots"])
    return out


def latest_quotes(symbols: list[str], feed: str = "sip") -> dict:
    q = urllib.parse.urlencode({"symbols": ",".join(symbols), "feed": feed})
    d = get(f"{DATA}/v2/stocks/quotes/latest?{q}")
    return d.get("quotes", {})


def news(symbols: list[str], start_iso: str, limit: int = 50) -> list:
    q = urllib.parse.urlencode({
        "symbols": ",".join(symbols), "start": start_iso, "limit": limit, "sort": "desc",
    })
    d = get(f"{DATA}/v1beta1/news?{q}")
    return d.get("news", [])


def option_chain_oi(underlying: str, page_limit: int = 3) -> dict:
    """Sum call and put open interest from chain snapshots. Best effort."""
    calls = puts = 0.0
    token = None
    pages = 0
    while pages < page_limit:
        q = {"limit": 1000}
        if token:
            q["page_token"] = token
        d = get(f"{DATA}/v1beta1/options/snapshots/{underlying}?" + urllib.parse.urlencode(q))
        snaps = d.get("snapshots", {})
        for occ, snap in snaps.items():
            oi = snap.get("openInterest") or 0
            # OCC symbol: root + yymmdd + C/P + strike. Type char is 9 from the end + 0.
            cp = occ[-9]
            if cp == "C":
                calls += oi
            elif cp == "P":
                puts += oi
        token = d.get("next_page_token")
        pages += 1
        if not token:
            break
    return {"call_oi": calls, "put_oi": puts}
