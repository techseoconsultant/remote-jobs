# SOP: Momentum Continuation Entry (v2.0 draft for QA)

Date: 2026-09-21. Author: Claude, for Micah. Status: DRAFT. Not approved. No live money. This SOP replaces the raw rule "it starts going up and keeps going up for a few minutes, so I buy." It was built from the 24 documents in New Research Sep 20th plus tests on 166 sessions of consolidated market data. Micah QAs this document, then approves or rejects it in his own words.

## TLDR

- The raw rule fails. Across 27,197 out-of-sample triggers, a stock that rose for 15 minutes kept rising only 48.6 percent of the time. This is worse than a coin flip. The research agrees: small gaps fill 55 to 85 percent of the time, and breakout win rates sit at 52 to 53 percent.
- The fix is not more speed. The fix is selection, timing, and exit shape. Trade only gap-up single stocks. Enter only in the first hour. Require a new session high, price above VWAP, and double relative volume. Hold with a wide trailing stop so the rare big runner pays for the frequent small losers.
- The upgraded rule survived its first out-of-sample test but is NOT proven. On 145 unseen sessions it took 34 trades and kept a positive mean at every cost level, +110 basis points a trade even at 20 basis points a side. But the median trade loses, one trade supplied most of the profit, and the statistical confidence is low (t about 1). Expect losing weeks.
- Most of the research folder is marketing. Three findings are worth adding, in this order: a nightly call-put open interest ranking (the one published, cost-adjusted paper: 19 basis points a day), a short-squeeze fuel score (short interest, days to cover, borrow cost), and a dealer-gamma regime flag (momentum continues when dealers are short gamma). All three are testable with free or cheap data and are staged as filters to score, not to trust.
- Decision for you after QA: A (recommended) run this SOP in shadow for 60 trading days with the staged filters scored alongside; B run it with small live money after 20 clean shadow days, accepting that it is unproven; C reject it.

## 1. Purpose and scope

Give one exact, testable rule for buying intraday momentum on US single stocks, with entry, exit, sizing, and stop-trading conditions. Applies to the Stock Decision Tool only. Does not touch STOCK-Auto, its integrity lock, or its SOPs. Long only. No options positions. No overnight holds.

## 2. Definitions

- Gap-up: today's open at least 3 percent above yesterday's close.
- Single stock: not an ETF, ETN, fund, or leveraged product. Filter by asset name.
- Session bars: 5-minute consolidated (SIP) bars, regular hours only, timestamps from the exchange calendar (handles DST).
- VWAP: volume weighted average price from the session open.
- Relative volume (rvol): volume of the last 3 bars divided by 3 times the median bar volume of the prior 20 bars.
- ATR: average true range over the last 12 five-minute bars.
- First hour: from 5 minutes after the open to 60 minutes after the open, exchange time.

## 3. What the evidence says

Grades: A = tested on our own consolidated data, in sample and out of sample. B = published, peer reviewed or cost adjusted. C = vendor backtest with stated parameters. D = claimed with no numbers.

