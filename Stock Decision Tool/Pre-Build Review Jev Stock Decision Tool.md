# Pre-Build Review: Jev Stock Decision Tool

Date: 2026-09-21. Author: Claude, for Micah. Status: review only. No build code exists yet.

## TLDR

- Verdict: build with changes. Build the tool as a scored shadow signal with no order path. Do not copy jev-trader's 30-second horizon or its maker-spread economics onto US stocks.
- Your goal, tested on your data: find what is rising, buy it as it rises, sell it as it turns, same day, dozens of names. On 1,208 mover-days from the last 21 sessions, the only version that made money was one round trip per name: buy a gap-up that is still above its open and VWAP at 10:00, hold with a wide trailing stop, sell at the stop or the close. It earned about 26 basis points a trade before costs and 6 to 12 after 10 basis points a side, on about 19 names a day, positive on 10 of 21 days, and not yet statistically distinguishable from zero. Your literal version, buy on a three-bar rise and sell on a three-bar fall all day, broke even before costs and lost 100 to 400 basis points a day after them, because it flips about ten times per name.
- Faster is not better. Per-second decisions were tested by jev-hft on Bitcoin: fees ate the signal. One-minute exits were worse than five-minute exits here at every stop width but the widest. A mover's average one-minute move is 19.6 basis points, about two round trips of cost. Watch by the second if you like; decide a few times a day.
- The kill assumption: Jev can call the direction of liquid US stocks above the cost breakeven. From 21 days of your own Alpaca data, a trade-every-bar tool needs 69.5 percent accuracy at 30 minutes, 59.7 percent to the close, and 53.1 percent to the next-day close, at 5 basis points per side. Every comparable says the intraday horizons fail. Only the daily horizon is open.
- Jev's own live crypto record is negative: about 1.02 million dry-run decisions, a 45.6 percent hit rate on the last 1,000, and a running loss. The jev-hft study found that a free order-book rule explained almost all of Jev's short-term signal, and fees ate the profit.
- What this improves: speed, cost, and measurement throughput. Jev answers in about a quarter second through the gateway, against 5 to 15 seconds for a Fable call and minutes for a Claude session run. A name-decision costs about 0.0001 USD on Jev, against about 0.007 USD on Fable when batched, so roughly 65 times cheaper, and it uses none of your Claude plan quota. That lets the tool score every name on every bar all day, about 7,800 decisions a day at 100 names, so the edge question gets a real answer in weeks. It does not improve accuracy. That is the unknown the test measures.
- Cost is not the constraint. Jev costs 0.042 USD per million input tokens, so 100 names on 5-minute bars cost under 1 USD a day. Sample size is not the constraint either. Accuracy against costs is.
- Three blockers before any code: add a card to the Vercel team, because every gateway call returns 403 today; rotate the gateway key that was pasted into chat; your Claude weekly limit resets 2026-09-22 at 23:00 UTC.
- Decisions for you, as options. A (recommended): the same-day momentum design in section 1b. Universe = each day's gap-ups (about 30 names). Jev ranks them at 10:00 and judges each pullback on 1-minute bars. One round trip per name per day. Scored as a shadow book for 20 trading days against the mechanical rule it must beat. B: a literal jev-trader clone, buy or sell every bar with no abstaining. The data above says it loses at any cost level; it is here only because it is what was first asked for. C: do not build. Keep STOCK-Auto's trend engine as the only live logic.
- Dozens or hundreds of trades a day: the pattern day trader rule no longer blocks this. The SEC approved its elimination on 2026-04-14, it took effect 2026-06-04, and Alpaca replaced it with a real-time intraday margin framework the same day. Settled-cash-only is STOCK-Auto's own setting, not a regulation. What still binds is cost per round trip against move size, and it differs tenfold by venue: 10 to 20 basis points on stocks as a taker, 3 to 6 as a maker on IBKR, about 1 on micro index futures, 3 to 4 as a maker on crypto perpetuals. Section 1c lays out the options. Trade count is the last step: with a positive per-trade edge more trades mean more profit and less variance, and with no edge more trades mean more cost.
- A profit every day is not a realistic target for any version tested; the best rule was positive on 10 to 13 of 21 days.

## 1. Goal in one line

Ask Jev, every 5-minute bar of the US regular session, typed questions about each stock in a fixed watchlist, show the answers live in the jev-trader style, score each answer against what the price then did, and hand STOCK-Auto a signal feed that it reads in shadow mode until the gate passes.

