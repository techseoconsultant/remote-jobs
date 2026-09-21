# Pre-Registration: Momentum Continuation Shadow Test

Version 1.0. Written 2026-09-21, before the first logged session. This file is frozen. Its SHA-256 hash is quoted in the session log and in the repository history. Any change to this file or to the SOP parameters restarts the clock.

## What is being tested

SOP Momentum Continuation Entry v2.0, exactly as written in "SOP Momentum Continuation Entry.md" at the commit that accompanies this file. No parameter may be tuned during the test window.

## Window

60 consecutive trading days from the first logged session. The exchange calendar defines trading days. Early-close sessions count if the first hour completed.

## Universe and cadence

The SOP's screen and trigger, verbatim: gap-up single stocks, top 30 by gap size, entries only between 09:35 and 10:30 exchange time, one entry per name per day.

## Shadow fills and costs

Entry and exit at the open of the next 5-minute bar after the signal, on consolidated (SIP) bars fetched at least 16 minutes after the fact. Cost: 20 basis points per side. No orders are placed. There is no order code in the system.

## Primary endpoint

After-cost mean return per taken trade, with a 90 percent confidence interval clustered by trading day. Pass requires the interval's lower bound above zero at day 60. Nothing else can trigger a pass.

## Secondary endpoints (Holm-corrected, reported, never a pass on their own)

1. Trimmed mean (top and bottom 2 percent removed) and median per trade.
2. Share of positive days.
3. For each staged filter (F1 options positioning, F2 squeeze fuel, F3 gamma regime, F4 catalyst) and for Jev's 0 to 100 score: the daily cross-sectional Spearman correlation between the filter value and the SPY-excess return from trigger to close, averaged over days and tested at the day level, and the after-cost lift of the top half versus bottom half of triggers.
4. Jev must also beat a walk-forward logistic regression fit on gap size, relative volume, the 09:30-to-10:00 return, and distance from VWAP. Beating zero is not enough.

## Validity rules

- A session with a data gap in more than 10 percent of candidate bars is voided, counted, and reported.
- Late or failed decisions carry a reason code and are excluded from endpoints, never scored as holds.
- Ex-dividend and split symbol-days are excluded from any next-day measure.
- The Jev model version is logged per answer; a version change is reported and splits the sample.

## Stopping rules

- Futility stop only. If at day 30 the primary interval's upper bound is below zero, the test may stop early as a fail.
- No early success stop. No parameter change mid-window. No adding capital mid-window.

## Expected outcome

Fail. The out-of-sample evidence behind the rule is 34 trades with a day-level t near 1, and the published base rates are against it. The test exists to measure, not to confirm.

## Commitment

No live capital, no size change, and no STOCK-Auto lane before the window completes and the owner approves the next step in his own words, in writing, with an amount.
