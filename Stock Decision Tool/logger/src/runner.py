"""Shadow logger for SOP Momentum Continuation Entry v2.0.

Live mode: run during a session; loops on 5-minute boundaries.
Replay mode: --replay YYYY-MM-DD reruns a past session from history.

There is NO order code in this project. Every position is a shadow row.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(__file__))
import alpaca  # noqa: E402
import indicators as ind  # noqa: E402

ET = ZoneInfo("America/New_York")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "config.json")))

FUND_PAT = re.compile(
    r"(\bETF\b|\bETN\b|\bFund\b|\b[123](\.5)?X\b|\b[123]x\b|-1X|\bBull\b|\bBear\b|Leveraged"
    r"|Leverage Shares|Inverse|Daily Target|ProShares|Direxion|GraniteShares|T-REX|T-Rex"
    r"|Defiance|YieldMax|Roundhill|Tradr|Kurv|\bUltra\b|Volatility|Futures|Bitcoin|Ether\b"
    r"|Ethereum|Solana|iShares|SPDR|Vanguard|Invesco|WisdomTree|VanEck|Global X)", re.I)


def log_path(day: str, name: str) -> str:
    d = os.path.join(ROOT, "data", day)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name)


def append_row(day: str, name: str, row: dict) -> None:
    path = log_path(day, name)
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)


def git_push_best_effort(day: str, msg: str) -> None:
    try:
        subprocess.run(["git", "add", "-A"], cwd=ROOT, check=False, capture_output=True)
        subprocess.run(["git", "-c", "user.name=sdt-logger", "-c", "user.email=logger@local",
                        "commit", "-q", "-m", msg], cwd=ROOT, check=False, capture_output=True)
        subprocess.run(["git", "push", "-q"], cwd=ROOT, check=False, capture_output=True, timeout=60)
    except Exception:
        pass  # logging must never die on push failure


def screen(day: str, prior_day: str, name_by_symbol: dict, replay: bool = False) -> list[dict]:
    """SOP Step 1. Gap vs prior close using premarket/last trade, refined at open."""
    u = CFG["universe"]
    symbols = [s for s in name_by_symbol if s.isalpha() and len(s) <= 5]
    start = (dt.date.fromisoformat(prior_day) - dt.timedelta(days=45)).isoformat()
    dailies = alpaca.daily_bars(symbols, start, prior_day)
    candidates = []
    for s, bars in dailies.items():
        if len(bars) < u["adv_lookback_days"] + 1:
            continue
        if bars[-1]["t"][:10] != prior_day:
            continue
        prior_close = bars[-1]["c"]
        if not u["min_prior_close"] <= prior_close <= u["max_prior_close"]:
            continue
        adv = sum(b["c"] * b["v"] for b in bars[-u["adv_lookback_days"]:]) / u["adv_lookback_days"]
        if adv < u["min_adv_usd"]:
            continue
        if FUND_PAT.search(name_by_symbol.get(s, "")):
            continue
        candidates.append({"symbol": s, "prior_close": prior_close, "adv_usd": round(adv)})
    out = []
    if replay:
        opens = alpaca.daily_bars([c["symbol"] for c in candidates], day, day)
        for c in candidates:
            bs = opens.get(c["symbol"]) or []
            if not bs or bs[-1]["t"][:10] != day:
                continue
            gap = bs[-1]["o"] / c["prior_close"] - 1
            if gap * 100 >= u["min_gap_pct"]:
                c["premarket_gap_pct"] = round(gap * 100, 2)
                out.append(c)
    else:
        snaps = alpaca.snapshots([c["symbol"] for c in candidates])
        for c in candidates:
            snap = snaps.get(c["symbol"]) or {}
            px = ((snap.get("latestTrade") or {}).get("p")
                  or (snap.get("minuteBar") or {}).get("c")
                  or (snap.get("dailyBar") or {}).get("o"))
            if not px:
                continue
            gap = px / c["prior_close"] - 1
            if gap * 100 >= u["min_gap_pct"]:
                c["premarket_gap_pct"] = round(gap * 100, 2)
                out.append(c)
    out.sort(key=lambda c: -c["premarket_gap_pct"])
    return out[: u["top_n_by_gap"]]


def refine_universe_at_open(day: str, cands: list[dict]) -> list[dict]:
    """Re-check the actual session open against the prior close (SOP gap definition)."""
    if not cands:
        return []
    o, _ = session_utc(day)
    bars = alpaca.intraday_bars([c["symbol"] for c in cands], o, add_minutes(o, 6))
    kept = []
    for c in cands:
        bs = bars.get(c["symbol"]) or []
        if not bs:
            continue
        gap = bs[0]["o"] / c["prior_close"] - 1
        c["open_gap_pct"] = round(gap * 100, 2)
        if gap * 100 >= CFG["universe"]["min_gap_pct"]:
            kept.append(c)
    return kept


def session_utc(day: str) -> tuple[str, str]:
    d = dt.date.fromisoformat(day)
    o = dt.datetime(d.year, d.month, d.day, 9, 30, tzinfo=ET).astimezone(dt.timezone.utc)
    c = dt.datetime(d.year, d.month, d.day, 16, 0, tzinfo=ET).astimezone(dt.timezone.utc)
    return o.strftime("%Y-%m-%dT%H:%M:%SZ"), c.strftime("%Y-%m-%dT%H:%M:%SZ")


def add_minutes(iso: str, minutes: int) -> str:
    t = dt.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    return (t + dt.timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


def spy_gate(day: str, prior_day: str) -> tuple[bool, float]:
    d = alpaca.daily_bars(["SPY"], prior_day, prior_day)
    prior_close = d["SPY"][-1]["c"]
    snap = alpaca.snapshots(["SPY"])
    px = ((snap.get("SPY") or {}).get("latestTrade") or {}).get("p") or prior_close
    chg = (px / prior_close - 1) * 100
    return chg <= CFG["session"]["spy_gate_drop_pct"], round(chg, 2)


def jev_score(day: str, cands: list[dict], bars_by_sym: dict, headlines: dict) -> dict:
    """Call the Jev sidecar once per candidate batch. Best effort, logged either way."""
    if not CFG["jev"]["enabled"] or not os.environ.get("AI_GATEWAY_API_KEY"):
        return {}
    payload = []
    for c in cands:
        s = c["symbol"]
        bs = bars_by_sym.get(s) or []
        closes = [b["c"] for b in bs][-12:]
        vw = ind.vwap_series(bs)[-1] if bs else None
        payload.append({
            "symbol": s, "gap_pct": c.get("open_gap_pct", c.get("premarket_gap_pct")),
            "closes_5min": closes, "vwap": vw,
            "headlines_untrusted": [h[:180] for h in headlines.get(s, [])[:5]],
        })
    try:
        proc = subprocess.run(
            ["node", os.path.join(ROOT, "jev", "jev.mjs")],
            input=json.dumps({"candidates": payload, "model": CFG["jev"]["model"]}),
            capture_output=True, text=True, timeout=90,
        )
        out = json.loads(proc.stdout or "{}")
    except Exception as exc:  # noqa: BLE001
        out = {"error": str(exc)[:200]}
    append_row(day, "jev.csv", {"ts": now_iso(), "raw": json.dumps(out)[:8000]})
    return out.get("scores", {}) if isinstance(out, dict) else {}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_day(day: str, replay: bool) -> None:
    cal = alpaca.calendar((dt.date.fromisoformat(day) - dt.timedelta(days=10)).isoformat(), day)
    days = [c["date"] for c in cal]
    if day not in days:
        print(f"{day} is not a trading day; exiting")
        return
    prior_day = days[days.index(day) - 1]
    open_utc, close_utc = session_utc(day)
    s_cfg = CFG["session"]

    name_by_symbol = {a["symbol"]: a.get("name", "") for a in alpaca.assets()
                      if a.get("tradable") and a.get("exchange") in ("NYSE", "NASDAQ", "ARCA", "AMEX", "BATS")}

    if not replay:
        wait_until(add_minutes(open_utc, -s_cfg["screen_minutes_before_open"]))
    cands = screen(day, prior_day, name_by_symbol, replay=replay)
    append_row(day, "screen.csv", {"ts": now_iso(), "n": len(cands),
                                   "symbols": " ".join(c["symbol"] for c in cands)})
    gate_hit, spy_chg = (False, 0.0)
    if not replay:
        wait_until(add_minutes(open_utc, 5))
        gate_hit, spy_chg = spy_gate(day, prior_day)
    else:
        spy_bars = alpaca.intraday_bars(["SPY"], open_utc, add_minutes(open_utc, 6))
        pd_close = alpaca.daily_bars(["SPY"], prior_day, prior_day)["SPY"][-1]["c"]
        if spy_bars.get("SPY"):
            spy_chg = round((spy_bars["SPY"][0]["o"] / pd_close - 1) * 100, 2)
            gate_hit = spy_chg <= s_cfg["spy_gate_drop_pct"]
    cands = refine_universe_at_open(day, cands)
    append_row(day, "universe.csv", {"ts": now_iso(), "spy_gate_hit": gate_hit, "spy_chg_pct": spy_chg,
                                     "n": len(cands), "symbols": " ".join(c["symbol"] for c in cands)})
    if gate_hit:
        print("SPY gate hit; logging triggers but marking gate_blocked")

    symbols = [c["symbol"] for c in cands]
    f_extra = collect_filters(day, prior_day, symbols)
    positions: dict[str, dict] = {}
    entered: set[str] = set()
    jev_scores: dict = {}
    jev_done = False
    end_min = 390  # minutes after open the loop covers
    step = CFG["bar_minutes"]

    for m in range(step, end_min + step, step):
        bar_end = add_minutes(open_utc, m)
        if not replay:
            wait_until(add_minutes(bar_end, 1))  # let the bar publish
        if not jev_done and m >= CFG["jev"]["ask_minutes_after_open"]:
            bars_now = alpaca.intraday_bars(symbols, open_utc, add_minutes(bar_end, -1)) if symbols else {}
            jev_scores = jev_score(day, cands, bars_now, f_extra.get("headlines", {}))
            jev_done = True
        bars_now = alpaca.intraday_bars(symbols + ["SPY"], open_utc, add_minutes(bar_end, -1)) if symbols else {}
        process_bar(day, m, bar_end, cands, bars_now, positions, entered,
                    jev_scores, f_extra, gate_hit)
        if not replay and m % 15 == 0:
            git_push_best_effort(day, f"log {day} +{m}m")
        if replay and m > 390:
            break
    # session end: flatten what remains at the last bar close
    for s, p in list(positions.items()):
        close_shadow(day, s, p, p.get("last_close"), "session_end", close_utc)
        positions.pop(s, None)
    git_push_best_effort(day, f"log {day} session complete")
    print(f"day {day} complete: {len(entered)} shadow entries")
    if not replay:
        wait_until(add_minutes(close_utc, 16))  # SIP embargo, then self-score
        subprocess.run([sys.executable, os.path.join(ROOT, "src", "score.py"), day], check=False)
        git_push_best_effort(day, f"score {day}")


def collect_filters(day: str, prior_day: str, symbols: list[str]) -> dict:
    out: dict = {"headlines": {}, "oi": {}}
    start_iso = f"{prior_day}T20:00:00Z"
    try:
        for n in alpaca.news(symbols, start_iso, limit=50) if symbols else []:
            for s in n.get("symbols", []):
                if s in symbols:
                    out["headlines"].setdefault(s, []).append(n.get("headline", ""))
    except Exception as exc:  # noqa: BLE001
        out["headlines_error"] = str(exc)[:120]
    for s in symbols[:30]:
        try:
            out["oi"][s] = alpaca.option_chain_oi(s, page_limit=2)
        except Exception:
            out["oi"][s] = None
    for s in symbols:
        append_row(day, "filters.csv", {
            "ts": now_iso(), "symbol": s,
            "f1_call_oi": (out["oi"].get(s) or {}).get("call_oi") if out["oi"].get(s) else "",
            "f1_put_oi": (out["oi"].get(s) or {}).get("put_oi") if out["oi"].get(s) else "",
            "f2_squeeze": "not_collected_v1",
            "f3_gamma": "not_collected_v1",
            "f4_headline_count": len(out["headlines"].get(s, [])),
        })
    return out


def process_bar(day, m, bar_end, cands, bars_by_sym, positions, entered,
                jev_scores, f_extra, gate_hit) -> None:
    s_cfg, x_cfg = CFG["session"], CFG["exit"]
    in_entry_window = s_cfg["entry_window_start_min_after_open"] <= m <= s_cfg["entry_window_end_min_after_open"]
    flatten_after = 390 - s_cfg["flatten_minutes_before_close"]
    for c in cands:
        s = c["symbol"]
        bs = bars_by_sym.get(s) or []
        if len(bs) < 2:
            continue
        i = len(bs) - 1
        # manage open shadow position on the just-completed bar
        if s in positions:
            p = positions[s]
            p["high_close"] = max(p["high_close"], bs[i]["c"])
            p["last_close"] = bs[i]["c"]
            stop = p["high_close"] - x_cfg["trail_atr_mult"] * ind.atr_at(bs, i, x_cfg["atr_bars"])
            if bs[i]["c"] < stop:
                close_shadow(day, s, p, bs[i]["c"], "trail_stop_signal", bar_end)
                positions.pop(s, None)
            elif m >= flatten_after:
                close_shadow(day, s, p, bs[i]["c"], "eod_flatten", bar_end)
                positions.pop(s, None)
            continue
        # look for a new trigger
        if not in_entry_window or s in entered:
            continue
        feat = ind.triggered(bs, i, CFG)
        if not feat:
            continue
        row = {
            "ts": now_iso(), "day": day, "symbol": s, "minutes_after_open": m,
            "bar_end_utc": bar_end, **feat,
            "gap_pct": c.get("open_gap_pct"), "jev_score": jev_scores.get(s, ""),
            "f4_headlines": len((f_extra.get("headlines") or {}).get(s, [])),
            "gate_blocked": gate_hit,
            "taken": (not gate_hit) and len(positions) < CFG["shadow"]["max_concurrent"],
        }
        append_row(day, "triggers.csv", row)
        entered.add(s)
        if row["taken"]:
            positions[s] = {
                "symbol": s, "signal_bar_end": bar_end, "signal_close": feat["close"],
                "high_close": feat["close"], "last_close": feat["close"],
                "entry_pending_bar": add_minutes(bar_end, CFG["bar_minutes"]),
            }
            append_row(day, "shadow_entries.csv", {**row, "entry_fill_rule": "next_bar_open"})


def close_shadow(day, s, p, exit_signal_close, reason, exit_bar_end="") -> None:
    append_row(day, "shadow_exits.csv", {
        "ts": now_iso(), "day": day, "symbol": s,
        "signal_bar_end": p["signal_bar_end"], "signal_close": p["signal_close"],
        "high_close": p["high_close"], "exit_signal_close": exit_signal_close,
        "exit_bar_end": exit_bar_end,
        "exit_fill_rule": "next_bar_open", "reason": reason,
    })


def wait_until(iso_utc: str) -> None:
    target = dt.datetime.strptime(iso_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    while True:
        delta = (target - dt.datetime.now(dt.timezone.utc)).total_seconds()
        if delta <= 0:
            return
        time.sleep(min(delta, 30))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", help="YYYY-MM-DD past session to replay")
    args = ap.parse_args()
    if args.replay:
        run_day(args.replay, replay=True)
    else:
        c = alpaca.clock()
        today = dt.datetime.now(ET).strftime("%Y-%m-%d")
        run_day(today, replay=False)


if __name__ == "__main__":
    main()