| Finding | Grade | Numbers |
|---|---|---|
| Raw 3-bar-rise entry has no edge | A | 47.7 percent continuation in sample (n=4,009); 48.6 percent out of sample (n=27,197) |
| First-hour entries beat afternoon entries | A (in sample), weaker out of sample | 53.0 percent and +17 bps in sample vs 45.5 percent and -15.5 bps after 2pm; out of sample 49.2 vs 48.9 percent, so treat as a mild filter, not an edge |
| Full rule (this SOP) is tail-driven and positive out of sample | A, low confidence | 34 trades over 145 sessions: mean +150.6 gross, +130.6 at 10 bps a side, +110.6 at 20; trimmed mean +25 to +65; median -17.6 to -57.6; win rate 38 to 44 percent; top trade 76 to 102 percent of total profit; day-level t 0.9 to 1.2 |
| Wide stops beat tight stops; 1-minute stop checks destroy the edge | A | 2.5 ATR on 5-minute closes kept the mean; 1.0 to 1.5 ATR on 1-minute closes cut it by about 24 bps |
| Costs on gappers are about 20 bps a side | A | measured half-spread at entry: median 10.1, mean 18.0 bps |
| Nightly call-put open interest ranking predicts next-day returns | B | published 2025, 458 stocks, 2020 to 2023, long-short 19 bps a day net of bid-ask, about 61 percent annualized |
| Opening range breakouts win slightly over half the time | C | 190,460 trades, 611 symbols, 30 days: 52.2 to 52.9 percent |
| Dealer-gamma regime: momentum continues when net gamma is negative, pins when positive | D (mechanism credible, no published win rate) | thresholds exist (net GEX below zero, call wall within 1 to 3 percent) but no backtest in the folder |
| Squeeze fuel: short interest over 20 percent of float, days to cover over 5, borrow cost over 30 percent | D | checklist thresholds only; GME and VW anecdotes |
| Sweeps, unusual-whales alerts, put-call extremes, IV rank for direction | D | no backtest delivered in any file; treat as unproven |
| High IV rank before a catalyst predicts IV crush | C | use only as a veto against buying options; this SOP holds stock, so it does not apply |
| Most frequent day traders lose | B | 97 percent lost in the Taiwan and Brazil studies |

## 4. The rule

Run every step in exchange time from the Alpaca calendar. If any step cannot run, do not trade that day.

Step 1. Universe, 09:25. Screen all US common stocks. Keep symbols with: open (indicated or premarket) at least 3 percent above the prior close; prior close between 10 and 1,250 dollars; 20-day average dollar volume at least 20 million dollars; not a fund by name filter. Rank by gap size. Keep the top 30. Expect about 11 to 25 names.

Step 2. Market gate, 09:35. If SPY is down more than 1 percent from its prior close, do not enter new positions today.

Step 3. Watch, from 09:35 to 10:30. For each name, build 5-minute bars, session VWAP, session high, rvol, and 12-bar ATR.

Step 4. Trigger. A name triggers when ALL of these are true on a completed 5-minute bar between 09:35 and 10:30:
- The last three 5-minute closes are strictly rising.
- The close is a new session high.
- The close is above VWAP.
- rvol is at least 2.0.
A name that is halted, or whose last bar is missing, cannot trigger.

Step 5. Entry. Buy at the open of the next 5-minute bar. One entry per name per day. No entries after 10:30. No adding to positions.

Step 6. Size. Equal notional per position. At most 5 concurrent positions. Total exposure at most 100 percent of allocated capital. No margin. If capital is 1,000 dollars, each position is at most 200 dollars, so only fractionable names qualify at that size.

Step 7. Exit. Track the highest 5-minute close since entry. Sell at the open of the next bar when a 5-minute close drops more than 2.5 ATR below that high. Evaluate the stop on completed 5-minute bars only, never on 1-minute prints. If the stop has not fired, sell everything at 15:55. Never hold overnight.

Step 8. Halt handling. If a held name halts, do nothing while halted. On reopen, treat the reopen print as the current close and apply Step 7.

Step 9. Daily stop. If realized plus unrealized loss for the day reaches 3 percent of allocated capital, sell everything and stop for the day.

Step 10. Record. Log for every trigger, taken or not: timestamp, price, VWAP, rvol, ATR, gap size, the quoted bid and ask at decision time, and the outcome at 30 minutes, at the close, and at the stop. The log is the input for the filter tests in section 5.

## 5. Staged filters (score first, adopt only if they help)

Score these on every logged trigger for 60 trading days. Adopt a filter only if it raises the after-cost mean on the log with a day-clustered interval above zero.

