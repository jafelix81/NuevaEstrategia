# Phase 191 — SEC N-PORT registered-fund short exposure: historical coverage and PIT feasibility

**Date:** 2026-11-07  
**Decision:** retain as a distinct conditional public-data hypothesis. Do not call it short interest, hedge-fund positioning or proof of informed trading. No short-equity sample row, historical security crosswalk or alpha test has yet passed.

## 1. Why this is a distinct candidate

The earlier Phase 27O N-PORT work tested a long-side share-accumulation dose-response and was killed in that tested form. Phase 191 identifies a different variable in the current Form N-PORT schema: non-derivative holdings have an explicit long/short payoff-profile field (Item C.3), alongside reported market value and percentage of fund net assets.

The SEC's February 2026 proposal explains that funds generally report positive values for long non-derivative positions and negative values for short positions. For December 2024, it reports 0.0040% of non-derivative long positions with a negative value and 0.0012% of short positions with a positive value. These are classification/value-sign inconsistency rates—not the prevalence of short positions. The proposal is not treated as current law; current Item C.3 is preserved.

This creates a testable registered-fund short-exposure hypothesis, not an assumption that every reporting fund is an institution with informed directional intent.

## 2. Historical coverage and operational scale

The SEC's current public Data Sets page covers **October 2019 through September 2026** and lists **28 quarterly archives**. Published compressed files range from 228.89 MB to 690.83 MB; their listed sizes total approximately **11.38 GB**. The page says the data sets are updated quarterly and was last reviewed September 30, 2026.

The SEC Data Sets Readme says the files are extracted from structured N-PORT XML submissions, contain information as filed, include amendments, include only information from filings disseminated by the Commission, and are published quarterly.

The SEC's March 2026 registered-fund statistics report states that current N-PORT information is public quarterly, that first- and second-month reports in each fund's fiscal quarter are not intended to be public, and that filings are due no later than 60 days after the fiscal quarter. It estimates a complete calendar-quarter picture may not be available until approximately four months after quarter end. The 2024 monthly-reporting amendments were delayed to November 17, 2027 for large fund groups and May 18, 2028 for smaller groups. A February 2026 proposal to change filing/publication rules is treated as a proposal, not current law.

**Interpretation:** this is a multi-year historical source, but not a monthly public tape. The public population is effectively one report month per fund fiscal quarter, with a substantial reporting delay and asynchronous fiscal calendars.

## 3. What the source actually identifies

The official Readme's `FUND_REPORTED_HOLDING` table includes accession and holding identifiers, issuer name and optional CUSIP, balance and unit, U.S.-dollar currency value and percentage of fund net assets, payoff profile (`long`, `short`, `N/A`), asset category, issuer type, investment country and a separate derivative category.

The `IDENTIFIERS` table can carry ISIN, ticker and other identifiers, but these fields are optional. The `FUND_REPORTED_INFO` table carries `SERIES_ID`; the registrant table carries CIK. The portfolio unit must be the fund series, not the registrant CIK or each share class. A public EDGAR filing example for Vanguard Total Stock Market Index Fund shows one series with multiple share classes, so summing class rows as if they were separate portfolios would double-count holdings.

The bulk `SUBMISSION` table includes accession, filing date, subtype and report date, but **does not include an acceptance timestamp**. It also includes NPORT-P/A amendments as separate as-filed submissions. Each accession/version therefore needs an EDGAR acceptance-time join and an append-only version ledger.

## 4. Narrow first hypothesis and field discipline

Start only with direct, non-derivative common-equity shorts:

1. Asset type = equity-common.
2. Issuer type = corporate.
3. Investment country = United States.
4. Item C.3 payoff profile = short.
5. Reported U.S.-dollar value is negative as a consistency check.

Do not classify a short solely from a negative balance, ticker or fund name. Preserve and quarantine disagreements between payoff profile and value sign. Do not include derivative positions in the first direct-short test: Item C.11 has separate payoff-profile and reference-instrument structures, and index/basket/derivative exposure requires a different mapping and notional methodology.

Even the narrow filter does not prove the security is a U.S.-listed ordinary common share. Country is an issuer/investment field, not a substitute for an effective-dated listing/security master. CUSIP, ISIN and ticker are optional, and a current CUSIP-to-FIGI mapping is not a historical crosswalk.

Candidate features, only after sample and PIT gates pass: aggregate direct short market value by issuer; change in short market value between consecutive public reports; breadth of fund series increasing, initiating, reducing or covering shorts; short exposure as a fraction of fund NAV and issuer market capitalization; and concentration/persistence with prior-return, liquidity, volatility and options-flow controls.

