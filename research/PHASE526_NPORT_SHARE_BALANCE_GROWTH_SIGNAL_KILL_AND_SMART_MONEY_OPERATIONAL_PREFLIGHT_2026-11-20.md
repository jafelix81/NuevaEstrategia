# Phase 526 — N-PORT share-balance growth hypothesis disposition and Smart Money operational preflight

**Date:** 2026-11-20 UTC  
**Disposition:** **KILL the simple standalone quarter-over-quarter N-PORT aggregate share-balance-growth ranking as an alpha candidate. Retain N-PORT only as descriptive institutional-holdings context pending stronger identity, vintage and return-data controls.**  
**Research class:** retrospective audit of existing GitHub Actions artifacts and current operational state. No new data pull, vendor request, backtest, or production change.

## Executive decision

The corrected N-PORT pilot and its separate dose-response diagnostic do not show a stable directional relationship between quarter-over-quarter aggregate reported-share growth and subsequent 63-session returns.

Across six completed formation transitions:
- the corrected 27N2 top-decile-minus-bottom-decile mean-return spread is positive in only 2 of 6 periods and negative in 4;
- the 27O cross-sectional Spearman IC is positive in only 1 of 6 periods and negative in 5;
- the 27O dose-response spread is positive in 2 of 6 periods and negative in 4;
- the latest two completed transitions (2024Q4 and 2025Q4) are negative on both diagnostics.

This is not a statistically conclusive rejection of every possible N-PORT feature: the sample has only six completed transitions, returns are incomplete for some securities, and the implementation is not a cost-matched F80 comparison. It is, however, sufficient to stop treating this simple aggregate share-growth ranking as a promising standalone signal. No threshold or holding period will be optimized to rescue it.

## 1. Repository and Actions preflight

- Main HEAD at preflight: `9195e1c63497e04670dc6af3e9535afa05f7b881`.
- Latest 100 Actions runs inspected; zero active or queued runs.
- 63 open pull requests at preflight.
- PRs #180, #181 and #182 (Phase 525 owner/crosswalk implementation and reconciliation) are merged.
- No manual dispatch, rerun, cancellation or duplicate capture was issued.

### Latest scheduled SEC captures (both predate the Phase 525 merge)

**Form 4 — [Run 44716430351](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44716430351), 2026-11-20 10:06 UTC**
- 33 new accession observations.
- 10 structured accessions backfilled.
- 37 detail rows appended, including 27 transaction rows.
- Zero parser errors.
- 1,213 bounded accessions remained for structured backfill.

**Form 144 — [Run 44720422923](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44720422923), 2026-11-20 10:34 UTC**
- Zero new accession events.
- 52 feed-observation rows.
- 10 structured accessions backfilled.
- 64 detail rows appended.
- Zero parser errors or live-feed errors.
- 358 structured accessions remained.

Current committed ledgers at the Phase 525 audit:
- Form 144: 448 event accessions, 90 structured accessions, 660 detail rows, 660/660 XML-hash matches.
- Form 4: 1,268 event accessions, 20 structured accessions, 59 detail rows, 39 transaction rows; 18 single-owner filings and 2 multi-owner filings quarantined.

### Phase 525 owner sidecar has not yet had a post-merge scheduled run

The main-branch Form 4 workflow now contains the scheduled steps to:
1. backfill up to ten oldest bounded, already-structured accessions into `reporting_owners.csv`;
2. build the descriptive Form 144/Form 4 crosswalk;
3. persist the append-only owner ledger and upload a compact artifact.

The latest Form 4 scheduled run occurred before PRs #180–#182 were merged. The current `research/data/sec_form4_first_seen/` directory therefore does not yet contain `reporting_owners.csv`. This is an unvalidated post-merge integration gate, not evidence that the new code failed. Wait for the next existing scheduled run; do not dispatch a duplicate.

## 2. N-PORT corrected pilot: Phase 27N2

The original Phase 27N produced zero tickers because it read a nonexistent `SHARES` field. That output is a code defect and is not evidence against the source.

