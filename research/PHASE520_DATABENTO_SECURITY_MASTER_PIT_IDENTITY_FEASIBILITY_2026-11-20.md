# Phase 520 — Databento security master PIT identity feasibility update

**Date:** 2026-11-20 UTC  
**Branch:** `phase520-databento-security-master-pit-update`  
**Disposition:** strongest currently documented candidate for the historical listing/identifier bridge; **conditional on an authorized 335-symbol pilot and vendor clarification of record-time semantics**. No API call or purchase was made.

## 1. Why this audit was reopened

Phase 390 previously ranked Databento as the best-documented candidate for a point-in-time public-security reference master, but left history, record-time semantics, universe coverage and licensing/sample gates open. The current official Databento documentation now makes the product scope and API more explicit. This is a documentation update, not evidence that the exact frozen 335-symbol panel has been covered.

The exact 335-ticker research snapshot is the Phase 21C artifact-backed list recovered in Phase 455:
- source commit: `1aa1b91f383ce9cef375a43e775c736a27356a5f`;
- path: `research/phase44_frozen_universe_335_tickers.csv`;
- Git blob SHA-1: `7edbd62b4fb34a6123276e4ce45cb3c1c62479c7`;
- Phase 455 recorded SHA-256: `f850655a22a8843dad90e9562b3152b9ca064560586109022b5bfd205a003dda`.

This is a frozen research snapshot, not a date-appropriate historical active-universe membership table. Phase 44 explicitly requires active/listed status to be determined at each signal knowledge date; an absent historical observation cannot be treated as zero without that gate.

## 2. Official product and API findings

The current product page advertises 21 years of point-in-time history, 860,000+ securities, and 215 venues. The feed guide states history from 2005-01-01 to present, global coverage, weekly updates, and listing-level records. It says the system continues to track delisted/relisted securities.

The Reference API exposes `security_master.get_range` with an `index` parameter supporting both `ts_effective` and `ts_record`. It accepts up to 2,000 symbols per request and supports US-country and security-type filters. Thus the exact 335 snapshot is below the documented single-request symbol limit, before any alias expansion.

The documented record includes:
- `ts_record` and `ts_effective`;
- `listing_id`, `listing_group_id`, `security_id`, `issuer_id`;
- `listing_status`, `listing_source`, `listing_created_date`, `listing_date`, `delisting_date`;
- `symbol`, `nasdaq_symbol`, `local_code`, exchange and MIC fields;
- CIK, CUSIP/US code, ISIN, FIGI and issuer/security classification fields.

Sources:
- Product: https://databento.com/security-master
- API reference: https://databento.com/docs/api-reference-data/security-master?lang=python
- Feed specification: https://databento.com/docs/datasets/security-master

## 3. PIT interpretation — conditional, not yet certified

The API's ability to filter/order by `ts_record` and `ts_effective` is materially better than a current-state-only master. The guide describes the records as PIT, and the sample response shows separate values for the two fields.

However, the public documentation does **not** define `ts_record` as the exact first time the information became publicly available, nor does it state a maximum delay from the upstream event to Databento's record. The guide says the product is updated weekly. Therefore:
- `ts_effective` is the candidate valid-from clock;
- `ts_record` is the candidate record-known clock;
- neither may be promoted to exact public availability without written vendor confirmation and a pilot comparing the two clocks;
- a strategy simulation must not use a record before its verified record-known timestamp;
- weekly update cadence may create a conservative lag and must be measured, not assumed away.

The pilot must retain both clocks, query parameters, retrieval time, response hash and vendor/API version. If vendor confirmation is unavailable, classify the source as historical identity support only, not a fully certified public-information clock.

## 4. Identity continuity and survivorship limits

The guide says each listing has a unique `listing_id`; `security_id` groups listings for the same security. It documents continuity through issuer-name/ticker changes, mergers and demergers. It explicitly says `listing_id`/`security_id` continuity does not apply to spin-offs or securities that are delisted and never relisted.