Population: liquid US single stocks. Recommended: the roughly 100 largest by dollar volume (an S&P 100 proxy). The 20-name list (AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA, AMD, AVGO, NFLX, JPM, XOM, LLY, UNH, COST, BAC, WMT, CRM, ORCL, PLTR) is the fallback.

## 1b. Your same-day momentum goal, tested

Goal as you stated it: figure out what is going up, buy it as it goes up, sell it as it goes down, same day, for dozens or hundreds of stocks, to realize a profit each day, with Jev deciding fast.

Test design (fixed before running): every trading day from 2026-08-20 to 2026-09-18 (21 sessions), screen the whole US equity universe (12,641 symbols with daily bars) for two mover sets that are known at the open: gap-ups (open at least 3 percent above the prior close) and prior-day movers (up at least 5 percent yesterday), both with 20-day average dollar volume of at least 20 million USD and price between 5 and 1,250 USD, top 30 of each per day. That gave 1,226 symbol-days, about 58 a day, and 1,208 with full consolidated (SIP) 5-minute bars. Decisions at bar closes, fills at the next bar's open, costs applied per side.

What the movers did on their own, 10:00 ET to the close:

| Set | Symbol-days | Mean, bps | Median, bps | Share positive |
|---|---|---|---|---|
| Gap-ups | 604 | +8.6 | +10.3 | 51.2 percent |
| Prior-day movers | 604 | -54.4 | -34.4 | 44.0 percent |

Yesterday's winners fade. Today's gappers barely continue. Rules tested on all 1,208:

| Rule | Trades | Win rate | Mean, gross | Mean at 5 bps a side | Mean at 10 bps | Mean at 20 bps | Positive days (gross, at 10 bps) |
|---|---|---|---|---|---|---|---|
| R0 hold every mover 10:00 to close | 1,208 | 50 percent | -9.7 | -19.7 | -29.7 | -49.7 | 10/21, 8/21 |
| R1 buy strength at 10:00 (above open and VWAP), sell at close | 395 | 50 percent | -7.2 | -17.2 | -27.2 | -47.2 | 10/21, 9/21 |
| R2 buy strength at 10:00, trailing stop 1.5 ATR | 395 | 44 percent | +26.2 | +16.2 | +6.2 | -13.8 | 13/21, 10/21 |
| R2 with a 2.5 ATR stop | 395 | 45 percent | +32.1 | +22.1 | +12.1 | -7.9 | 12/21, 9/21 |
| R3 opening range breakout, trailing stop | 508 | 44 percent | +18.0 | +8.0 | -2.0 | -22.0 | 9/21, 7/21 |
| R4 buy on 3-bar rise, sell on 3-bar fall, all day (your literal rule) | 1,208 symbol-days, about 10 round trips each | 46 percent | -0.2 | -99.3 | -198.5 | -396.8 | 11/21, 1/21 |

All returns in basis points per trade. The R2 gross mean has a 90 percent interval of -7 to +59, so it is not yet distinguishable from zero. Its median trade loses about 40 basis points; the mean is carried by a few large winners, which is normal for a trailing-stop rule and means results swing day to day.

Faster observation, tested: the same R2 entries with exits judged on 1-minute bars instead of 5-minute bars.

| Stop width | 5-minute exits, gross | 1-minute exits, gross | 5-minute at 10 bps | 1-minute at 10 bps |
|---|---|---|---|---|
| 1.0 ATR | +18.3 | -3.4 | -1.7 | -23.4 |
| 1.5 ATR | +26.2 | +2.5 | +6.2 | -17.5 |
| 2.5 ATR | +32.1 | +24.6 | +12.1 | +4.6 |

Finer exits stop you out on noise. The average absolute 1-minute move on these names is 19.6 basis points, about two round trips of cost. Per-second decisions sit below that, where jev-hft already found on Bitcoin that fees consumed the signal. Speed of reaction is useful; frequency of decision is the enemy.

What this means for the design:

1. Universe: the day's gap-ups, about 30 names. Drop prior-day movers.
2. Cadence: watch on 1-minute bars (or faster) so exits are not late, but decide entries once, at 10:00 ET, and allow at most one round trip per name per day.
3. Jev's two jobs, both scorable: at 10:00, rank the gap-ups by the probability that the name closes above its 10:00 price, so the tool buys the top of the list instead of all of them; on every 1-minute bar while in a position, judge whether the pullback is a reversal or noise, scored in phase 1 against the mechanical 2.5 ATR stop, not acted on.
4. The bar to clear: the mechanical R2 rule is the floor. Jev's selection and exit judgment must lift the after-cost mean with a 90 percent lower bound above zero at 10 basis points a side, over at least 20 trading days and about 400 trades. If they do not, the mechanical rule is the product and Jev is a dashboard.
5. Costs: assume 10 basis points a side on these names, not 5. They gap, their spreads are wider, and fills at the open of the next bar are optimistic.

## 1c. Options for dozens or hundreds of trades a day

Correction to the first draft: the pattern day trader rule is gone. The SEC approved FINRA's amendments on 2026-04-14, they took effect 2026-06-04, brokers have until 2027-10-20 to finish implementing them, and Alpaca switched to its Intraday Margin Framework on 2026-06-04. Intraday buying power now follows real-time margin excess. The 25,000 USD floor is no longer a constraint on Alpaca. STOCK-Auto's settled-cash-only rule is a configuration choice in a margin account, not a regulation.

The constraint that remains is arithmetic: breakeven accuracy = 50 percent + (round-trip cost) / (2 x mean absolute move at your horizon). Cost differs about tenfold across venues, so the venue sets how accurate Jev has to be. Move sizes below are measured from consolidated 5-minute bars, 2026-08-20 to 2026-09-18, for the instruments named.

| Venue and role | Instruments | Round-trip cost | Mean 30-minute move | Breakeven, 30 min | Breakeven, 1 hour | What else you should know |
|---|---|---|---|---|---|---|
| Alpaca, US stocks, taker (today) | Any US stock | 10 to 20 bps: no commission, but spread plus slippage; more on gappers | 25.6 bps on the 20 large caps; larger on movers | 69.5 percent at 10 bps | 64.5 percent | No day-trade limit since 2026-06-04. Free data is IEX real time plus 15-minute delayed SIP at 200 requests a minute; the 99 USD a month Algo Trader Plus plan gives real-time SIP and 10,000 requests a minute and removes the sparse-name problem. |
| IBKR Pro tiered, US stocks, maker (resting limit orders) | Any US stock | About 3 to 6 bps when filled: 0.0035 USD a share less an add-liquidity rebate, and the spread is earned, not paid | Same | About 56 to 62 percent | About 54 to 59 percent | Fills are not guaranteed and the ones you get skew adverse. API access. Costs still well below a taker's. |
| Micro index futures (MES, MNQ) via IBKR or a futures broker | S&P 500 and Nasdaq 100 only, 2 to 4 instruments | About 1 to 1.5 bps: 0.25 to 0.91 USD a side commission plus a one-tick 1.25 USD spread on about 33,000 USD of notional | SPY 8.5 bps; QQQ 12.1 bps | 57.4 percent (SPY), 55.2 percent (QQQ) | 55.5 percent, 53.8 percent | Never had a day-trade rule. Day margin 40 to 50 USD a micro contract at some brokers. Trades 23 hours a day. Deepest, most competitive market there is. It is not "stocks going up"; it is the index. |
| Hyperliquid perpetuals, maker | BTC, ETH, alts; HIP-3 stock perpetuals (NVDA, TSLA, indices) at double fees | Maker 1.5 bps a side (3 bps on stock perps), about 3 to 4 bps a round trip after adverse selection | BTC 20.0 bps; ETH 27.0 bps | About 55 percent (BTC) | About 53.6 percent | 24 hours a day, 7 days a week. This is the jev-trade and jev-trader pattern in its native habitat. Both public Jev trading records here are negative so far. |
| Hyperliquid perpetuals, taker | Same | Taker 4.5 bps a side (9 bps on stock perps), about 9 to 10 bps a round trip | Same | About 70 percent (BTC) | 64.4 percent | Same venue, but crossing the spread puts you back at stock-like costs. |

How to read the table for your goal:

- If "stocks that are going up" is the point, the venue is IBKR Pro tiered with maker orders, or Alpaca with the one-round-trip rule from section 1b. IBKR roughly halves the cost; Alpaca is simpler and already wired into STOCK-Auto.
- If "dozens to hundreds of fast decisions a day" is the point, micro index futures are the only venue where a 30-minute decision needs about 55 to 57 percent accuracy instead of 70. Jev can decide every 5 to 30 minutes for about 1 basis point a round trip, with no day-trade limit and a 23-hour session. The trade-off: two instruments, not hundreds of stocks, and the most efficient market on earth on the other side.
- Crypto perpetuals as a maker are the cheapest 24-hour option and the one Jev was demonstrated on, but the demonstrations lost.

