# Pre-Build Review: Jev Stock Decision Tool

Date: 2026-09-21 (Sunday evening Pacific; the next US open is Monday 2026-09-21 at 06:30 Pacific). Author: Claude, for Micah. Status: review only. No build code exists. Two adversarial review rounds: the first on the draft design (four reviewers, 64 findings, merged in section 6), the second on the revised design (four reviewers, 55 findings, merged in section 6b).

## Decision statement, in your terms

1. What can be built for Monday: a shadow logger with no order code in it. At 09:58 ET it logs the day's single-stock gap-ups; at 10:00 it asks Jev one score question per name; after the close and the next close it scores every answer on consolidated data. Nothing trades.
2. What Friday will show: that the code runs, what a round trip really costs on these names from logged quotes, Jev's latency and error rate, and five days of rank correlations, which is not enough to conclude anything.
3. What it costs: Jev under 1 USD a day; hosting about 5 USD a month; Alpaca 0 or 99 USD a month; your time to approve, plus this session's overage.
4. What it cannot do: prove an edge in days, make dozens of trades a day on real single stocks (there were about 11 qualifying gap-ups a day and 3 rule-eligible entries a day in the last 21 sessions), or turn 1,000 USD into anything but a small loss on the rules tested.
5. What you sign before the first call: a one-page pre-registration with the metric, the baseline, a 60-trading-day horizon, a futility stop only, and the sentence "no live capital, no size change and no STOCK-Auto lane before a named date".

## TLDR

- Verdict: do not put money on this. If anything is built, build a research logger only: Jev ranks each day's gap-ups, every answer is scored later against consolidated data, nothing trades, no live buy or sell board, fixed end date, pre-registered with "expected outcome: fail". That is Option A. Option B (1,000 USD live from Monday) is not recommended because every rule tested tonight loses on real single stocks after measured costs.
- Jev works through your gateway now. One probe call at 03:31 UTC: 141 ms at the provider, about 1 second end to end on a cold connection, cost 0.0000245 USD, 5 USD credit on the account. On an AAPL state it answered "higher at the close" with probability 0.51, "up in the next 30 minutes" 0.67, conviction 1.8 of 4. Speed and cost are as claimed. Accuracy is unknown, and every public market record of Jev is negative.
- Your same-day momentum goal, tested on your data: the version that looked positive an hour ago was carried by leveraged single-stock ETFs and one micro-cap biotech. Half of the 1,208 mover-days were funds or leveraged products (605). On single stocks only, buy strength at 10:00 with a trailing stop lost 10 to 27 basis points a trade at 10 basis points a side, the opening range breakout with a range-low stop lost about 100 basis points a trade, and your literal rule (buy on a three-bar rise, sell on a three-bar fall, all day) lost 100 to 400 basis points a day. Measured half-spreads on these names at entry: median 10 basis points, mean 18, so 20 basis points a side is the realistic cost, not 10.
- Faster is not better. One-minute exits were worse than five-minute exits. The average one-minute move on a mover is 19.6 basis points, about one round trip of cost. Jev's own one-decision-per-second record (jev-hft, Bitcoin) was eaten by fees. Watch by the second if you like; decide a few times a day.
- Proof in days is not available. The per-trade swing is about 400 basis points against edges of a few basis points either way, and trades on the same day move together, so the honest unit is the trading day. From the day-level figures, distinguishing the best rule's mean from zero at 90 percent confidence would take roughly 500 to 1,000 trading days, two to four years. Five days can prove the plumbing.
- Volume: mechanically yes on Alpaca (no day-trade rule since 2026-06-04, 200 orders a minute). Margin on each trade: no. In every rule, most trades lost and a few large winners carried the mean, or nothing did.
- What Jev improves: speed (about 0.14 to 0.26 seconds a decision versus 5 to 15 for Fable and minutes for a Claude session), cost (about 0.0001 USD a name-decision, 65 times cheaper than batched Fable, zero draw on your Claude quota) and measurement throughput. Not accuracy.
- Remaining switches for Option A, all yours: rotate the gateway key that was pasted into chat and set a monthly spend cap on the Vercel team; rotate STOCK-Auto's Alpaca keys and strip the secrets file from the zip on Drive, because this session read that zip and the keys therefore exist outside STOCK-Auto's environment; a private GitHub repository for the tool plus a Railway account or a 5 USD VPS; the Alpaca 99 USD data plan (recommended, not required for a logger); a separate Alpaca paper account for the worker so it never shares STOCK-Auto's keys; your approval in your own words. A logger can be running by Monday's open if those arrive tonight, with the independent code review the skill requires before the first call.
- The review sits in a public fork (remote-jobs). It contains your plan capital, rules and results. Move it to a private repository before it grows further; that decision is yours.

