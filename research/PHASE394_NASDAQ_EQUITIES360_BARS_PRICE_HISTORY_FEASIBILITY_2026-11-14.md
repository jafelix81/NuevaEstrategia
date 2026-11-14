# Phase 394 — official Nasdaq Data Link Equities 360 / Bars feasibility audit

**Audit date:** 2026-11-14 UTC  
**Disposition:** conditional paid historical-price candidate; no sample, account, trial, API key, quote, or purchase. No Phase 20C price fallback admitted.

## 1. Why this phase follows Phase 393

Phase 393's corrected public `api.nasdaq.com/api/quote/{symbol}/historical` request returned 2,499 rows for AAPL/MSFT/NVDA but zero rows and application-level `Symbol not exists` errors for all seven unresolved Phase 20C names (AVB, EA, EQR, LPRO, ROKU, WBD, WBS). SPY was an invalid stock-class control. The public quote-history route is closed as a fallback candidate; do not repeat it.

This phase evaluates a different official product family: Nasdaq Data Link Equities 360 and its Bars/Charting API. It is a documentation-only feasibility screen, not a live data test.

## 2. Official product evidence

Nasdaq Data Link's Equities 360 product page describes:
- Premium / custom API access.
- 16,000+ U.S. companies.
- Coverage across Nasdaq, NYSE, NYSE American and other regional listings.
- Pricing data, company/reference data, corporate actions and analytics.
- Overall product history shown as January 1998.

The product page's data organization separately describes Bars/Charting (table family `NDAQ/BAR`) as intraday/daily pricing with historical coverage since 2008. Nasdaq's general Data Link API overview also describes Bars for all U.S.-listed and OTCBB securities with 10+ years of OHLCV history.

Important scope distinction: the Equities 360 page's January 1998 history is the overall product history, not a demonstrated January 1998 start for every price field. The price-specific Bars start advertised in the product documentation is 2008.

Official sources:
- Equities 360 product and specifications: https://data.nasdaq.com/databases/E360
- Nasdaq Data Link API overview / Bars: https://www.nasdaq.com/es-es/products/data/data-link/api
- Nasdaq Basic product scope (context only; not the same historical product): https://www.nasdaq.com/products/data/equities/nasdaq-basic

## 3. Feasibility assessment

| Gate | Evidence | Status |
|---|---|---|
| U.S. exchange breadth | Nasdaq, NYSE, NYSE American and regional listings stated | Candidate pass; exact seven-name coverage untested |
| Historical depth | Bars advertised since 2008 | Candidate pass for 2016–2026 window |
| Price fields | OHLCV / charting | Candidate pass |
| Corporate actions | Included in Equities 360 product description | Candidate; field-level adjustment policy unverified |
| Inactive/delisted securities | No explicit guarantee found in reviewed product page | FAIL / unknown |
| Effective-dated listing/security identity | All Symbols / Symbol Details described, but no two-clock vintage guarantee found | FAIL / unknown |
| Record-known point-in-time history | No record-known / first-delivery / correction-vintage ledger documented | FAIL / unknown |
| Exact seven-symbol coverage | No authenticated sample or API response | Unknown |
| Commercial use / redistribution | Premium custom API; exact license not publicly established | Human/vendor confirmation required |
| Price | Premium; login required to view pricing | Unknown; no quote obtained |

## 4. Disposition

Equities 360 / Bars is a materially more credible next price-history candidate than the public quote endpoint because Nasdaq explicitly describes broad U.S. exchange coverage and Bars history from 2008. It is not yet a valid Phase 20C fallback.

Do not assume:
- the 16,000+ company count includes inactive/delisted securities;
- current All Symbols is a historical security master;
- the January 1998 overall product history applies to Bars;
- corporate-action fields guarantee reproducible total-return adjustments;
- a Bars response establishes record-known point-in-time identity.

No sample, account, trial, API key, vendor contact, purchase or price quote was used. No raw prices, forward returns, alpha, OOS, bootstrap, LOO or holdout test was run.

## 5. Minimum sample gate before any price use

If a lawful trial or sample is later obtained, test only the seven unresolved names plus at least four positive controls and two known inactive/delisted controls before scaling to the 335-name diagnostic universe.

Require:
1. At least 220 valid daily observations per target over its listing-appropriate interval, with explicit IPO/listing start and terminal/delisting handling.
2. Coverage report for every name, including exchange, listing identifier, share class, effective dates and inactive status.
3. Independent adjusted/unadjusted OHLCV reconciliation against a second source; dividends, splits, symbol changes and spinoffs must be explicit.
4. Security identity must be effective-dated; if the provider cannot show record-known history, it may support retrospective price diagnostics but not strict PIT security-master joins.
5. Daily file first-receipt timestamps, revisions/corrections and immutable hashes must be captured prospectively.
6. Business-use rights and data retention/redistribution limits must be documented.
7. The fixed Phase 20C universe and original window must remain unchanged. Do not drop symbols, impute missing prices or splice providers to force 329/329.

Only after these gates pass can Phase 20C's existing price-history block be reconsidered. Price data feasibility alone does not authorize a FINRA short-flow/short-interest return test; the FINRA signal's own PIT, security identity and OOS gates remain separate.

## 6. Frozen controls

- `F80_TOP20_PARTIAL50_BASELINE_C20`: unchanged and frozen.
- Phase 20C: remains blocked at its existing 328/329 valid price-history gate.
- No fallback accepted; no universe or ticker changes.
- No capital, exposure, production or parameter changes.
- No legacy holdout use.
