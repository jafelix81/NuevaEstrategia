# Phase 504 — Cboe Volatility Surfaces, Complex Order Flow and Option Sentiment catalog-status audit

**Date:** 2026-11-19 UTC  
**Branch:** `phase504-cboe-volatility-surfaces-complex-flow-audit`  
**Baseline main:** `9bb95604c1fb4ebe433dbccf1932c29918fcb731`  
**Disposition:** **Volatility Surfaces promoted to a conditional historical IV/skew candidate; Complex Order Flow retained as a prospective-only hedge/carry diagnostic; Option Sentiment downgraded to legacy/unlisted until current orderability is confirmed. No source is PIT- or alpha-admitted.**

## 1. Repository / Actions preflight

Before this audit, reviewed main, the latest 50 of 7,894 Actions runs, run-specific jobs/logs/artifacts for the latest relevant runs, the first 100 branches, all 56 open PRs, recent commits, and the Phase 501–503 research files.

- Main HEAD at preflight: `9bb95604c1fb4ebe433dbccf1932c29918fcb731`.
- PR #157 (Phases 501–503) is merged at `190211d58fcd6519abef7acf9c475fef267e6ad0`; the final main state addendum commit is `9bb95604c1fb4ebe433dbccf1932c29918fcb731`.
- The latest 50 Actions runs were all completed at the final recheck; no queued or in-progress run was present. No workflow was started or duplicated.
- Latest Phase 500 PR run [44534689780](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44534689780): offline regression succeeded (46 tests); live-capture was skipped; no artifact was produced.
- Latest scheduled Form 144 run [44521745535](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44521745535) was partial: zero events written; Form 144 returned 3,292 bytes with a ParseError; 144/A returned an empty 29-byte page, did not contain its prior watermark and remained a possible feed-window gap. This run predates Phase 500's diagnostic integration.
- Latest Form 4 capture [44505739718](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44505739718) succeeded and uploaded compact artifact 14519048458; prior Phase 497 adjudication recorded 18 new canonical events, but no signal-eligible events.
- Latest inspected FINRA Reg SHO capture [44453548570](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44453548570) predates Phase 495. Its eight HTTP-200 files were all rejected by the old parser; this is not a live validation of the corrected facility-grain parser.
- Latest inspected CFTC TFF capture [44453066854](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44453066854) passed 17 tests, retained 3,039 rows and found no new reports or revisions.
- Relevant existing drafts remain open: PR #44 (Phase 357 Cboe metadata/PIT reconciliation) and PR #48 (Phase 373 Cboe source ranking). PR #48 ranks IvyDB TradeFlow as the primary conditional all-venue signed-flow candidate; this audit does not silently supersede that unmerged draft.

The 22:25 UTC CFTC and 22:30/23:30 UTC FINRA schedule windows had not yet run at the time of this audit. No manual capture was dispatched.

## 2. New current product: Cboe Volatility Surfaces

Official current product page: https://datashop.cboe.com/volatility-surfaces  
Official specification v1.0 (04/2025): https://datashop.cboe.com/documents/VolatilitySurfacesSpecifications%20(1).pdf

The current DataShop product page exposes both historical and subscription purchase workflows. It states historical availability from **August 2011**, with one zipped CSV per trading day containing four files:

1. Expiration-specific delta-relative surface.
2. Expiration-specific price-relative surface.
3. Constant-maturity delta-relative surface.
4. Constant-maturity price-relative surface.

The product describes start-of-day snapshots at **09:40 ET** and end-of-day snapshots at **15:45 ET and 16:00 ET**. A 16:15 ET snapshot is available only for indices that trade through 16:15 ET. Each row includes a calculation timestamp (HH:MM:SS.sss), underlying symbol, expiry or constant maturity, and the surface grid.

### Surface detail and quality fields

- Delta-relative grids cover nominal delta points from 5 to 95.
- Price-relative grids cover 50% through 150% of the underlying price.
- Both constant-maturity and listed-expiry views are available.
- Each volatility point has a weighted-confidence field.
- The specification says the surfaces are interpolated from the listed-options **mid-volatility surface**. These are model/interpolation outputs, not executed trades and not a raw NBBO or order-book feed.
- Confidence is a data-quality statistic related to the number of mid-vegas spanned by the bid/ask spread; it is not a probability of correctness. The specification maps approximately 0.97 to 1 vega, 0.93 to 2, 0.87 to 4, 0.74 to 8 and 0.51 to 16 vegas. Values below 0.5 warrant strong suspicion. Negative codes (-1, -2, -5, -6) indicate extrapolation or flat-lining conditions and must not be treated as ordinary confidence values.
- For indices, underlying price is excluded/zero in the specification; those rows need a separate underlying-price source and must not be treated as ordinary stock rows.