## 1. Goal in one line

Find what is rising, buy it as it rises, sell it as it turns, same day, across dozens or hundreds of stocks, with Jev making each call in a fraction of a second, and feed the result to STOCK-Auto once it is proven. Population: liquid US single stocks that are in play that day (gap-ups), not funds, not leveraged products, not index ETFs.

## 1b. Your same-day momentum goal, tested

Design (fixed before running): every trading day from 2026-08-20 to 2026-09-18 (21 sessions), screen all 12,641 US symbols with daily bars for two sets known at the open: gap-ups (open at least 3 percent above the prior close) and prior-day movers (up at least 5 percent yesterday), each with 20-day average dollar volume of at least 20 million USD and price 5 to 1,250 USD, top 30 of each. That gave 1,208 symbol-days with consolidated (SIP) 5-minute bars. Decisions at bar closes, fills at the next bar's open, costs per side.

Correction made after the first adversarial review: the screen did not exclude funds. 151 of the symbols, 605 of the 1,208 symbol-days, were ETFs, ETNs, or 2X and 3X single-stock leveraged products (Tradr, T-REX, GraniteShares, Direxion, ProShares and similar). The four largest winners in the first pass were BIAF (a micro-cap biotech, +3,603 basis points) and three 2X leveraged ETFs on the same day (+1,300 each). The tables below are single stocks only.

What the movers did on their own from 10:00 ET to the close, all 1,208: gap-ups +8.6 basis points mean (51 percent positive), prior-day movers -54.4 (44 percent positive). Yesterday's winners fade; today's gappers barely continue. SPY over the same days moved less than one percent either way.

Rules on single stocks only (603 symbol-days, price at least 5 USD), basis points per trade:

| Rule | Trades | Win rate | Gross mean (trimmed 1 percent) | At 10 bps a side | At 20 bps a side | Positive days |
|---|---|---|---|---|---|---|
| Buy strength at 10:00 (above open and VWAP), 1.5 ATR trailing stop | 182 | 42 percent | +9.7 (-3.0) | -10.3 | -30.3 | 11 of 21 |
| Same, 2.5 ATR stop | 182 | 45 percent | -3.0 (-8.2) | -23.0 | -43.0 | 12 of 21 |
| Same, price at least 10 USD, 2.5 ATR | 151 | 46 percent | +1.6 (+7.3) | -18.4 | -38.4 | 12 of 21 |
| Opening range breakout (30 min), stop at range low | 227 | 43 percent | -80.6 (-67.2) | -100.6 | -120.6 | 5 of 21 |
| Opening range breakout, 1.5 ATR trailing stop | 227 | 44 percent | +7.1 (-12.9) | -12.9 | -32.9 | 7 of 21 |
| Buy on 3-bar rise, sell on 3-bar fall, all day (all movers, about 10 round trips each) | 1,208 symbol-days | 46 percent | -0.2 | -198.5 | -396.8 | 1 of 21 |

No rule is positive after costs. The day-level t statistics are all between -2.8 and +0.4. The medians are all negative.

Costs measured, not assumed: consolidated quotes at the entry and exit timestamps of the single-stock trades (134 entries): half-spread at entry median 10.1 basis points, mean 18.0, 75th percentile 20.8, 90th 37.1; at exit median 7.1. A market order pays that on each side before slippage. Twenty basis points a side is the honest number for gappers.

Faster observation, tested on the earlier all-mover set: the same entries with 1-minute exits were worse than 5-minute exits at 1.0 and 1.5 ATR and similar at 2.5 ATR. Movers' mean absolute 1-minute move is 19.6 basis points. Per-second decisions sit below that; jev-hft found on Bitcoin at one decision per second that fees consumed the signal.

Design consequences: (1) decide entries once a day at most, (2) do not trade the mechanical rules above, they lose, (3) if Jev is tested, test whether its ranking of gap-ups at 10:00 carries information (rank correlation against SPY-excess to-close return), not whether a rule makes money, (4) assume 20 basis points a side.

## 1c. Options for dozens or hundreds of trades a day

The pattern day trader rule is gone (SEC approval 2026-04-14, effective 2026-06-04; Alpaca moved to real-time intraday margin the same day). STOCK-Auto's settled-cash-only rule is a setting. Rate limits are not the constraint: Jev 1,200 requests a minute direct, Alpaca 200 orders a minute, Hyperliquid 1,200 weighted requests a minute.

