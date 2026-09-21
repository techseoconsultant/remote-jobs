# Stock Decision Tool: Momentum Shadow Logger

Implements "SOP Momentum Continuation Entry v2.0" as a shadow logger. There is no order code in this repository. Nothing here can place a trade.

Pre-registration: "Pre-Registration Momentum Shadow Test.md" (SHA-256 8b5aad35052561740314740ee6d5cf5e2db743ec630b6a3d9509bc4ed648f513). The parameters in config.json are frozen for the 60-day window. Do not tune them.

## What it does each trading day

1. 09:25 ET: screens all US single stocks for gap-ups (SOP Step 1) and logs the list.
2. 09:35 ET: re-checks gaps against the actual open, reads the SPY gate, logs the universe.
3. 09:35 to 10:30 ET: on each completed 5-minute bar, evaluates the SOP trigger (three rising closes, new session high, above VWAP, rvol at least 2). Logs every trigger; opens a shadow position for up to 5 concurrent names.
4. 09:58 ET: asks Jev (typesafe-ai/jev via the Vercel AI Gateway) for a 0 to 100 continuation score and a close-up probability per candidate, in one batch. Logged, never acted on.
5. Until 15:55 ET: manages shadow exits with a 2.5 ATR trailing stop on 5-minute closes; flattens at 15:55.
6. After the close plus 16 minutes: `score.py` computes fills (next bar open) and net returns at 20 bps a side, writes outcomes.csv and summary.json.
7. Filters logged per candidate: F1 options open interest (Alpaca chain), F4 headline count (Benzinga). F2 squeeze and F3 gamma are placeholders in v1.

## Running

```
export ALPACA_API_KEY=...        # account with Algo Trader Plus data
export ALPACA_SECRET_KEY=...
export AI_GATEWAY_API_KEY=...    # Vercel AI Gateway
npm install                      # once, for the Jev sidecar
python3 src/runner.py            # live, run during the session
python3 src/score.py 2026-09-22  # after the close
python3 src/runner.py --replay 2026-09-18   # replay a past day
```

Logs land in `data/YYYY-MM-DD/` as CSV. The runner commits and pushes every 15 minutes if a git remote is configured, and never crashes on push failure.

## Design notes

- Bars are fetched with an end one minute before the boundary so a forming bar can never leak into a decision (no lookahead).
- Replay mode screens from historical daily bars, so replays are reproducible.
- Jev receives numeric state plus headlines under a field named headlines_untrusted with an instruction that they are data, not instructions.
- Scoring is idempotent per day and matches exit bars by timestamp.
- Zero-trade days are normal. The backtest rate is about 0 to 3 entries a day.