Rate limits are not the constraint at any of these: Jev allows 1,200 requests a minute direct, Alpaca 200 orders a minute on the free plan, Hyperliquid 1,200 weighted requests a minute.

Order of work, whichever venue: pick the venue whose cost matches the goal; prove the per-trade edge after that cost in shadow, with a 90 percent interval above zero; then raise the trade count. More trades multiply whatever the per-trade edge is, including a negative one.

## 2. What "use Jev" means here

Jev is TypeSafe AI's System One decision model. It is on your Vercel AI Gateway as typesafe-ai/jev. It is not a chat model. It takes a state object of up to 32,000 tokens and typed questions (boolean, choice, score) and returns probabilities for all questions in one request, in parallel. It answers in about 130 milliseconds direct and about 260 milliseconds through the gateway. Input costs 0.042 USD per million tokens. Output is free.

jev-trader (github.com/jarrodwatts/jev-trader) is the pattern: one Jev decision per Monad block, a post-only limit order one tick inside the touch so fills earn the spread, one order in flight, hold when late, a Bun server with SSE, and a Next.js page on Vercel.

Two parts of that pattern do not transfer to US stocks. The 30-second horizon is not scorable against retail costs, because mean 5-minute moves on large caps are 10.9 basis points and a round trip costs about 10. The maker-spread economics do not transfer, because a retail order in US equities does not reliably earn the spread. The plan keeps the loop shape, the late rule, the dry-run flag, the SSE schema, and the page layout. It replaces the horizon and the cost model.

## 2b. What this improves

The comparison is against the two ways you could run a decision layer today: STOCK-Auto's retired path, where a scheduled Claude session wrote theses over a short list, and a frontier model such as Fable called on every bar.

| Measure | Claude session (STOCK-Auto v10 path) | Fable on every bar (gateway) | Jev on every bar (this plan) |
|---|---|---|---|
| Time from bar close to decision | Minutes; a few session runs a day | 5 to 15 seconds per batched call | About 0.26 seconds through the gateway, 0.13 direct; all questions in one request, in parallel |
| Names covered per day | About 12 shortlisted names, 1 to 2 passes | 20 names, 78 bars, if paid for | 100 names, 78 bars: about 7,800 name-decisions |
| Cost per name-decision | Your Claude plan quota (exhausted this week) | About 0.007 USD batched, 0.03 USD unbatched | About 0.0001 USD (2,500 input tokens at 0.042 USD per million) |
| Cost per day | Plan quota | About 10 USD for 20 names; about 50 USD for 100 | About 0.17 USD for 20 names; about 0.85 USD for 100 |
| Cost per month | Plan quota | About 220 to 1,100 USD | About 4 to 25 USD, plus about 5 USD for the worker host |
| Decisions scorable in 20 trading days | Dozens | About 31,000 at 20 names | About 156,000 at 100 names |
| Accuracy | Measured at zero contribution in the replay | Unknown; frontier LLMs test near coin flip intraday | Unknown; the live crypto demo is at 45.6 percent. This is what the test measures. |

Speed: about 20 to 60 times faster than a Fable call, and hundreds of times faster than a session run. Cost: about 65 times cheaper than batched Fable per decision, and zero draw on your Claude quota. Measurement: enough decisions in three to four weeks to accept or reject the edge with a confidence interval, which the v10 path never reached.

The improvement stops at accuracy. Nothing here makes Jev right more often. It makes finding out fast and nearly free.

## 3. Benchmark, side by side

