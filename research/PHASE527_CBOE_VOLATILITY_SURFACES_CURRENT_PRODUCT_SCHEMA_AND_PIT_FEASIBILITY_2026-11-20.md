# Phase 527 — Cboe Volatility Surfaces current-product, schema and PIT feasibility update

**Audit date:** 2026-11-20 UTC  
**Main HEAD at preflight:** `88edc94d6a960668361142774f964108d8ae399d`  
**Disposition:** **CONDITIONAL HISTORICAL IV / VOLATILITY-RISK-STATE CANDIDATE; NOT STRICT-PIT, UNIVERSE-COVERAGE, LICENSE OR ALPHA ADMITTED.** This is a risk/volatility information source, not a smart-money identity feed.

## 1. Repository and Actions preflight

Before this audit:
- Inspected the latest 100 of 7,964 Actions runs, their current statuses, the first 100 branches, all returned open PRs, current main commit history, research tree, and relevant SEC/FINRA/CFTC workflow files.
- Main HEAD: `88edc94d6a960668361142774f964108d8ae399d` (Phase 526 N-PORT signal disposition).
- Latest Actions run at preflight: [44728717197](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44728717197), a successful PR check on the Phase 525 report-count branch; it was not a live capture.
- Zero active, queued, waiting, requested or in-progress runs were returned.
- PRs #180–#183 are merged. Drafts #170, #171, #159, #164, #165, #166 and #167 remain open; they were not changed.
- Latest scheduled SEC runs remain pre-Phase-525-merge: Form 4 [44716430351](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44716430351) and Form 144 [44720422923](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44720422923). Form 4's latest run captured 33 new accessions, parsed 10 documents into 37 detail rows (27 transaction rows), had zero parser errors, and left 1,213 bounded accessions. Form 144 captured 52 feed-observation rows, parsed 10 documents into 64 detail rows, had zero parser/hash errors, and left 358 accessions. Neither run exercised the Phase 525 owner-sidecar/crosswalk steps because both preceded the merge.
- The current Form 4 workflow now includes scheduled reporting-owner backfill and descriptive Form 144/Form 4 crosswalk steps. `reporting_owners.csv` is not yet present on main; the next existing schedule is the live integration gate. No manual dispatch or duplicate capture was made.
- FINRA Reg SHO's latest live run [44669121290](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44669121290) predates Phase 515: 8 HTTP 200 files, 8 invalid, 0 valid, 0 eligible. Post-Phase-515 live validation remains pending.
- CFTC TFF [44668300202](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44668300202) retained 3,039 rows and found no new report or revision; historical archive rows remain ineligible under the existing PIT ruling.

No workflow was dispatched, rerun, cancelled or duplicated.

## 2. Current official product status and historical coverage

Cboe DataShop currently lists **Volatility Surfaces** as an orderable product with both historical and subscription purchase paths:
- Product page: https://datashop.cboe.com/volatility-surfaces
- Current file specification: https://datashop.cboe.com/documents/VolatilitySurfacesSpecifications%20(1).pdf
- General DataShop delivery FAQ: https://datashop.cboe.com/faqs
- DataShop contracts and policies: https://datashop.cboe.com/data-policies

The current product page states:
- Start-of-day snapshot at **09:40 ET**.
- End-of-day snapshots at **15:45 ET** and **16:00 ET**; a **16:15 ET** snapshot is available only for indices that trade through that time.
- Four surface products: constant-maturity delta-relative, constant-maturity price-relative, expiration-specific delta-relative and expiration-specific price-relative.
- Daily subscription files and historical daily files, with advertised history from **August 2011**.

This is a materially stronger current orderability/advertised-history indication than the legacy/unlisted Option Sentiment catalog entry. It does not prove that every date or every F80 security is available. The purchase page explicitly warns that some selected dates or symbols may be unavailable and exposes an excluded-symbol/date list. That list must be captured and reconciled before any order or feature panel is approved.

## 3. Schema audit from the current v1.0 specification (April 2025)

Each trading day is delivered as one ZIP containing four CSV files. The schema is surface-point based rather than raw option-trade based.

Key fields include:
- `underlying_symbol`;
- `expiry` for expiration-specific files or `maturity` for constant-maturity files;
- calculation `timestamp` in HH:MM:SS.sss;
- `underlying_price` (zero for indices);
- interpolated implied-volatility nodes;
- corresponding strike nodes;
- weighted confidence values for each interpolated volatility node.

The price-relative surface includes points from 50% to 150% of underlying price, with denser coverage around the money. The delta-relative surface includes 5–95 delta nodes. The files provide enough structure to investigate level, wing shape and term structure without reconstructing every contract from raw OPRA prints.

### Confidence and extrapolation are not optional metadata

The specification defines confidence on [0,1] and gives the following warning: values below 0.5 should be treated with suspicion. Negative codes identify surface extrapolation or flat-lining:
- -1: higher skew unavailable; lower skew used for extrapolation;
- -2: lower skew unavailable; higher skew used for extrapolation;
- -5: surface flat-lined from the left;
- -6: surface flat-lined from the right.

These values must remain explicit quality states. Do not coerce negative codes to zero, interpolate through them, or silently treat low-confidence points as valid observations. A primary feature panel should require pre-registered confidence/quality rules and report the retained denominator by symbol/date/node.

The specification says surfaces are interpolated from listed-option mid-volatility. The data are model-derived market-state summaries, not actual signed trades, investor identities, or proof of informed positioning.

## 4. Delivery clock and historical PIT ruling

The DataShop FAQ says daily equity/option files for trade date T are typically delivered by SFTP on the following day between 00:05 and 03:00 ET, but explicitly warns that delays can cause the prior day's file to arrive during the following session after the market opens.

