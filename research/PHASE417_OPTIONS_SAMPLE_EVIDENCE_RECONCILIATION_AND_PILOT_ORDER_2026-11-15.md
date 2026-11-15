# Phase 417 — Options sample evidence reconciliation and pilot order

**Audit time:** 2026-11-15 13:25 UTC  
**Disposition:** Reconcile prior branch-level sample evidence before further options-source work. Cboe Open-Close and ORATS each have a successful one-date public-sample schema/coverage audit. These are feasibility observations only, not historical-universe, PIT, or alpha passes. No data purchase, vendor contact, return test, or strategy change.

## 1. Repository preflight

- Main HEAD at audit start: `46c9cf1362da93c8beab5af802c5d4232542d342`.
- Rechecked latest 100 Actions runs (7,658 total reported by API), latest 100 PRs (56 open returned), branch search across all returned pages, latest run jobs/logs/artifacts, and the current research state.
- Latest 100 runs: 62 success, 37 failure, 1 cancelled; zero queued and zero in-progress runs at 2026-11-15 13:25 UTC.
- Latest mainline SEC capture: [run 43709012759](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43709012759), both jobs successful; offline regression 15/15. Artifact [14159294388](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43709012759/artifacts/14159294388), SHA-256 `29f3d2b6ddcd78b7a7f46fdf86a534beedcc4c78f2e965da4a187a514b80c442`. It appended 55 feed observations (50 Form 144 and 5 Form 144/A), but produced zero new accessions/events/candidate matches/XML resolutions; no feed-window gap was detected. Persistent SEC state: four successful polls, all events remain signal-ineligible. The 12:37 UTC scheduled slot was still not visible by 13:25 UTC; classify as not observed, not as proof of deactivation. Do not dispatch manually or alter the cron.
- CFTC TFF Phase 384 remains on its existing weekday 22:15 UTC schedule. Next expected capture is Monday 2026-11-16 22:15 UTC, after the official 20:30 UTC release. Sunday has no scheduled slot. Historical baseline rows remain ineligible.
- FINRA Phase 20C remains blocked at 328/329 valid price histories; no universe reduction or provider mixing.

## 2. Important clarification to Phase 416

Phase 416's statement that no Cboe sample bytes were obtained refers to **Cboe Option Trades (OPRA-wide raw trades/NBBO)**. It must not be read as saying that no Cboe options sample had ever been parsed. Earlier branch-level Phase 54 / Phase 59b work successfully downloaded and parsed a **Cboe Open-Close EOD** public sample. The two products are distinct and their evidence is reconciled below.

## 3. Existing sample evidence — Cboe Open-Close EOD

Canonical sample run [41762583602](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41762583602), artifact [13291147097](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41762583602/artifacts/13291147097).

- C1 EOD sample date: 2025-03-28; sample fraction: 20%.
- Contract rows: 23,179.
- Current 335-name diagnostic tickers observed: 288/335 (85.97%).
- Required EOD/participant fields: 100% present and 100% non-null in this sample.
- The 34 participant-volume columns sum exactly to `total_exchange_vol` on all 23,179 rows.
- The same ZIP contained separate 1-minute and 10-minute samples (87,322 and 78,468 rows); those grains do not alter the EOD result.

**What passed:** download/integrity, EOD schema, participant-bucket partition reconciliation, and one-date C1 sample reach.

**What did not pass:** full (non-sampled) coverage, all-four-Cboe-venue coverage, historical point-in-time F80 optionability, adjusted-root/OCC multiplier joins, historical first-receipt timestamps, and total-market coverage. The sample is C1-only; Cboe Open-Close is not consolidated OPRA.

Participant categories remain execution-capacity proxies. Customer includes retail and institutional clients; Professional Customer includes professional traders and institutional participants. Neither identifies beneficial owners or proves informed trading.

## 4. Existing sample evidence — ORATS Near-EOD

Canonical public sample run [41787946992](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41787946992), artifact [13301409440](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41787946992/artifacts/13301409440).

- ZIP: 66,808,802 bytes; SHA-256 `e04a37310b0f453fedc03a000c55adfc517a119279150173916ebdc5fb514570`.
- Trade date: 2024-01-03; 716,822 rows; 5,787 underlyings.
- Current 335-name diagnostic tickers observed: 324/335 (96.72%).
- 39-column core schema; required sample fields were present and non-null.
- Call/put volume is cumulative only through the approximately 3:46 p.m. ET snapshot, not final daily volume.
- OI is prior-night OCC OI, not same-day final OI.
- Sample underlying price fields are option-derived references, not independent equity prices.
- No explicit contract multiplier/deliverable was in the sample.
- Sample hosting Last-Modified (2024-03-12) is not a historical daily publication timestamp.