A missing row is not automatically a cover: require complete filings for the same series and period, consistent identifiers and valid report continuity. Normalize at series level and avoid share-class duplication.

## 5. PIT ruling

- `REPORT_DATE` is the portfolio measurement date, not the public knowledge date.
- The quarterly bulk data set itself has a later quarterly publication time. If the bulk archive is the strategy's source, its own first receipt controls availability.
- For a filing-level EDGAR reconstruction, join each accession to its SEC-HEADER acceptance timestamp (or equivalent SEC submissions metadata). Acceptance is an availability lower bound, not a captured first-receipt log; until a prospective immutable capture exists, use no earlier than the next full regular trading session.
- Keep the original NPORT-P and every NPORT-P/A version. Apply each amendment only from its own verified availability time. Never overwrite the prior version or backdate amended holdings.
- Because only the third month of each fund's fiscal quarter is intended to be public under the current regime, do not manufacture monthly first/second-month observations from the data set.

The SEC Data Sets Readme says the files are as-filed and include amendments, but its `SUBMISSION` table provides `FILING_DATE`, not acceptance time. Exact first public receipt and amendment dissemination history are therefore not established by the bulk file alone.

## 6. Scope and limitations

N-PORT covers a subset of registered funds, not all institutions. The SEC scope excludes money-market funds, SBICs and BDCs; the filing population also does not represent private hedge funds that do not file N-PORT. It does not identify beneficial owners behind positions. A short position can reflect hedging, relative-value, arbitrage, liquidity management or directional views. A `short` label is not a signal of informed bearishness.

The current public archives establish a documented history floor, but Phase 191 did not download a quarterly archive or parse an actual non-derivative U.S. common-equity short row. It did not measure issuer-level identifier coverage, delisted-name coverage or short-position prevalence. Those remain explicit gates.

## 7. Admission decision and next gate

| Gate | Result |
|---|---|
| Official historical archive and scope | PASS — documentation only |
| Current non-derivative short field semantics | PASS — documentation only |
| Actual direct U.S. common-equity short-row sample | NOT VERIFIED |
| Acceptance-time and amendment version reconstruction | PARTIAL / NOT VERIFIED |
| Series/share-class deduplication | DOCUMENTED, NOT SAMPLED |
| PIT CUSIP/ISIN/security crosswalk | NOT ESTABLISHED |
| Historical active/delisted equity universe | NOT ESTABLISHED |
| Incremental alpha versus frozen LTM/F80 | NOT AUTHORIZED |

Next, retrieve a deterministic, stratified sample of public NPORT-P and NPORT-P/A filings from early, middle and recent archive years. Verify actual short common-equity rows, payoff/value sign agreement, CUSIP/ISIN/ticker completeness, series-level uniqueness, amendment lineage and acceptance timestamps. Only after those checks should a broad quarterly panel be built and aligned to a historical active/inactive security universe.

If the data gates pass, preregister short-exposure changes as a separate hypothesis and test all economically plausible holding horizons. Explicitly distinguish whether fund short changes predict subsequent stock returns or merely follow prior declines. Use identical exposure/cost assumptions against frozen LTM/F80, chronological walk-forward splits, block/cluster bootstrap, leave-one-fund/issuer-out, and a genuinely untouched prospective holdout. Do not tune the existing Phase 27O long-accumulation result to rescue it.

**Controls:** no bulk archive downloaded; no actual short-equity row parsed; no forward returns, alpha test, bootstrap/LOO, holdout use, production change, purchase or vendor contact. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Official sources

- SEC Form N-PORT Data Sets: https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets
- SEC N-PORT Data Sets Readme: https://www.sec.gov/files/nport_readme.pdf
- SEC Registered Fund Statistics, March 2026: https://www.sec.gov/files/im-investment-registered-fund-statistics-202603.pdf
- SEC April 2025 final rule delaying Form N-PORT monthly-reporting amendments: https://www.sec.gov/rules-regulations/2025/04/s7-26-22
- SEC February 2026 proposed Form N-PORT amendments: https://www.sec.gov/files/rules/proposed/2026/ic-35962.pdf
- SEC Form N-PORT: https://www.sec.gov/about/forms/formn-port.pdf
- SEC EDGAR example, Vanguard Total Stock Market Index Fund, accession 0000036405-26-000323: https://www.sec.gov/Archives/edgar/data/36405/0000036405-26-000323-index.htm