This makes Databento a strong candidate for:
- effective-dated ticker-to-listing/security mapping;
- CIK/CUSIP/ISIN/FIGI cross-checks for SEC and FINRA records;
- listing/delisting status at historical knowledge dates;
- distinguishing multiple exchange listings from a single security.

It does **not** by itself supply delisting returns, terminal cash/stock consideration, fractional-share cash, or complete corporate-action total returns. Keep the Phase 474/475 corporate-action work and CRSP/other independently licensed price-source gate. CRSP currently advertises daily/monthly history and corporate actions for more than 36,000 active and inactive securities with permanent PERMNO/PERMCO identifiers, but requires subscription access: https://indexes.morningstar.com/research-data-products/crsp-us-stock-databases.

A static 335-symbol list also does not prove that all 335 securities were historically active on each signal date, nor recover the original universe-selection rule. Any FTD, FINRA T1, Form 4/144 or 13D/G panel must distinguish:
1. not yet listed / already delisted;
2. active with no observed source record;
3. active with an observed source record;
4. unresolved identity.

## 5. Commercial and redistribution gate

The product page's sample/pricing section says a Standard plan includes 1,000 symbols and lists $0.50/month for each additional symbol. Its FAQ calls the plan Starter and lists $1.75/month for additional symbols. The same page advertises $125 in new-user credits and permits internal personal/commercial use while prohibiting external redistribution of files or API data.

Because the plan labels and incremental price conflict on the same official page, do not budget from either figure. Obtain a current written quote and confirm the permitted storage/use for a private GitHub repository and any Actions artifacts. Do not upload raw security-master rows or vendor data to public artifacts; the proposed pilot should emit aggregate-only results and keep any licensed raw data in approved private storage.

## 6. Feasibility decision

| Gate | Decision | Reason |
|---|---|---|
| Historical depth | PASS, product-level | 2005-01-01 to present / 21 years advertised |
| PIT fields | CONDITIONAL | Both clocks exposed; `ts_record` semantics/lag not explicitly defined |
| 335-symbol request size | PASS, request-size only | 335 < documented 2,000-symbol limit |
| Exact 335 coverage | NOT TESTED | No authorized API sample or vendor data |
| US venue scope | PASS, product-level | US primary venues include Nasdaq, NYSE, NYSE American, NYSE Arca and Cboe BZX |
| Listing/delisting history | CONDITIONAL | Listing-level and delisted records; no ID continuity for permanent delistings/spin-offs |
| CIK/CUSIP/FIGI/ISIN bridge | CONDITIONAL | Fields documented; exact panel match and identifier quality untested |
| Price/terminal returns | FAIL as standalone | Security master is not a delisting-return/total-return database |
| License/price | NOT VERIFIED | Current plan terminology/price conflict; no subscription |
| Signal/alpha | NOT AUTHORIZED | No data sample, no PIT certification, no return test |

## 7. Next gate — one-shot authorized pilot

Only after an account/plan and internal-use terms are confirmed:
1. place the API key in GitHub Actions secret `DATABENTO_API_KEY` (never in code, logs or chat);
2. run a manual, one-shot audit for the exact 335 Phase 21C tickers, using both `ts_record` and `ts_effective`, US listings and equity-share classifications;
3. measure exact and normalized ticker coverage, missing/ambiguous symbols, number of listings/security IDs per ticker, CIK/CUSIP/FIGI availability, historical record depth, listing/delisting dates and `ts_record - ts_effective` lag distribution;
4. separately test the seven low-coverage/delisted symbols from Phase 473–475 and compare terminal outcomes against an independent source;
5. emit aggregate-only results; do not commit raw licensed rows;
6. only if the identity and record-time gates pass, build the date-appropriate active-universe crosswalk for FINRA T1, SEC FTD and SEC ownership filings.

No vendor account, trial, purchase, API key, API request, raw data download or license acceptance occurred in this phase. No alpha, forward-return, OOS, bootstrap, LOO or holdout test was run. `F80_TOP20_PARTIAL50_BASELINE_C20`, its universe, parameters, exposure, costs and holdout remain unchanged.
