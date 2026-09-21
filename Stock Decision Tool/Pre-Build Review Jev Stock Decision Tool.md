# Pre-Build Review: Jev Stock Decision Tool

Date: 2026-09-21. Author: Claude, for Micah. Status: review only. No build code exists yet.

## TLDR

- Verdict: build with changes. Build the tool as a scored shadow signal with no order path. Do not copy jev-trader's 30-second horizon or its maker-spread economics onto US stocks.
- The kill assumption: Jev can call the direction of liquid US stocks above the cost breakeven. From 21 days of your own Alpaca data, a trade-every-bar tool needs 69.5 percent accuracy at 30 minutes, 59.7 percent to the close, and 53.1 percent to the next-day close, at 5 basis points per side. Every comparable says the intraday horizons fail. Only the daily horizon is open.
- Jev's own live crypto record is negative: about 1.02 million dry-run decisions, a 45.6 percent hit rate on the last 1,000, and a running loss. The jev-hft study found that a free order-book rule explained almost all of Jev's short-term signal, and fees ate the profit.
- Cost is not the constraint. Jev costs 0.042 USD per million input tokens, so 100 names on 5-minute bars cost under 1 USD a day. Sample size is not the constraint either. Accuracy against costs is.
- Three blockers before any code: add a card to the Vercel team, because every gateway call returns 403 today; rotate the gateway key that was pasted into chat; your Claude weekly limit resets 2026-09-22 at 23:00 UTC.
- Decisions for you, as options. A (recommended): 100-name universe, Jev questions every 5-minute bar, scored at 30 minutes, the close, and the next-day close, shadow only, 20 trading days, then a go or no-go on the pre-registered gate. B: a literal jev-trader clone on 20 names with only the 30-minute horizon. It will almost surely fail the gate, but it is the fastest thing to look at. C: do not build. Keep STOCK-Auto's trend engine as the only live logic.

## 1. Goal in one line

Ask Jev, every 5-minute bar of the US regular session, typed questions about each stock in a fixed watchlist, show the answers live in the jev-trader style, score each answer against what the price then did, and hand STOCK-Auto a signal feed that it reads in shadow mode until the gate passes.

Population: liquid US single stocks. Recommended: the roughly 100 largest by dollar volume (an S&P 100 proxy). The 20-name list (AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA, AMD, AVGO, NFLX, JPM, XOM, LLY, UNH, COST, BAC, WMT, CRM, ORCL, PLTR) is the fallback.

## 2. What "use Jev" means here

Jev is TypeSafe AI's System One decision model. It is on your Vercel AI Gateway as typesafe-ai/jev. It is not a chat model. It takes a state object of up to 32,000 tokens and typed questions (boolean, choice, score) and returns probabilities for all questions in one request, in parallel. It answers in about 130 milliseconds direct and about 260 milliseconds through the gateway. Input costs 0.042 USD per million tokens. Output is free.

jev-trader (github.com/jarrodwatts/jev-trader) is the pattern: one Jev decision per Monad block, a post-only limit order one tick inside the touch so fills earn the spread, one order in flight, hold when late, a Bun server with SSE, and a Next.js page on Vercel.

Two parts of that pattern do not transfer to US stocks. The 30-second horizon is not scorable against retail costs, because mean 5-minute moves on large caps are 10.9 basis points and a round trip costs about 10. The maker-spread economics do not transfer, because a retail order in US equities does not reliably earn the spread. The plan keeps the loop shape, the late rule, the dry-run flag, the SSE schema, and the page layout. It replaces the horizon and the cost model.

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

- Option A (recommended): 100 names, 5-minute cadence, three horizons, shadow only, 20 trading days, gate as written in the plan. Cost under 30 USD a month.
- Option B: literal jev-trader clone, 20 names, 30-minute horizon, buy or sell every bar, dry run. Fast to see. Almost sure to fail the gate.
- Option C: do not build.

Sub-decisions if A or B: Jev through the gateway as you asked (needs the card) or a direct TypeSafe key (faster, no throttle); Railway for the worker as jev-trader does; whether STOCK-Auto's weekly review should report the shadow metrics.

Nothing in STOCK-Auto's locked files changes in phase 1. A lane that acts on the signal needs your approval in your own words and a relock, after the gate passes.

## 9. Memory note

No memory tool is available in this session. Record: "2026-09-21 Pre-Build Review for the Jev stock decision tool. Verdict: build as scored shadow signal only. Kill assumption: Jev direction accuracy above cost breakeven (69.5 percent at 30 minutes, 53.2 percent next day). Blockers: Vercel card, key rotation, weekly limit."

## Appendix: data tables

The CSV files next to this document hold the full tables: Horizon Baselines, Watchlist Baselines 30 Minute, Universe Expansion Baselines, Sample Size Power.
