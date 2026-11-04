# Phase 54 — Cboe Open-Close EOD sample results
Date: 2026-11-04

## Execution
- Run: [41762583602](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41762583602)
- Job: 126353459116 — success.
- Artifact: 13291147097 — `phase54-cboe-open-close-eod-sample`.
- Parser tests: PASS.
- Public sample ZIP downloaded and parsed successfully.

## Sample findings

The ZIP contains three distinct samples: 10-minute, 1-minute and EOD. The EOD schema gate was correctly applied only to the EOD file; intraday schemas were retained separately and did not contaminate the EOD gate.

| Metric | EOD sample |
|---|---:|
| Exchange | C1 |
| Trade date | 2025-03-28 |
| Sample fraction | 20% |
| Contract rows | 23,179 |
| Frozen-335 tickers observed | 288 |
| Exact ticker coverage | 85.97% |
| Required EOD/participant fields present | 100% |
| Non-null rate for each required field | 100% |
| Rows with nonzero participant activity in parsed categories | 100% |

Required fields include underlying, quote date, expiration, strike, call/put, total exchange volume, OI/previous OI, and participant-specific buy/sell/open/close volumes. The sample includes Firm, Broker/Dealer, Market Maker, Customer and Professional Customer categories, with customer/pro-customer size buckets.

The sample's `total_exchange_vol / total_industry_vol` ratio had median 0.5 and 90th percentile 2.0. This is not accepted as a market-share estimate: Cboe documents historical convention changes and third-party best-effort total-industry volume. Reconcile units and conventions before using this field.

## Research interpretation

This is a meaningful data-feasibility pass, not an alpha result. The sample demonstrates a usable EOD schema and broad ticker reach in a 20% C1 sample. It does not establish full-market coverage or historical availability for every frozen ticker.

The product covers Cboe exchanges BZX, C1, C2 and EDGX, not all OPRA. C1 EOD history begins 2005-01-03; BZX/C2/EDGX begins 2018-01-02. EOD files are delivered overnight after midnight US Eastern; use the next trading session as conservative KnowledgeDate.

Cboe documents OI conventions that must be handled: C1 values were shifted one day ahead through 2019-10-04; C2 through 2018-05-11. C2 total industry volume was doubled through 2018-05-11. The 2025 sample is outside those OI convention windows.

Participant labels are exchange capacity categories, not proof of informed trading. In particular, Customer includes retail and institutional clients; Professional Customer includes professional traders and institutional participants. Firm is proprietary trading capacity. These are hypotheses to test, not investor identities.

## Cost and licensing

The official April 21, 2026 Cboe fee schedule lists EOD Open-Close historical pricing of $600 per month of history for 1–4 years and $300 per month of history for 5+ years, with daily updates listed at $600/month. It also lists a first-time free trial of up to six months, subject to eligibility. The total for a 335-symbol pick-list and multi-year order must be confirmed with Cboe/DataShop. Raw data is licensed for internal use; external redistribution of derived data requires additional approval/licensing.

## Decision

- PASS: public sample schema and initial target-ticker reach.
- CONDITIONAL: full 335-ticker coverage, exchange share, pricing, trial eligibility, PIT delivery, and historical option-root mapping.
- Next complementary source: Option EOD Summary (full OPRA, Jan 2012 onward, optional 15:45 IV/Greeks) for quotes/OI/volatility, joined to Open-Close EOD for Cboe participant flow.
- No forward returns or alpha tests.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