- F1, overnight options positioning (grade B). Each night, snapshot call and put open interest per candidate from the Alpaca options chain. Rank tomorrow's gappers by the overnight change in call minus put open interest. Score whether top-half names outperform bottom-half after triggers.
- F2, squeeze fuel (grade D). Short interest over 20 percent of float, days to cover over 5, borrow cost over 30 percent. Free sources are twice-monthly and delayed; log the values you can get and score them.
- F3, dealer gamma regime (grade D). Net gamma exposure below zero at the open, or price above the call wall. Free tier data is 5 requests a day; enough for a daily flag.
- F4, catalyst present (grade C). At least one symbol-tagged headline since the prior close. Already available from the Benzinga feed.
- Jev (unknown). Ask Jev at 09:58 to score each candidate 0 to 100 for continuation. Score its ranking exactly as the Pre-Build Review specifies. Jev is a filter candidate here, not the decision maker.

## 6. Data required

- Alpaca market data with the existing keys: daily bars for the screen, 5-minute SIP bars, quotes at decision time, Benzinga news. The 99 dollar plan gives real-time SIP; the free plan is enough for shadow scoring with delayed verification.
- Alpaca options chain snapshots (verified working with your keys) for F1.
- Free short-interest sources for F2; a gamma vendor free tier for F3.
- No ORATS purchase in phase 1. Reconsider at 199 to 599 dollars a month only if F1 scores well and needs better options history.

## 7. Status and validation

This rule is a hypothesis with one supportive out-of-sample test, not a proven edge. The parameters (3 percent gap, 2.0 rvol, 2.5 ATR, first hour) were chosen while looking at the August to September window, so that window no longer counts as evidence. The January to July replay is the only honest test so far: positive at all cost levels, driven by a few runners, low confidence.

Validation plan, pre-registered before the first shadow day:
1. Freeze this SOP's parameters. Any change makes a new version and restarts the clock.
2. Run 60 trading days in shadow. Log every trigger and every filter value.
3. Primary metric: after-cost mean return per trade at 20 basis points a side, with a day-clustered 90 percent interval. Secondary: trimmed mean, median, positive-day share, and each filter's lift.
4. Fail is defined now: if the day-clustered interval includes zero at 60 days, the rule stays in shadow or stops. Expect this outcome; the base rates say most day-trading rules die after costs.
5. Any live capital before the 60 days completes requires Micah's approval in his own words, a stated amount, and acceptance in writing that the rule is unproven.

## 8. Risk statements

- The median trade loses. The profit model is a few large winners. A month without a runner is a losing month.
- The out-of-sample rule traded 0.2 times a day. This is not a dozens-of-trades-a-day system. Raising the trade count without a proven per-trade edge multiplies costs, as the earlier tests showed (the all-day flip rule lost 100 to 400 basis points a day).
- 21 plus 145 sessions contain no 2022-style bear market. The rule is untested in a selloff. The SPY gate in Step 2 is the only protection and it is crude.
- Published base rates: 97 percent of frequent day traders lose money.

## 9. QA checklist for Micah

Check each line. Mark pass or fail. Your marks decide what changes before v2.1.

1. Is every threshold in Step 1 to Step 9 a number you accept? Which would you change, and why?
2. Do you accept "no entries after 10:30" even on a day that looks strong at 1pm?
3. Do you accept the 2.5 ATR stop knowing the median trade loses about 40 to 60 basis points?
4. Do you accept at most 5 positions and no margin at the start?
5. Do you accept the 60-day shadow before any live dollar, or do you want option B (small live money after 20 clean shadow days), stating the amount?
6. Which staged filters (F1 to F4, Jev) do you want scored from day one?
7. Do you approve the data spend: 0 now, or 99 dollars a month for real-time SIP?
8. Anything in section 3's evidence table you dispute or want retested?

## 10. Change control

This document is versioned in the Stock Decision Tool folder. Only Micah approves changes, in his own words. Every change: bump the version, restate the frozen parameters, restart the validation clock. Never tune parameters on the window being scored.