This is a **general DataShop daily-file statement**, not a product-specific hard SLA for Volatility Surfaces. The surface file's internal calculation timestamp (09:40/15:45/16:00/16:15) is an event/calculation time, not proof of when a recipient could first use the file.

Therefore:
1. For any future subscription, record actual first successful SFTP receipt UTC, remote path/filename, remote size/mtime where exposed, local bytes, SHA-256, schema version, parse status and every later replacement/revision as a separate immutable event.
2. Use actual receipt as the feature-availability clock. Do not backdate a feature to 15:45/16:00 or assume that a nominal overnight target guarantees pre-open availability.
3. Execute at the first regular-session price strictly after actual receipt and any required validation/processing latency. If the file arrives after the open, the next eligible session is later.
4. Historical archives from 2011 are backfill, not historical first-delivery vintages. Without vendor-provided original receipt/vintage or correction records, historical strict PIT is **not certified**.
5. Preserve 09:40 and EOD snapshots as separate source observations. Do not use the 16:15 index-only snapshot as if it existed for single-name equities.

## 5. Universe, identity, licensing and sample gates

| Gate | Current evidence | Disposition |
|---|---|---|
| Advertised history | August 2011 onward | Pass for advertised product history only |
| Current orderability | Current product page has historical and subscription purchase paths | Conditional |
| Exact F80 335-name coverage | Purchase UI warns that selected symbols/dates may be unavailable; no full matrix captured | Fail closed |
| Inactive/delisted coverage | Not demonstrated | Fail closed |
| Security identity | Surface rows key by underlying symbol; no effective-dated CUSIP/FIGI crosswalk in this product | Fail closed |
| Historical first-delivery vintages | Not documented | Fail closed for strict historical PIT |
| Corrections/replacements | No complete product-specific vintage policy verified | Fail closed pending vendor confirmation |
| Current price / internal business-use rights | Purchase flow includes an Internal Usage selector, but no price/terms quote was obtained | Human/vendor authorization required |
| Sample | Product page exposes a sample link; the web retrieval interface rejected the ZIP content type, so no sample bytes/schema execution were obtained | Not sample-validated |

No purchase, vendor contact, sample-byte acquisition, credential creation or automated collector was attempted. Do not infer that an advertised history start equals complete symbol coverage or that a public sample grants commercial-use rights.

Before any purchase, obtain written confirmation of internal business/research use, storage/retention of raw and derived data, permitted model use, and any redistribution restrictions. No cost is assumed in this audit.

## 6. Research role and preregistered hypotheses

**Role:** conditional daily volatility-surface / risk-state information. It is not a participant-flow or smart-money proxy. It may have value by forecasting realized volatility, downside tail risk, drawdown or risk-state transitions even if it has no standalone directional-return alpha.

If licensing, sample, identity, coverage and prospective PIT gates pass, keep the first test small and preregistered:

1. **ATM level / volatility state:** changes in constant-maturity near-ATM IV (e.g. 30D and 90D) and short/long term-structure slope; outcomes should include forward realized volatility and downside risk separately from returns.
2. **Wing asymmetry:** price-relative 90% versus 110% IV (or delta-relative wings only after the vendor confirms put/call and delta-sign conventions). Treat this as an option-implied risk premium, not a directional investor-flow measure.
3. **Surface repricing:** change from the 09:40 snapshot to 15:45/16:00 on the same trade date. Use it only after actual file receipt; test whether it forecasts subsequent, not contemporaneous, outcomes.
4. **Confidence-aware quality:** use confidence and negative extrapolation/flat-line codes as validity/quality controls. Do not optimize confidence thresholds against the final holdout.
5. **Conditional risk control:** test whether surface state adds risk information beyond prior realized volatility, momentum, liquidity, earnings/event windows, sector/market moves and frozen LTM/F80. Evaluate portfolio risk and drawdown effects separately from directional stock selection.

All rolling baselines must use prior observations only. Distinguish repricing that follows the underlying's same-day return from forward information. No feature may use a surface timestamp before the actual receipt/validation clock.

## 7. Required next gates

1. Obtain a lawful sample or small authorized order covering old/new dates, liquid and less-liquid F80 names, and inactive/acquired cases where available; preserve the vendor's excluded-symbol/date list.
2. Reconcile symbol/date coverage against the effective-dated F80 universe and a separate historical security master; unknown identity remains unknown.
3. Validate all four CSV schemas, timestamps, confidence codes, missing/zero semantics, duplicate keys and corporate-action/adjusted-contract behavior.
4. Obtain written internal-use/license terms and a price quote before any order or subscription.
5. Start a prospective first-receipt ledger before treating subscription files as tradable.
6. Only after those gates pass, compare a small preregistered set of surface features against frozen LTM/F80 with identical universe, exposure, turnover and costs; use chronological discovery/validation/OOS, block bootstrap, LOO, multiple-testing control and the untouched holdout.

## 8. Final disposition

- **Retain:** Cboe Volatility Surfaces as a conditional historical IV / risk-state candidate.
- **Do not label:** smart money, institutional flow, or signed directional demand.
- **Strict historical PIT:** not certified.
- **F80 335-name / inactive-security coverage:** not verified.
- **Sample execution:** not completed.
- **Vendor license / cost:** unresolved.
- **Signals admitted:** 0.
- **Backtests, event studies, OOS, bootstrap and LOO:** 0.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No production, exposure, cost, parameter, universe or holdout changes.

Phase 527 is a source-feasibility update only. It does not authorize a purchase or a predictive test.