**What passed:** public sample download, ZIP integrity, core schema and one-date current-list reach.

**What did not pass:** PIT historical F80 coverage, delisted/expired contract continuity, adjusted deliverables, daily first-publication/vintage timestamps, and business-use licensing. The 11 names absent from this one date are not necessarily missing historical coverage; several may not yet have been listed or optionable.

ORATS is a useful broad options-context candidate (volume snapshot, OI, IV, Greeks and quotes), not a signed-flow or participant-identity source by itself.

## 5. Other source evidence that constrains the design

- **Cboe Option EOD Summary:** prior sample run [41763011186](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41763011186), artifact [13290668468](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41763011186/artifacts/13290668468). It validated schema/optional calculations, but only four underlyings were represented and only TSLA overlapped the current 335-name list. It is not a universe-coverage pass.
- **OCC Volume Query:** corrected run [41763113005](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41763113005), artifact [13292225481](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41763113005/artifacts/13292225481). Coverage was 325/335 (97.01%) on 2025-01-03 and 320/335 (95.52%) on 2026-11-02, but OCC explicitly limits the query to about 24 months. The response has underlying/account-type/call-put/exchange aggregates, not aggressor side, open/close, strike/expiry or actual OI. Keep only as a recent complement, not a long-OOS signal source.
- **OptionMetrics IvyDB TradeFlow:** remains the conditional primary signed-flow candidate. Its buy/sell aggressor and participant buckets are vendor-derived execution proxies, not beneficial-owner identity. The 2016 archive floor does not establish that the current TradeFlow classifier was historically applied unchanged; version/vintage, first delivery, correction lineage, exact fields, delisted coverage and business license remain open.
- **Cboe Option Trades:** remains an independent OPRA-wide raw trade/NBBO reconstruction candidate. Its public sample bytes were not obtained in Phase 416. Public documentation conflicts between January 2010 and January 2012 archive floors; retain January 2012 conservatively until reconciled.
- **MIAX Open-Close:** remains a possible independent venue replication, with EOD history from June 2021 for Options/Pearl/Emerald and August 2024 for Sapphire. No sample or full-universe test has passed.
- **ThetaData / Databento / IVolatility:** potentially useful raw trade/quote reconstruction alternatives, but business-use license, full historical symbol/contract identity, cancellation/correction handling, actual historical vintages and complete F80 optionability coverage remain unresolved. Do not infer commercial-use rights from individual pricing.

## 6. Recommended sequence — feasibility only

1. Preserve ORATS as the broad context candidate and Cboe Open-Close as the participant-capacity/open-close candidate; do not conflate their different grains or market scopes.
2. Before any purchase, require written professional/business-use terms and a fixed-price sample/extract scope. No personal-use plan may be used for firm research without explicit permission.
3. Require multi-date samples spanning early/middle/recent history and include known delisted issuers, expired options, adjusted roots, and corporate actions. Measure coverage against historical F80 membership and historical optionability, not today's 335 tickers.
4. Obtain OCC point-in-time series identifiers, multiplier and deliverables; exclude unresolved adjusted contracts rather than assuming 100 shares.
5. Preserve raw trade date, actual file/API first receipt, correction/replacement vintage, KnowledgeDate and execution date. Until a stronger clock is evidenced, use next-session availability and next-session-close execution for both baseline and augmented models.
6. Only after those gates pass, compare participant-specific net opening/closing delta proxies separately, normalized by prior-available OI/ADV and full-OPRA context. Control for prior returns, volatility, liquidity, earnings and market/sector exposure to separate prediction from return-chasing.
7. Any eventual test must use identical exposure/costs versus frozen LTM/F80, chronological nested validation, block bootstrap, issuer-clustered uncertainty, LOO and an untouched holdout. No horizon or CAGR target is imposed.

## 7. Final disposition

- The prior Cboe Open-Close sample is a genuine one-date schema/coverage PASS; Phase 416's no-sample statement is limited to Option Trades.
- ORATS is a genuine one-date schema/current-list reach PASS, not a historical PIT or delisted-coverage PASS.
- OCC Volume Query is recent-only due to its 24-month retention.
- No source is admitted to alpha; no return, OOS, bootstrap, LOO or holdout test is authorized.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, holdout, capital, exposure and production remain unchanged.
- No data purchase, subscription, trial, vendor contact or license acceptance occurred.

