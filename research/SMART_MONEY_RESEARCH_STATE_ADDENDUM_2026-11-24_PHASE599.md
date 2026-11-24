# Smart Money Research state addendum — Phase 599 (2026-11-24 15:56 UTC)

Main HEAD at preflight: 6a0362c2af1a9f76f935663d9698be8ca5c66e6c.

## Operational state
- 8,109 Actions runs; latest 100 = 90 success / 10 failure; 0 active / 0 queued.
- 59 schedule-triggered runs; 380 branches; 72 open PRs; 96 workflows; 492 research entries.
- Latest natural FINRA/CFTC/Form 4/Form 144 runs: 45339067236 / 45338400329 / 45332760566 / 45330252226. Their jobs and artifacts were inspected.
- Form 144's 15:47 UTC nominal slot had not appeared by 15:56 UTC; this nine-minute delay is not classified as a new failure. Form 4's 16:17 UTC slot was not yet due. Individual workflow enabled/paused state is not exposed by the read-only connection.
- No workflow was dispatched, rerun, cancelled or duplicated.

## New source-ranking decision
- Databento OPRA.PILLAR is the leading conditional route for a bounded, licensed market-wide options-flow sample. Advertised history starts 2013-04-01. TCBBO/CMBP-1 begin 2023-03-28; pre-2023 data are subsampled and only CBBO-1m is available. OPRA does not publish aggressor side; TCBBO supports quote-relative inference only.
- Databento's live OPRA commercial non-display fee table currently lists $2,000/firm plus separate distribution/user fees; this is not a historical-only quote. Exact historical pricing and license applicability remain unresolved.
- Cboe DataShop standard license prohibits strategy creation absent a separate written and executed agreement; Massive and ThetaData individual-use terms are not suitable for the intended organizational/public-repository workflow without new written rights.
- ORATS Near-EOD remains volatility context only; its one-date public sample is not historical F80 coverage and it does not identify signed flow.
- OptionMetrics TradeFlow remains the leading direct signed-flow hypothesis but requires a sample, methodology/coverage validation, PIT vintages and a license.

## Strategy and research status
- New signals admitted: 0.
- Alpha/OOS/bootstrap/LOO results: 0.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- No data, license, credentials, code, workflow or production changes were made.
- Full audit: PHASE599_OPTIONS_SOURCE_LICENSE_AND_PIT_RERANK_2026-11-24.md.