| Row | jev-trader live demo (crypto) | jev-hft study (BTC and US stocks) | Lopez-Lira and Tang 2023 | STOCK-Auto v10 catalyst backtest | This plan |
|---|---|---|---|---|---|
| Sample size | 1,023,492 decisions since 2026-09-17 | 30,312 market-data decisions in nine hours; news sample not published | [PENDING research agent] | 1,058 signals; 12,175 events screened | 20 trading days: about 31,000 answers at 30 minutes per 20 names; 2,000 next-day answers per 100 names |
| Population | One pair, MON/USDC on Kuru | Bitcoin on Coinbase; up to 30 US stocks on Alpaca | [PENDING] US single stocks with headlines | US gap-ups, 20M USD dollar volume and up, priced 5 to 1,250 USD | 100 large caps by dollar volume |
| Data sources | On-chain order book each block | Coinbase book, Alpaca bars, Benzinga, SEC, X | [PENDING] | Consolidated SIP 5-minute and daily bars | Alpaca IEX 5-minute bars, Alpaca Benzinga news |
| Period | 2026-09-17 to date | September 2026 | [PENDING] | 2024-09-03 to 2026-08-25 | Forward only, from first run |
| Cost and fill assumptions | Maker fills, simulated, earns spread | Paper only; fees noted as consuming profit | [PENDING] | 50 basis points per side | 5 basis points per side plus half the quoted spread, taker fills at next bar open |
| Success criteria | None published | Accuracy against next move and against a free baseline | [PENDING] | 300 trades, profit factor 1.3, +0.15R | Wilson 90 percent lower bound above the horizon's breakeven; Brier below 0.25 |
| Review process | Open source demo, no report | Public repo with method docs | [PENDING] peer status | Internal report, fixed rules before test | This document plus an independent code review before any test |
| Result | 45.6 percent hit rate on last 1,000; running loss | Signal real at 2 to 10 seconds, but order-book imbalance did better for free; 80 percent of answers leaned down | [PENDING] | +0.031R, PF 1.06; out of sample -0.023R; LLM stock-picking contribution measured at zero | Unknown; that is the point of the test |
| Known failure modes | Late blocks; no abstaining; tiny notional | Directional bias; fees; short run | [PENDING] | Reaction-day entries lose; no edge at retail costs | Listed in section 5 |

Where this plan is weaker than a benchmark row, the reason is given in section 5, or the plan changed. The plan is stronger than jev-trader on cost model and scoring, equal to jev-hft on paper-only design, and weaker than Lopez-Lira on sample period because Jev cannot be backtested honestly (its training data is not disclosed and the jev-latest alias moves).

## 4. Sample and data

Each item below was probed live on 2026-09-21.

- Alpaca 5-minute bars, IEX feed, with your existing keys: 32,657 bars for 20 names over 21 trading days in about 20 seconds; 153,377 bars for 96 names in 18 seconds through the multi-symbol endpoint. Some names are sparse on IEX (V returned 357 bars). The build must check bar completeness per name and drop sparse names, or pay for SIP.
- Alpaca daily bars, SIP feed: 99 names, 77 sessions, under one second.
- Alpaca Benzinga news with the same keys: works, tagged by symbol.
- Yahoo Finance unofficial endpoints: work, but unofficial and not for the loop.
- Vercel AI Gateway: the key lists 376 models including typesafe-ai/jev. Every inference call returns 403 customer_verification_required. Balance 0. A card unlocks it. The gateway free tier is throttled hard, so a direct TypeSafe key is the fallback for the loop.
- jev-trader backend: public state and SSE, read for the numbers above.
- STOCK-Auto v14 code and state, from your Drive: read for the integration surface.

Storage: about 1,600 answers a day at 20 names, or 8,000 at 100 names, a few hundred bytes each. Under 100 MB a year in Postgres or SQLite.

Cost per month, option A: Jev about 25 USD at most, Railway about 5 USD, Vercel Hobby 0, Alpaca IEX data 0.

Backtest versus live: none of Jev's answers can be replayed on history without lookahead risk, because the model's training data is undisclosed. The evaluation is forward only.

Baselines the tool must beat, from the same bars (details in the appendix):

| Horizon | Decisions | Naive momentum accuracy | Mean absolute move, bps | Breakeven accuracy at 5 bps per side |
|---|---|---|---|---|
| 5 minutes | 30,481 | 49.4 percent | 10.9 | 95.8 percent |
| 30 minutes | 28,581 | 48.5 percent | 25.6 | 69.5 percent |
| 1 hour | 26,114 | 48.3 percent | 34.5 | 64.5 percent |
| To the close | 30,727 | 48.4 percent | 51.4 | 59.7 percent |
| Next-day close (99 names) | 7,387 | 49.0 percent | 158.6 | 53.2 percent |

Power: to detect 55 percent against 50 percent needs 618 decisions. That is 6 trading days with 100 names on the daily horizon, or 31 days with 20 names. To detect 53 percent needs 1,715 decisions: 17 days with 100 names, 86 days with 20.