This is a meaningful improvement over Option Sentiment for **current product orderability and historical IV-surface feasibility**: the product page is live, includes a historical purchase path, and documents an August 2011 start. It is not a signed-flow or participant-identity source.

### Availability limits

The DataShop purchase page warns that some selected symbols/dates may be unavailable and will be excluded from the order. Therefore:
- “Historical from August 2011” is a product-level start claim, not proof of complete coverage for every symbol/date.
- No 335-name frozen-universe coverage census, delisted-underlying census, or date-gap map has been run.
- The product page and public specification do not guarantee continuous coverage for all inactive/acquired names or historical share classes.
- No price, internal-use license, derived-data retention terms or redistribution rights have been confirmed.
- The public sample link was visible, but the ZIP could not be retrieved through either the web retrieval path (unsupported ZIP content type) or the runtime download path. No sample bytes or parser/schema execution test are claimed.

### PIT ruling

The product is delivered as a daily end-of-day file. The general DataShop FAQ says daily equity/option files are typically uploaded the following day between 00:05 and 03:00 ET, but delays can push delivery until after the next market open. The Volatility Surfaces product page does not publish a hard maximum delay or a per-file historical first-receipt ledger.

Consequences:
- The 09:40 and 15:45/16:00 timestamps are **calculation times**, not vendor-availability times.
- Even the 09:40 surface is only usable after the daily file containing it has actually arrived and passed validation.
- A prospective subscription must record actual first receipt UTC, remote filename/metadata, byte count, SHA-256, schema version, parse status, and any replacement/correction lineage.
- Historical archive files do not prove when that version was originally available. Strict historical PIT remains **not certified**.
- In any future prospective simulation, the decision time is actual receipt; execution is the first executable underlying price strictly after receipt. Do not backdate to 09:40, 15:45 or 16:00.

## 3. Complex Order Flow: valuable context, but prospective-only

Official product page: https://datashop.cboe.com/complex-order-flow  
Official specification v1.0: https://datashop.cboe.com/documents/Complex_Order_Flow_Specifications_v1.0.pdf

The current page describes five daily strategy files:
- Reversal conversions (RevCon).
- Box spreads.
- Jelly rolls.
- Tied outright option/stock executions.
- Tied option spreads with stock executions.

The specification describes OPRA option legs plus CTA/UTP consolidated equity legs and both RTH and GTH executions. Fields include trade date, underlying, option execution time, exchange, strategy price/rate, option roots/expiries/strikes/types/sizes/prices/theoretical prices/deltas and paired stock execution size/price/exchange where applicable.

Economic interpretation:
- RevCons, boxes and jelly rolls primarily encode financing, carry, lending/borrowing or synthetic-forward relationships.
- Tied outright/spread records identify stock executions linked to option legs, often structured to offset or neutralize delta.
- These are not automatically directional bets, informed purchases or beneficial-owner identities. A large tied trade may be hedging; a box may be financing rather than a view on the underlying.

**Historical gate:** the current product page shows a subscription workflow and daily delivery but does not publish a historical start date or a historical purchase option. Do not assume an archive exists. Until Cboe confirms historical backfill, treat this as a **prospective-only auxiliary source**. It may eventually help distinguish directional option activity from hedged/financing structures or serve as a carry/borrow diagnostic, but it cannot currently support a historical OOS test from public documentation alone.

No price, license, maximum delivery delay, correction policy or actual first-receipt vintage history has been established.

## 4. Option Sentiment status correction

Official references:
- Specification v1.4 (marked 0525): https://datashop.cboe.com/Documents/Cboe_OptionSentiment_Specs.pdf
- DataShop FAQ: https://datashop.cboe.com/faqs
- Options catalog pages 1–3: https://datashop.cboe.com/options

The FAQ still lists Option Sentiment with a January 2012 start, and the archived v1.4 specification describes 80 daily underlying-level fields. However, as of this audit:
- the dedicated `/option-sentiment` URL redirects to the DataShop home page;
- Option Sentiment is absent from all three current Options catalog pages;
- no current product-specific purchase page or orderability path could be verified.

Therefore Phase 503's “high-priority conditional candidate” must now be read more narrowly: **the schema is documented, but the product appears unlisted/legacy and active orderability is unverified**. Downgrade it to **LEGACY / ORDERABILITY UNCONFIRMED** until Cboe confirms it is still sold or has been renamed/replaced. Do not plan a purchase or parser around it yet.

The semantic cautions in Phase 503 remain:
- net delta uses midpoint-based initiating-side classification; spreads, late and tied trades are excluded from that calculation;
- OCC customer/firm/market-maker fields are unsigned participant-volume aggregates, not participant-by-side net flow;
- “customer” is not synonymous with retail, and “firm” is not proof of informed/institutional buying;
- vendor 20-day averages have an unspecified inclusion cutoff; recompute prior-only baselines if the product is ever obtained.