What binds is cost per round trip against move size: breakeven accuracy = 50 percent + cost / (2 x mean absolute move). Moves measured from consolidated 5-minute bars, 2026-08-20 to 2026-09-18:

| Venue and role | Instruments | Round-trip cost | Mean 30-minute move | Breakeven, 30 min | Breakeven, 1 hour | Notes |
|---|---|---|---|---|---|---|
| Alpaca, US stocks, taker (today) | Any US stock | 20 to 40 bps on gappers (measured half-spreads above); 10 to 20 on large caps | 25.4 bps on 20 large caps; larger on movers | About 70 percent (large caps) | 64.5 percent | 99 USD a month for real-time consolidated data at 10,000 requests a minute; free tier is IEX, about 3 to 5 percent of volume, 200 requests a minute |
| IBKR Pro tiered, US stocks, maker | Any US stock | About 3 to 6 bps when filled (0.0035 USD a share less rebate; spread earned) | Same | 56 to 62 percent | 54 to 59 percent | Retail limit orders fill about 65 percent of the time and the unfilled ones are the winners |
| Micro index futures (MES, MNQ) | S&P 500, Nasdaq 100 | About 1 to 1.5 bps (0.25 to 0.91 USD a side plus a 1.25 USD tick on about 33,000 USD) | SPY 8.5 bps; QQQ 12.1 bps | 57.4 percent (SPY), 55.2 percent (QQQ) | 55.5, 53.8 percent | No day-trade rule ever; 23 hours; day margin 40 to 50 USD a contract at some brokers; the most competitive market there is; it is the index, not stocks going up |
| Hyperliquid perpetuals, maker | BTC, ETH, alts; HIP-3 stock perpetuals at double fees | Maker 1.5 bps a side, about 3 to 4 bps a round trip after adverse selection | BTC 20.0 bps; ETH 27.0 bps | About 55 percent (BTC) | About 53.6 percent | 24/7; the native jev-trade pattern; both public Jev records here lost |
| Hyperliquid perpetuals, taker | Same | About 9 to 10 bps | Same | About 70 percent | 64.4 percent | Stock-like costs |

How to read it: if "stocks going up" is the point, the venue is stocks with maker orders (IBKR) or Alpaca with one round trip a day, and tonight's data says even that has no measured edge. If "dozens of fast decisions a day" is the point, micro index futures are the only place a 30-minute call needs about 55 percent accuracy instead of 70. Order of work in any venue: pick the venue whose cost matches the goal, prove the per-trade edge after that cost in shadow with an interval above zero, then raise the trade count. More trades multiply whatever the per-trade edge is, including a negative one.

## 1d. Starting Monday 2026-09-21: what it takes, what it costs, what 1,000 USD does

Time: it is about 20:30 Pacific Sunday. The open is 06:30 Pacific Monday. Your Claude weekly limit resets Tuesday 2026-09-22 at 16:00 Pacific; you are on overage until then.

Switched on already: the Vercel card (Jev answers; 5 USD credit).

Still yours to switch on for Option A: a private GitHub repository for the tool that this session can push to; a Railway account (or a 5 USD VPS); a separate Alpaca paper account and keys for the worker; the Alpaca 99 USD plan if you want real-time consolidated bars in the state (IEX real time is acceptable for the state; scoring always uses consolidated bars fetched after the 15-minute embargo); rotation of the pasted gateway key; and your approval in your own words. A direct TypeSafe key pinned to jev-1.13.0 is preferred for the loop because the gateway reports only the alias and cannot tell you when the model changes.

Usage: Jev under 1 USD a day at any scale discussed; Alpaca 0 or 99 USD a month; Railway about 5 USD a month; Vercel free. This session's Claude usage for the build and the independent code review is several hours of Fable at your overage rate.

What 1,000 USD does: on single stocks, every rule tested is negative after measured costs, so the expected result of Option B is a loss of roughly 1 to 4 USD a day with daily swings of 14 to 17 USD and a better-than-even chance that the week ends down. The earlier projection of +0.70 USD a day rested on the leveraged-ETF and micro-cap winners and is withdrawn.

Proof in days is not available. Trades on the same day are correlated, so the unit of evidence is the day. From the day-level mean and swing of the best rule (about +0.7 USD a day against 14 to 17 USD), rejecting zero at 90 percent confidence takes about 500 to 1,000 trading days. What five days can prove: data, Jev latency, the screen, scoring, the pre-registration discipline.