## 5. Weakest links

1. Jev has no directional information on stocks at these horizons. Evidence against: the live demo's 45.6 percent, and jev-hft's finding that a free imbalance rule subsumed the signal. Handling: the tool is scored, not traded. Fail is defined now. If the 90 percent lower bound is below breakeven at every horizon after 20 trading days, the tool stays a dashboard.
2. The signal exists but does not clear costs. Breakeven is 69.5 percent at 30 minutes. Handling: score three horizons, not one, and score the top conviction decile separately. Selective trading is the only way an intraday signal can clear costs.
3. Data and plumbing hide the answer. IEX bars are incomplete for some names, Benzinga headlines arrive late, the gateway throttles, and the jev-latest alias can change answers mid-test. Handling: pin the model version, drop sparse names, log latency and late answers per bar, decide at bar close and fill at the next open.

Reused: jev-trader loop shape, late rule, dry-run flag, SSE schema, page layout; STOCK-Auto's Alpaca and Benzinga access and its untrusted-headline convention. Redone: horizon, questions, cost model, scoring, storage, hosting.

## 6. Adversarial review

[PENDING: three independent reviewers (statistics, systems, risk and integration) and a completeness critic are running. Their findings and the answers to each will be inserted here.]

## 7. Your four questions

1. Best comparable example, row by row: section 3. The closest is jev-hft, the same model on the same asset class with paper scoring. It found the signal did not beat a free rule and did not beat fees.
2. What an expert would say is wrong: intraday direction on large caps is near coin-flip for every published method, costs set a breakeven no signal has cleared, and Jev's one live record is negative. An expert would also say a 20-name daily test is under-powered, which is why option A uses 100 names.
3. Not tested that could change the answer: Jev's accuracy on stocks at any horizon, because no inference call can run until a card is on the Vercel team. Also untested: whether the top conviction decile carries larger moves, and whether headline questions add anything over bars.
4. The assumption that kills this: that Jev's probabilities carry directional information on liquid US stocks beyond what the last few bars already say. If that is false, no cadence, universe, or architecture saves it.

## 8. Decisions for you

- Option A (recommended): the same-day momentum design of section 1b. Gap-up universe, Jev as 10:00 selector and 1-minute exit judge, one round trip per name per day, shadow book scored for 20 trading days against the mechanical R2 rule at 10 basis points a side. The 100-large-cap multi-horizon track from the first draft can run beside it for the same near-zero cost, since it answers a different question (does Jev see anything in bars alone). Cost under 30 USD a month.
- Option B: literal jev-trader clone, buy or sell every bar, no abstaining. The data in section 1b says it loses at every cost level tested. Listed because it was the original ask.
- Option C: do not build.
- Venue sub-decision (section 1c): stay on Alpaca stocks (simplest, wired into STOCK-Auto, 10 to 20 bps a round trip), move stock execution to IBKR Pro tiered maker orders (about half the cost, uncertain fills), or run the fast-decision track on micro index futures (about 1 bp a round trip, two instruments). The shadow test can score more than one venue at once, since Jev costs almost nothing to ask.

The adversarial review in section 6 was run on the first draft (100 large caps, three horizons). Sections 1b and 1c change the universe, the cadence and the venue options; those changes were not adversarially reviewed and need a follow-up pass before any build.

Sub-decisions if A or B: Jev through the gateway as you asked (needs the card) or a direct TypeSafe key (faster, no throttle); Railway for the worker as jev-trader does; whether STOCK-Auto's weekly review should report the shadow metrics.

Nothing in STOCK-Auto's locked files changes in phase 1. A lane that acts on the signal needs your approval in your own words and a relock, after the gate passes.

## 9. Memory note

No memory tool is available in this session. Record: "2026-09-21 Pre-Build Review for the Jev stock decision tool. Verdict: build as scored shadow signal only. Kill assumption: Jev direction accuracy above cost breakeven (69.5 percent at 30 minutes, 53.2 percent next day). Blockers: Vercel card, key rotation, weekly limit."

## Appendix: data tables

The CSV files next to this document hold the full tables: Horizon Baselines, Watchlist Baselines 30 Minute, Universe Expansion Baselines, Sample Size Power, Movers Momentum Baselines, Exit Granularity Test, Venue Breakeven Table.