## 5. Updated Cboe options source ranking

| Source | Research role | Current disposition |
|---|---|---|
| IvyDB TradeFlow | Conditional all-venue signed-flow hypothesis | Primary conditional flow candidate per draft PR #48; 2016 archive is backfill after 2026 launch, so PIT/version/sample/licensing gates remain |
| Cboe Volatility Surfaces | IV level, skew, term structure, surface repricing and risk-state features | **New conditional historical candidate**; Aug 2011 product start, but coverage and historical PIT not certified |
| Cboe Option Trades + Quotes | Independent OPRA-wide trade/NBBO reconstruction and quote/OI context | Conditional validation source; date-start conflict, corrections, PIT and coverage gates remain |
| Cboe Open-Close | Capacity × side × open/close on Cboe venues | Complementary, venue-limited; historical convention and vintage gates remain |
| Enhanced TBT | Trade-by-trade side/open-close/capacity | C1-only, costly, and not a full OPRA substitute |
| Complex Order Flow | Complex/hedged/financing structure and tied stock-option context | Prospective-only until historical backfill is confirmed |
| Option Sentiment | Daily aggregate flow/volatility schema | Legacy/unlisted; active orderability unconfirmed |

Volatility Surfaces should be evaluated as a **risk/volatility-state and possible conditional-predictor source**, not called smart money. TradeFlow remains the signed-flow candidate; Volatility Surfaces can test a different information family and may be useful even if it predicts forward volatility/drawdown rather than direction.

## 6. Preregistered hypotheses if the data gates pass

1. **Surface repricing:** changes from the 09:40 to 15:45 surface in the same trade date, measured only after actual file receipt, predict subsequent realized volatility, downside tail risk or returns.
2. **Wing asymmetry:** price-relative OTM put/call wing differences (for example, 90% versus 110% moneyness) or delta-relative skew may predict future downside/volatility. Confirm the provider's delta sign/put-call mapping before constructing a standardized 25-delta skew; do not infer it from field names alone.
3. **Term structure:** constant-maturity short-versus-long IV slope and curvature may forecast forward realized volatility or drawdown, separately from directional returns.
4. **Confidence-aware surfaces:** use the supplied confidence fields as quality/missingness controls or continuous weights; quarantine extrapolated/flat-lined points and test sensitivity to confidence thresholds fixed before return inspection.
5. **Incremental value:** test surface features beyond frozen LTM/F80, same-day return/momentum, realized volatility, liquidity, sector/market moves and known earnings/event windows. Distinguish contemporaneous repricing/return-chasing from forward prediction.
6. **Complex-flow control:** if a historical archive is confirmed, test whether RevCon/box/jelly-roll and tied-stock activity help identify hedged/financing flow or improve classification of directional flow. Do not treat strategy counts as directional alpha.

Evaluate directional-return prediction separately from volatility/risk-state prediction. A source may improve risk-adjusted returns through exposure control without having positive standalone directional alpha.

## 7. Required gates before any test

1. Obtain written price, business/internal-use rights, derived-data retention and redistribution terms for Volatility Surfaces; no contact or quote request was made.
2. Obtain a lawful sample or small authorized date/symbol order and validate the four CSV schemas, row keys, timestamps, nulls, confidence codes and duplicate handling.
3. Run a symbol/date availability census for the frozen 335-name universe, including inactive/delisted names and effective-dated share-class/ticker mappings.
4. Confirm delta sign/put-call mapping, constant-maturity conventions, underlying-price source, confidence semantics and handling of corporate actions/adjusted contracts.
5. Confirm daily file delivery schedule, maximum delay, SFTP metadata, missed-file recovery and correction/replacement lineage; then start a prospective first-receipt ledger.
6. For Complex Order Flow, first confirm whether historical backfill exists, its start date, price, license, corrections and delivery timing. Otherwise keep it prospective-only.
7. For Option Sentiment, obtain explicit confirmation of current product status or replacement product before further work.

Only after coverage, identity, licensing and timing gates pass should features be built. Use actual receipt time, strict chronological discovery/validation/OOS, identical universe/exposure/turnover/costs versus LTM/F80, block bootstrap, LOO, multiplicity control and an untouched holdout.

## 8. Decision and frozen controls

- Volatility Surfaces: **conditional candidate for historical IV/risk-state research; not admitted**.
- Complex Order Flow: **prospective-only auxiliary candidate pending historical-backfill confirmation**.
- Option Sentiment: **legacy/unlisted; orderability unconfirmed**.
- No sample bytes, vendor contact, quote request, purchase, parser, feature, backtest, event study, OOS, bootstrap, LOO or signal admission.
- New signals admitted: **0**.
- `F80_TOP20_PARTIAL50_BASELINE_C20`: unchanged and frozen; universe, parameters, exposure, costs, holdout and production unchanged.