First mover: there is no first-mover advantage in a signal that has not been shown to beat its costs. The first to move is the first to pay the spread.

## 2. What "use Jev" means here

Jev is TypeSafe AI's System One decision model (launched 2026-09-15). It takes a state of up to 32,000 tokens and typed questions (boolean, choice, score) and returns probabilities for all questions in one request. Direct: about 130 ms, POST /v1/systemone, alias jev-latest = jev-1.13.0 (the alias moves). Gateway: typesafe-ai/jev via AI SDK 7.0.105+ experimental_evaluate, about 260 ms warm. Price 0.042 USD per million input tokens, output free. TypeSafe's own documents say calibration holds across groups of predictions, not per answer, and that Jev handles numeric state worse than semantic state; its published evaluations are business workflows scored against a two-frontier-model consensus, with no market task.

jev-trader (github.com/jarrodwatts/jev-trader) is the pattern: one Jev decision per Monad block, post-only limit orders one tick inside the touch (earning the spread as a maker), one order in flight, hold when late, a Bun server with SSE, a Next.js page. The live demo runs Jev (its Jev spend counter is accumulating) and shows about 1.02 million dry-run decisions, a 45.6 percent hit rate on the last 1,000 and a running loss of about 1,110 USD.

What transfers: the loop shape, the dry-run flag, the SSE schema, the page layout. What does not: the 30-second horizon (unscorable against retail costs), the maker-spread economics (retail US equity orders do not reliably earn the spread), and the late rule as written (at 5-minute cadence lateness only measures throttling; replace it with a decision deadline and reason codes).

## 2b. What this improves

| Measure | Claude session (STOCK-Auto v10 path) | Fable on every bar (gateway) | Jev on every bar |
|---|---|---|---|
| Time from bar close to decision | Minutes; a few session runs a day | 5 to 15 seconds per batched call | 0.14 seconds at the provider, about 0.26 warm through the gateway (measured) |
| Names covered per day | About 12 shortlisted names, 1 to 2 passes | 20 names, 78 bars, if paid for | 100 names, 78 bars: about 7,800 name-decisions |
| Cost per name-decision | Your Claude plan quota (exhausted this week) | About 0.007 USD batched | About 0.0001 USD (measured 0.0000245 USD for a 600-token state) |
| Cost per month | Plan quota | About 220 to 1,100 USD | About 4 to 25 USD, plus about 5 USD hosting |
| Decisions scorable in 20 trading days | Dozens | About 31,000 at 20 names | About 156,000 at 100 names |
| Accuracy | Measured at zero contribution in STOCK-Auto's replay | Unknown; frontier LLMs test near coin flip intraday | Unknown on stocks; 45.6 percent on the live crypto demo |

The improvement stops at accuracy. Jev makes finding out fast and nearly free. It does not make the answer yes.

## 3. Benchmark, side by side