The corrected [Phase 27N2 run 39496676182](https://github.com/jafelix81/NuevaEstrategia/actions/runs/39496676182) used `FUND_REPORTED_HOLDING.BALANCE` only when `UNIT` was `NS` or `SH`, retained the 335-name frozen universe, used a 75-calendar-day post-report knowledge cutoff, and ranked aggregate share-balance growth. The top and bottom deciles were equal-weighted for a raw 63-trading-session long-minus-short mean-return diagnostic.

| Formation | Ranked names | Raw 63-session top-minus-bottom spread |
|---|---:|---:|
| 2020Q4 | 253 | -10.65% |
| 2021Q4 | 266 | -6.31% |
| 2022Q4 | 289 | +12.86% |
| 2023Q4 | 293 | +5.84% |
| 2024Q4 | 292 | -3.82% |
| 2025Q4 | 300 | -1.74% |
| 2026Q3 | 301 | Not evaluated; forward horizon incomplete |

These are raw cross-sectional spreads, not a costed portfolio return, not annualized and not matched to F80 exposure.

Artifact: [Phase 27N2 artifact 12299225396](https://github.com/jafelix81/NuevaEstrategia/actions/runs/39496676182/artifacts/12299225396).

## 3. Independent dose-response diagnostic: Phase 27O

The separate [Phase 27O run 39503800069](https://github.com/jafelix81/NuevaEstrategia/actions/runs/39503800069) evaluated cross-sectional Spearman IC and top-minus-bottom decile spreads for the same basic reported-share-growth hypothesis.

| Formation | Spearman IC | Top-minus-bottom spread |
|---|---:|---:|
| 2020Q4 | -0.1199 | -11.77% |
| 2021Q4 | -0.0768 | -5.56% |
| 2022Q4 | +0.0161 | +12.03% |
| 2023Q4 | -0.0292 | +6.12% |
| 2024Q4 | -0.1076 | -4.78% |
| 2025Q4 | -0.1006 | -1.74% |

The dose-response is not monotonic or directionally stable. The only positive IC is small (+0.0161 in 2022Q4); the two most recent completed periods have materially negative ICs and negative spreads.

Artifact: [Phase 27O artifact 12303188100](https://github.com/jafelix81/NuevaEstrategia/actions/runs/39503800069/artifacts/12303188100).

## 4. Data and inference limitations

These limitations make the result unsuitable for promotion and reinforce the decision to stop the simple signal:

1. **Only six completed formation transitions.** 2026Q3 is signal-only; it has no completed 63-session outcome.
2. **Incomplete return coverage.** The yfinance logs show unavailable historical return windows for names including AVB, SPWR, LPRO and WBD in 27N2, and EQR, AVB, WBS, EA, LPRO, SPWR and WBD in 27O. Missing returns are not zeros; excluding them can create selection bias, especially for inactive/delisted names.
3. **Identity is still conditional.** Same-snapshot ticker/CUSIP/ISIN co-occurrence is a candidate crosswalk, not a complete effective-dated security master. It does not prove that every mapping was valid and known at the historical decision time.
4. **PIT is conservative but not fully vintage-certified.** The 75-day cutoff uses filing dates and latest filing per series; the existing archives do not provide an immutable original first-receipt/vintage ledger for every historical filing.
5. **Return-chasing is unresolved.** The pilot does not residualize reported-share growth against prior price momentum, prior returns, sector, size, liquidity, volatility or corporate actions.
6. **No economic portfolio validation.** No transaction costs, turnover constraints, identical F80 exposure, block bootstrap, leave-one-out, multiplicity adjustment or untouched independent holdout were applied.

Consequently, do not quote the six-period results as statistically significant alpha or as a fully clean OOS rejection. They are a failed exploratory robustness screen.

## 5. Hypothesis disposition

**Killed:** `NPORT_QOQ_AGGREGATE_REPORTED_SHARE_BALANCE_GROWTH` as a standalone directional stock-selection alpha candidate.

Reasons:
- inconsistent sign across completed periods;
- weak/non-monotonic dose-response (negative IC in five of six periods);
- negative results in the latest two completed periods;
- incomplete survivorship-aware return coverage;
- unresolved historical identity/vintage limitations;
- no prior-return controls or cost-matched comparison.

**Not killed:** N-PORT as a source of descriptive institutional holdings. It may remain useful for contextual variables such as fund breadth, holder persistence or concentration, but those are new hypotheses and must not inherit the failed signal's evidence. Do not resume them until an effective-dated security crosswalk, complete inactive-security returns and filing-vintage controls are independently established. Any new test must be separately preregistered.

## 6. Other source and operational gates

- **FINRA Reg SHO:** Phase 515's parser repair passed offline tests, but the latest live capture [44669121290](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44669121290) predates the repair. Post-merge live validation remains pending.
- **FINRA Consolidated Short Interest:** PR [#159 / Phase 505](https://github.com/jafelix81/NuevaEstrategia/pull/159) remains draft. The last Phase 447 live attempt failed at the credential guard before any API request. Credential configuration and usage rights are not verified by the current read interface. The next scheduled publication is **2026-11-24** for the **2026-11-13** settlement; the settlement date is not the feature-availability date. Before a one-settlement validation, configure an authorized `FINRA_CLIENT_ID` + `FINRA_CLIENT_SECRET` pair or `FINRA_ACCESS_TOKEN` as GitHub Actions secrets and confirm the credential terms for the intended use. Never place secret values in repository files or chat. Do not launch the 106-settlement historical batch before one complete async snapshot passes.
- **Options:** OptionMetrics IvyDB TradeFlow remains the primary conditional all-venue signed-flow candidate; Cboe Option Trades remains the independent OPRA trade/NBBO reconstruction candidate; Open-Close is complementary. Licensing, historical-vintage/first-receipt PIT and coverage gates remain unresolved. No trial, purchase, vendor contact or sample acquisition occurred.
- **OCC:** account-type volume and OI remain conditional on explicit authorization/licensing; no automated collection is permitted under the currently reviewed access terms.

## 7. Controls and next gates

1. Wait for the next existing scheduled Form 4 run and verify that `reporting_owners.csv`, the owner-backfill summary and crosswalk artifact are actually produced. Reconcile the Atea examples without interpreting them as predictive signals.
2. Wait for the next naturally scheduled Phase 469 Reg SHO capture after Phase 515; validate real CNMS files before any data eligibility.
3. If FINRA credentials and usage rights are configured, run exactly one Phase 447 settlement validation before considering any historical re-ingestion.
4. Keep options source work at feasibility/licensing level until a lawful sample and PIT/vintage protocol are available.
5. Do not reopen the killed N-PORT share-growth ranking absent a materially different, preregistered hypothesis and improved identity/return data.

No new backtest, event study, OOS test, bootstrap, LOO or production change was run in this phase.

## Frozen baseline

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. Universe, parameters, holding period, exposure, costs, holdout and production are unchanged. Signals admitted: **0**.
