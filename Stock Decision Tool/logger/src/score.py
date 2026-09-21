"""Score a logged day after the 15-minute embargo. Idempotent per (day, symbol).

Fills: entry at the open of the bar after the signal bar; exit at the open of the
bar after the exit-signal bar (or that bar's close at session end). Costs from
config. Writes outcomes.csv and a one-line summary.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(__file__))
import alpaca  # noqa: E402
from runner import CFG, ROOT, add_minutes, log_path, session_utc  # noqa: E402


def read_csv(day: str, name: str) -> list[dict]:
    path = log_path(day, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def bar_open_at(bars: list[dict], iso: str) -> float | None:
    for b in bars:
        if b["t"] == iso:
            return b["o"]
    return None


def score(day: str) -> None:
    entries = read_csv(day, "shadow_entries.csv")
    exits = {(r["day"], r["symbol"]): r for r in read_csv(day, "shadow_exits.csv")}
    if not entries:
        print(f"{day}: no shadow entries to score")
        return
    open_utc, close_utc = session_utc(day)
    symbols = sorted({e["symbol"] for e in entries})
    bars = alpaca.intraday_bars(symbols, open_utc, close_utc)
    cost = CFG["shadow"]["cost_bps_per_side"] / 10000.0
    rows, rets = [], []
    for e in entries:
        s = e["symbol"]
        bs = bars.get(s) or []
        entry_bar = add_minutes(e["bar_end_utc"], 0)  # signal bar END == next bar START
        ep = bar_open_at(bs, entry_bar)
        x = exits.get((day, s))
        if ep is None or x is None:
            rows.append({"day": day, "symbol": s, "status": "unscored_missing_data"})
            continue
        # exit fill: open of the bar that starts at the exit-signal bar's end;
        # fall back to price match, then to the last close.
        exit_signal_close = float(x["exit_signal_close"])
        xp = None
        if x.get("exit_bar_end"):
            xp = bar_open_at(bs, x["exit_bar_end"])
        if xp is None:
            for j, b in enumerate(bs):
                if abs(b["c"] - exit_signal_close) < 1e-9 and b["t"] >= entry_bar:
                    xp = bs[j + 1]["o"] if j + 1 < len(bs) else b["c"]
                    break
        if xp is None:
            xp = bs[-1]["c"]
        net = (xp / ep - 1) - 2 * cost
        rets.append(net)
        rows.append({"day": day, "symbol": s, "status": "scored", "entry_px": ep,
                     "exit_px": xp, "exit_reason": x["reason"],
                     "net_ret_bps": round(net * 1e4, 1),
                     "jev_score": e.get("jev_score", ""),
                     "gap_pct": e.get("gap_pct", ""), "rvol": e.get("rvol", "")})
    path = log_path(day, "outcomes.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=sorted({k for r in rows for k in r}))
        w.writeheader()
        w.writerows(rows)
    summary = {
        "day": day, "trades": len(rets),
        "mean_bps": round(st.mean(rets) * 1e4, 1) if rets else None,
        "median_bps": round(st.median(rets) * 1e4, 1) if rets else None,
        "sum_bps": round(sum(rets) * 1e4, 1) if rets else None,
        "win_rate": round(sum(1 for r in rets if r > 0) / len(rets), 3) if rets else None,
        "cost_bps_per_side": CFG["shadow"]["cost_bps_per_side"],
    }
    with open(log_path(day, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary))


if __name__ == "__main__":
    score(sys.argv[1] if len(sys.argv) > 1 else dt.date.today().isoformat())