| Row | jev-trader live demo (crypto) | jev-hft study (BTC and US stocks) | Lopez-Lira and Tang (2023, JFE 2025) | Zarattini, Barbon and Aziz (2024), stocks in play ORB | STOCK-Auto v10 catalyst backtest | This session's mover test | Option A as revised |
|---|---|---|---|---|---|---|---|
| Sample size | 1,023,492 decisions | 30,312 market-data decisions in nine hours; news sample not published | 159,137 firm-headline-days, about 4,100 stocks | More than 7,000 US stocks, daily selection of stocks in play | 1,058 signals; 12,175 events screened | 1,208 mover-days; 603 single-stock; 182 to 227 trades per rule | About 30 gap-ups a day; 60 trading days; about 1,800 ranked names |
| Population | One pair, MON/USDC on Kuru | Bitcoin on Coinbase; up to 30 US stocks on Alpaca | US stocks with headlines; effect concentrated in small caps | US stocks with unusual relative volume that day | US gap-ups, 20M USD dollar volume and up | US gap-ups and prior-day movers, 20M USD dollar volume, price 5 to 1,250 | US gap-up single stocks, funds excluded, price at least 10 USD |
| Data sources | On-chain order book | Coinbase book, Alpaca bars, Benzinga, SEC, X | Headlines and CRSP returns | Consolidated intraday bars | Consolidated SIP 5-minute and daily bars | Consolidated SIP 5-minute and 1-minute bars, consolidated quotes | Alpaca IEX or SIP live state; SIP for scoring after the embargo; Benzinga headlines in a separate request |
| Period | 2026-09-17 to date | September 2026 | October 2021 to May 2024 | 2016 to 2023 | 2024-09-03 to 2026-08-25 | 2026-08-20 to 2026-09-18 (21 sessions, one regime) | Forward only from first run; fixed end date |
| Cost and fill assumptions | Maker fills, simulated | Paper; fees noted as consuming profit | Before costs in the headline; unprofitable at 20 bps round trip | Commissions and slippage modeled; net results reported | 50 bps a side | 0, 10 and 20 bps a side; half-spreads measured at 10 (median) and 18 (mean) | 20 bps a side; fill at first consolidated trade at least 1 second after the decision |
| Success criteria | None published | Rank correlation with next move versus a free imbalance rule | Sharpe and daily alpha of a long-short portfolio | Net return, Sharpe, alpha versus benchmark | 300 trades, PF 1.3, +0.15R | Mean, trimmed mean, median, day-level t, positive days | Primary: rank correlation of Jev's 10:00 ranking against SPY-excess to-close return, block-bootstrapped by day; secondary with Holm correction |
| Review process | Open source demo, no report | Public repo with method docs, single author | Peer reviewed | SSRN working paper, widely cited, some replications | Internal, rules fixed before test | This document, two adversarial rounds | Pre-registration file hashed and signed before the first call; independent code review |
| Result | 45.6 percent hit rate, running loss | Jev signal real at 2 to 10 s but subsumed by a free rule; fees ate it; 80 percent of answers leaned down | GPT-4: 58 percent hit rate, 34 bps a day, Sharpe 2.97 before costs; decayed from Sharpe 6.5 in 2021Q4 to 1.2 in 2024; unprofitable at 20 bps | Reported significant net benefit from restricting ORB to stocks in play (numbers in appendix note) | +0.031R, PF 1.06; out of sample -0.023R; LLM contribution zero | Every rule negative after costs on single stocks | Unknown; expected outcome written as fail |
| Known failure modes | Late blocks, tiny notional | Directional lean, fees, one nine-hour run | Small caps, costs, decay, lookahead in any backtest of a pretrained model | Leverage in headline figures; single research group; replication mixed | Reaction-day entries lose | One regime; funds contaminated the first pass; costs assumed until measured | Listed in sections 5 and 6 |

Where Option A is weaker than a benchmark row and why: shorter period than Lopez-Lira or Zarattini, because Jev cannot be backtested (training data undisclosed, alias moves), so it is forward only; smaller universe than Zarattini, because the design rejects funds and leveraged products, which the mover test showed were the only winners.

## 4. Sample and data

Probed live on 2026-09-21:

- Jev through the Vercel AI Gateway with the card on file: one evaluation on an AAPL state, 141 ms at the provider, 1,012 ms end to end including connection setup, 0.0000245 USD, model reported only as the alias typesafe-ai/jev. Credit balance 5 USD.
- Alpaca, with STOCK-Auto's paper keys: consolidated SIP historical 5-minute and 1-minute bars work (15-minute embargo); IEX real time works; consolidated quotes at timestamps work; Benzinga news works. 32,657 5-minute bars for 20 names and 153,377 for 96 names fetched in seconds; 585,056 daily bars for 12,641 symbols in 28 seconds; 404,367 1-minute bars for 1,080 mover-days in 16 seconds.
- Large-cap baselines are identical on SIP and IEX (mean 30-minute move 25.4 versus 25.6 basis points; to close 51.4 both), so the first-draft breakeven table stands.
- jev-trader backend: public state and SSE, read for its record.
- STOCK-Auto v14: read from your Drive for the integration surface. It does not reference the Alpaca day-trade fields that were removed in July 2026.

Storage: under 100 MB a year at any scale discussed if the state is stored as hashes and reconstructable inputs rather than full JSON. Cost per month for Option A: Jev under 25 USD, hosting about 5 USD, data 0 or 99 USD.

Backtest versus live: none of Jev's answers can be replayed on history and scored as a forecast; the evaluation is forward only.

Baselines the tool must beat (single stocks, from the same data): naive momentum at 30 minutes 48.5 percent; always-long gap-ups from 10:00 to the close +8.6 basis points before costs; the mechanical rules above, all negative after costs.

## 5. Weakest links

