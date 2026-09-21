"""Pure indicator math on 5-minute bars. No I/O."""
from __future__ import annotations

import statistics as st


def vwap_series(bars: list[dict]) -> list[float]:
    pv = vv = 0.0
    out = []
    for b in bars:
        tp = (b["h"] + b["l"] + b["c"]) / 3
        pv += tp * b["v"]
        vv += b["v"]
        out.append(pv / vv if vv else b["c"])
    return out


def atr_at(bars: list[dict], i: int, window: int) -> float:
    lo = max(0, i - window + 1)
    trs = []
    for j in range(lo, i + 1):
        if j == 0:
            trs.append(bars[0]["h"] - bars[0]["l"])
        else:
            pc = bars[j - 1]["c"]
            trs.append(max(bars[j]["h"] - bars[j]["l"], abs(bars[j]["h"] - pc), abs(bars[j]["l"] - pc)))
    return sum(trs) / len(trs)


def rvol_at(bars: list[dict], i: int, run: int, lookback: int) -> float:
    prior = [b["v"] for b in bars[max(0, i - lookback) : i - run + 1]]
    med = st.median(prior) if prior else 0
    if med <= 0:
        return 0.0
    recent = sum(b["v"] for b in bars[i - run + 1 : i + 1])
    return recent / (run * med)


def triggered(bars: list[dict], i: int, cfg: dict) -> dict | None:
    """SOP v2.0 Step 4 on completed bar i. Returns feature dict or None."""
    t = cfg["trigger"]
    r = t["rising_closes"]
    if i < max(r, 3):
        return None
    closes = [b["c"] for b in bars[: i + 1]]
    for k in range(r):
        if not closes[i - k] > closes[i - k - 1]:
            return None
    vw = vwap_series(bars[: i + 1])
    if t["require_above_vwap"] and not closes[i] > vw[i]:
        return None
    if t["require_new_session_high"] and not closes[i] >= max(closes):
        return None
    rv = rvol_at(bars, i, r, t["rvol_lookback_bars"])
    if rv < t["rvol_min"]:
        return None
    return {
        "close": closes[i],
        "vwap": round(vw[i], 4),
        "rvol": round(rv, 2),
        "atr": round(atr_at(bars, i, cfg["exit"]["atr_bars"]), 4),
        "session_high": max(closes),
        "run_pct": round((closes[i] / closes[i - r] - 1) * 100, 3),
    }