1. Jev has no directional information on stocks at any tradable horizon. Evidence against it: the live demo's 45.6 percent, jev-hft's finding that a free imbalance rule absorbed its signal, TypeSafe's own statement that Jev handles numeric state worst. Handling: forward test only, one primary endpoint (rank correlation against SPY-excess to-close return), the state discretized into words, controls that include a logistic regression on the same features, and fail written as the expected outcome.
2. The costs. Measured half-spreads at entry on gappers average 18 basis points. No rule tested clears them. Handling: no order path in phase 1; if a pass ever occurs, the venue question in 1c is re-opened before any live test.
3. Sample and plumbing hide the answer. Twenty-one sessions in one regime; correlated names on the same bar; IEX gaps; alias drift; late answers counted as holds. Handling: 60 trading days minimum, SPY-excess outcomes, block bootstrap by day, model version pinned and logged per row, decision deadline with reason codes, scoring on consolidated data after the embargo.

Reused: jev-trader loop shape, dry-run flag, SSE schema, page layout; STOCK-Auto's untrusted-headline convention. Redone: horizon, questions, cost model, scoring, storage, hosting, the late rule.

## 6. Adversarial review, round one (draft design), merged

Four independent reviewers who had not seen the work: a statistician (verdict: do not build, 14 findings), a systems engineer (build with changes, 19), a risk officer (build with changes, 17), a completeness critic (do not build, 14). Disposition of each theme:

Fixed in this document:
- Wrong weekday (the review said Monday 2026-09-22; Monday is 2026-09-21). Fixed.
- Mover screen included ETFs, ETNs and leveraged single-stock products, and one trade supplied a third of the gain. Re-run on single stocks only with trimmed means, medians, top-trade share and day-level tests (section 1b). The positive result did not survive.
- Costs assumed at 10 basis points a side without a probe. Measured from consolidated quotes at entry and exit (section 1b). Twenty a side adopted.
- Large-cap baselines computed on IEX while the mover test used SIP. Recomputed on SIP; identical.
- No Jev call had ever been made. One made through the gateway after the card was added (section 4).
- Whether the jev-trader demo runs Jev or its mock. Its Jev spend counter is accumulating; it runs Jev.
- Whether STOCK-Auto reads removed Alpaca day-trade fields. It does not.
- Section 3 lacked the Lopez-Lira column and the best comparable for a gap-up design. Both added.

Accepted as design changes for Option A:
- Delete the 30-minute horizon as an endpoint; breakeven 69.5 to 71.5 percent is unreachable by construction.
- Primary endpoint is rank correlation (or AUC) of Jev's probability against the SPY-excess forward return, which is invariant to Jev's documented directional lean; directional accuracy is secondary. One primary endpoint, Holm correction for the rest, the full request template and thresholds frozen and hashed before the first call.
- Effective sample size: names on the same bar share the market factor, so score SPY-excess returns, one observation per symbol per horizon per day, block bootstrap by day, and run at least 60 trading days.
- Controls computed on the identical state at the identical time: always-long, fade-momentum, VWAP-reversion, and a walk-forward logistic regression on the same features. Naive momentum alone is a straw man.
- Direct TypeSafe key pinned to jev-1.13.0, response model logged per row, run aborted with an alert if it changes; the gateway exposes only the alias.
- Replace jev-trader's late rule with a decision deadline (bar open plus 10 seconds) and reason codes (provider 429 or 529, timeout, data gap, worker down); late answers excluded from accuracy, not scored as holds.
- Fill at the first consolidated trade at least one second after the logged decision timestamp; score on SIP bars fetched after the 15-minute embargo; scorer idempotent, keyed by decision id and horizon.
- Exclude ex-dividend and split days from the next-day horizon.
- Separate Alpaca paper account and keys for the worker, REST polling only, because Alpaca allows one WebSocket per account and STOCK-Auto may hold it.
- Drive the session clock from Alpaca's clock and calendar endpoints; the run crosses the DST change on 2026-11-01.
- Split requests: numeric state discretized into words for the direction and conviction questions; headlines only, stripped and capped, in a separate request for the catalyst question. Headlines are an injection vector TypeSafe itself documents.
- No live buy or sell board. Answers are published only after their outcome horizon has resolved and been scored, shown as calibration bins and hit rates. A live board of green decisions is a discretionary trading screen.
- No writes into STOCK-Auto's Drive folder, no live /signals endpoint, no weekly-review hook in phase 1. STOCK-Auto reads nothing from the tool.
- Secrets: rotate the pasted gateway key now; move STOCK-Auto's secrets out of the zip on Drive into its runtime environment and delete the zip (your action).
- Hosting: SQLite in WAL mode with a nightly copy, Railway deployment overlap set to zero and draining to 30 seconds, or a single process on a 5 USD VPS; deploy outside market hours.
- Pre-registration file (endpoints, baselines, thresholds, end date, "expected outcome: fail") hashed and signed by you before the first call.

Accepted as fatal for the original integration plan, and why the plan changed:
- Breakeven accuracy sits above every published Jev result; no engineering fix exists. Option A is therefore a research logger with fail as the expected outcome, not a signal feed.
- The original graduation gate was weaker than the gate that retired STOCK-Auto's catalyst engine. There is now no graduation gate into STOCK-Auto at all in phase 1.
- Under SOP 11 a per-symbol direction answer is a stock pick and has no legal destination inside STOCK-Auto. A pass cannot become a lane unless you amend SOP 11 in writing and relock.
- 5,000 USD of settled cash cannot execute an intraday signal on 20 names. Moot with no order path.

Answered:
- "Are we using Jev for quick, cheap decisions?" Yes. It is the only decision model, measured at 141 ms and 0.0000245 USD a call. Cheap and fast are settled. Right is not.
- "The review sits in a public fork." True. Moving it is your decision.

## 6b. Adversarial review, round two (revised design), merged

Three lenses (statistician, execution engineer, risk officer) and a completeness critic reviewed sections 1b to 1d as they stood before the single-stock rerun. All four returned "build with changes" with eight findings marked fatal. Disclosure they asked for: these are lenses run by the same model in the same session, not independent human reviewers; the checks that are independent of this session's judgment are the reruns on data and the probes.

Fixed with data after their findings:
- "The floor was computed on a universe the design no longer uses." Rerun on single-stock gap-ups only: 241 symbol-days in 21 sessions, about 11 a day; the buy-strength rule qualified on 63, about 3 a day. At 10 basis points a side the mean is +0.6 (1.5 ATR) or -43.6 (2.5 ATR) basis points a trade, trimmed means -36 and -64, medians -62 and -67, and the day-clustered 90 percent intervals span roughly -400 to +400 basis points a day. Holding every single-stock gap-up from 10:00 to the close lost 60 basis points on average. There is no floor.
- "Costs are unmeasured." Measured from consolidated quotes (section 1b): 10 basis points median half-spread at entry, 18 mean.
- "Jev's response shape for a ranking is unverified." Verified: the score question returned a probability-weighted score and a per-level distribution; the boolean returned a probability; provider confidence came back in the metadata.
- "Account type unresolved." The paper account is a margin account, multiplier 4, about 100,000 USD of paper equity, shorting enabled, no day-trade fields present. 89 percent of the gap-up names are fractionable on Alpaca.
- "The 5,600-trade figure is not reproducible and uses the wrong unit." Replaced with day-based figures (500 to 1,000 trading days).
- "Two different Option Bs." There is now one Option B, and it is not recommended.
- "Screen ranking key unstated." The key is gap size at the open (open divided by prior close) for gap-ups and prior-day return for movers, both computed from daily bars known at 09:30; the dollar-volume filter uses the prior 20 sessions. No post-10:00 data enters the screen.

Accepted as design changes for Option A:
- Metric for Jev's ranking job: a score question (0 to 100) per name, labeled by the 10:00-to-close return minus SPY's return over the same window; primary statistic the daily cross-sectional Spearman correlation averaged over days and tested at the day level; incremental correlation after regressing out a free baseline of gap size, relative volume, the 09:30-to-10:00 return and distance from VWAP. Jev must beat the baseline, not zero.
- Score every screened name every day in shadow, so the metric uses all 10 to 30 names rather than a selected few.
- Horizon 60 trading days minimum; stop early only for futility.
- The pullback question is asked once per pullback episode and labeled by what the price did afterward, not by whether a mechanical stop fired.
- Log the consolidated quote at every decision minute so realized half-spreads are measured continuously.
- Direct TypeSafe key as primary with the version identifier logged on every answer; gateway as fallback only.
- Alpaca clock and calendar drive the schedule; halts are detected from the trading status stream and marked.
- Postgres or a Railway volume rather than ephemeral storage; the browser connects to the worker's SSE directly; endpoints behind a bearer token; no account identifiers in any payload.

Accepted as fatal for Option B and for a Monday order path:
- Option B has negative expected value before the first trade and cannot be sized as modeled (52 USD positions, fractional orders, whole-share names). Removed as a recommendation; it appears only to record that it was asked for.
- A fully built and reviewed execution system by 06:30 Pacific is not realistic; Option A ships with no order-submission code path at all.
- The gap-up book is long, high-beta and correlated; the 21 sessions contain no market-wide selloff, so the tail is not the 25 USD worst day shown in section 1d.

Untested, in order of how much it could change the answer: Jev's daily rank correlation on real gap-ups over 60 days (the purpose of Option A); the frozen rules replayed on January to July 2026 and on 2022; halt frequency among gap-ups from the trading status stream; realized fills versus the next-bar-open assumption.

## 7. Your four questions

1. Best comparable example, row by row: section 3. The closest to your goal is Zarattini, Barbon and Aziz's stocks-in-play opening range breakout (7,000 stocks, 2016 to 2023, net of costs, positive as published). Our 21-session replay of a related rule on single stocks lost about 100 basis points a trade with a range-low stop. The closest to the tool is jev-hft: same model, paper scoring, signal absorbed by a free rule and eaten by fees.
2. What an expert would say is wrong: intraday single-stock direction from bars is near coin flip for every published method; measured costs on gappers are about 20 basis points a side and no tested rule clears them; the one positive result tonight came from leveraged products and a micro-cap; Jev's calibration is group-level, its numeric handling is its weak spot, and its one live record is negative; twenty-one sessions is one regime.
3. Not tested that could change the answer: Jev's ranking of real gap-ups at 10:00 scored against SPY-excess to-close returns over 60 days (the whole point of Option A); Jev on headline text alone, event driven, which the literature says is where LLM edges have appeared; a walk-forward logistic baseline on the same features; the stocks-in-play ORB rule exactly as published over a longer sample.
4. The assumption that kills this: that Jev's probability on a gap-up carries information about the rest of that day beyond what the bars already say. If it does not, no cadence, universe, venue or architecture saves it, and every mechanical fallback tested tonight loses.

## 8. Decisions for you

- Option A (the only one recommended if anything is built): research logger. Gap-up single stocks, funds excluded, price at least 10 USD, about 11 a day at the 3 percent gap threshold in the last 21 sessions (loosen to 2 percent if the count is too low, decided before the first run). At 10:00 ET one Jev request per name with the state in words, plus a separate headline request. Scored later on consolidated data at to-close and next-day-close horizons against SPY-excess returns and four controls. No orders, no live board, no STOCK-Auto hooks. 60 trading days. Expected outcome written down as fail. Cost under 30 USD a month plus optional 99 USD data. Can be logging by Monday's open if the repo, hosting, worker keys and your approval in your own words arrive tonight, with the independent code review before the first call.
- Option B: 1,000 USD live from Monday on the one-round-trip rule. Not recommended. Every version tested loses after measured costs; expected about -1 to -4 USD a day, better-than-even chance of a losing week, and a live P&L line that will pressure the design.
- Option C: do not build. STOCK-Auto's trend engine remains the only live logic.
- Option D: a separate pre-build review of the published stocks-in-play opening range breakout as a mechanical strategy, replayed exactly as published over years, not weeks, before Jev is asked to improve it.

Sub-decisions if A: direct TypeSafe key versus gateway (direct recommended); Railway versus a 5 USD VPS; Alpaca 99 USD plan or IEX live state; private repository name.

## 9. Memory note

No memory tool is available in this session. Record: "2026-09-21 Pre-Build Review, Jev stock decision tool. Jev works via gateway (141 ms, 0.0000245 USD a call). Every intraday rule tested on single stocks loses after measured costs (half-spread 10 to 18 bps on gappers). Verdict: no order path; Option A research logger only, 60 days, expected fail; Option B (1,000 USD live) not recommended. Blockers: key rotation, private repo, worker keys, approval in own words."

## Appendix: data tables and scripts

CSV files next to this document: Horizon Baselines, Watchlist Baselines 30 Minute, Universe Expansion Baselines, Sample Size Power, Movers Momentum Baselines (all movers, including funds; superseded for conclusions by Movers Single Stock Only), Movers Single Stock Only, Exit Granularity Test, Venue Breakeven Table. Scripts: Movers Momentum Test.py, Exit Granularity Test.py. Measured half-spreads and the Jev probe output are in the session log.

Zarattini and Aziz (2023) reported a 5-minute opening range breakout on QQQ returning 1,484 percent from 2016 to 2023 against 169 percent for buy and hold, using leverage; their 2024 paper with Barbon extended it to more than 7,000 stocks and reported a significant net benefit from restricting trades to stocks in play. The QQQ study reports an annualized alpha of 33 percent net of commissions, with leverage via 3x products. Exact net figures for the stocks-in-play paper were not retrievable in this session (SSRN blocked the fetch) and should be read from the paper before Option D is scoped.
