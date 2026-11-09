# Phase 219 — SEC N-PORT direct-short exposure-change hypothesis preregistration

**Audit date:** 2026-11-08  
**Status:** `DISTINCT_SHORT_SIDE_HYPOTHESIS_PREREGISTERED_NO_ALPHA`  
**Scope:** hypothesis separation, measurement specification and admission gates only. No new SEC downloads, return tests, holdout use or production changes.

## Executive decision

A new N-PORT hypothesis is worth preserving, but it is **not** a continuation or rescue of the killed Phase 27N/27O long-accumulation experiment.

The old Phase 27N implementation explicitly admitted only `PAYOFF_PROFILE` blank/LONG rows and rejected negative `CURRENCY_VALUE`; Phase 27O reused that same long-share-accumulation signal. It did not test direct short-payoff positions. Phase 27O's six-period long-side dose-response remains killed and must not be retuned.

The distinct candidate is:

> Do changes in registered-fund series' explicitly reported, non-derivative U.S. common-equity short exposure contain negative forward-return information after the filing becomes public, beyond lagged price/volatility/liquidity controls and frozen LTM/F80?

This is a hypothesis about **registered-fund-reported short exposure**, not hedge-fund positions, beneficial-owner identity, public short interest, securities-borrow demand, or necessarily directional conviction. Shorts can be hedges, relative-value legs, arbitrage or portfolio risk management.

## 1. Evidence boundary and non-duplication

- Phase 27N/27N2/27O filtered holdings to `PAYOFF_PROFILE` in blank/LONG and non-negative value/balance. Short-payoff rows were excluded by construction.
- Phase 27O tested the long share-accumulation dose-response over six annual formation periods (2020Q4–2025Q4). Top-minus-bottom results had unstable signs; the implementation was killed. Do not reuse its result as evidence for or against the new short-side construct.
- Phase 191 establishes 28 quarterly SEC bulk archives from 2019Q4 through 2026Q3, but does not admit a broad PIT universe.
- Phase 192 is purposive search-index discovery across five accessions, not a representative prevalence sample.
- Phase 193 attempted raw retrieval of five accessions but supplied an empty `SEC_CONTACT_EMAIL` secret, sent zero SEC requests and downloaded zero bytes. This was not an SEC denial.
- Phase 217 inspected one complete SEC submission text and selected 23 direct-short common-equity rows. The complete raw submission and primary XML were not downloaded and hashed; 23 is a selected evidence sample, not an exhaustive filing parse.
- Phase 218 distinguishes direct short payoff positions from fund-reported loaned-out holdings. The borrower aggregate is not a security-level borrow-demand measure.

## 2. Candidate observation and row filter

Use one observation per `ACCESSION_NUMBER × SERIES_ID × security_id`, retaining every accession as an immutable as-filed vintage.

Initial narrow direct-short common-equity filter:

- `PAYOFF_PROFILE = Short`;
- `ASSET_CAT = EC`;
- `ISSUER_CAT = CORP`;
- `INV_COUNTRY = US`;
- `UNIT = NS`;
- `TITLE = Common Stock` where present and consistent;
- negative `BALANCE`, `CURRENCY_VALUE` and `PERCENTAGE/pctVal` must be sign-concordant;
- a valid CUSIP or ISIN must resolve to a U.S. primary listing effective on the report date.

`INV_COUNTRY=US` is not a listing-venue field. A foreign-format CUSIP/ISIN, ADR, dual listing, missing identifier or unresolved share class is not promoted by fuzzy ticker matching. Preserve exceptions and quarantine unresolved rows.

Provisional magnitudes for validation against raw XML:
- `short_pct_nav = -pctVal` in percentage points;
- `short_market_value_usd = -valUSD`;
- `short_shares = -balance` for `NS` rows.

The Phase 217 sample is consistent with `pctVal` being percentage points (for example, -3.154 for approximately -3.154% of fund NAV), but this unit must be checked across the complete raw filing panel before use.

## 3. Pre-registered signal definition

The primary feature is the change in explicit direct-short exposure for the **same fund series and same historically resolved security** between consecutive publicly available report vintages:

`delta_short_pct_nav = current_short_pct_nav - prior_short_pct_nav`

Positive values mean the fund increased the magnitude of its short exposure. The fixed directional hypothesis is that larger positive changes predict lower subsequent security returns.

For the first implementation, calculate changes only where an explicit short row exists in both consecutive reports. Do **not** convert an absent row into zero, infer an initiation/covering event, or treat missing identifiers as no position. Entry/exit features are deferred until full-holdings completeness and omission semantics pass independent controls.

Cross-fund summaries, if coverage permits:
- median `delta_short_pct_nav` across independent registrant-CIK clusters;
- breadth: fraction of eligible registrant clusters increasing short exposure;
- median current short exposure level;
- number of eligible registrant clusters and fund series;
- report age and report-to-acceptance lag;
- concentration / largest registrant contribution.

A registrant CIK is only a conservative clustering proxy, not a verified ultimate adviser/manager identity. Collapse multiple series within a registrant before computing cross-registrant breadth so one registrant with many series cannot dominate. Do not label any bucket "smart money."

## 4. Point-in-time rules

Preserve separate fields for:
- report period end;
- filing date;
- SEC `ACCEPTANCE-DATETIME` in ET and UTC;
- first independently captured public-receipt time, if later established;
- first full regular U.S. equity session whose open is strictly after acceptance.

Until first public receipt is independently captured, use that first full-session boundary and never trade a partial session after an intraday acceptance. Do not use report date, quarterly bulk archive publication date, or a fixed 58/60-day lag as the knowledge time.

For every signal date, use only the latest accession for each fund series that was accepted before the session boundary. Preserve amendments as separate vintages; an amendment accepted later may update the state only from its own later knowledge boundary. Reconstruct as-of state without overwriting earlier versions.

The 25-filing Phase 218 lag sample is purposive and descriptive (17–60 calendar days; median 59), not a population estimate. Never hard-code its median.

## 5. Feasibility gates before any return test

All gates below must pass before alpha testing is authorized:

1. Retrieve the five Phase 193 accessions' complete submission text, primary XML and directory index; record byte sizes and SHA-256 hashes.
2. Reconcile accession, form, report period, filing date and acceptance timestamp against SEC-HEADER; retain raw source bytes as a time-limited artifact and metadata/hashes in the repository.
3. Parse every investment-security node deterministically, not a selected line sample. Reconcile XML rows against the complete submission and SEC bulk dataset.
4. Establish fund `SERIES_ID` continuity, registrant/fund-series deduplication and NPORT-P/A amendment lineage. Never overwrite a prior vintage.
5. Validate short-row sign/unit semantics and complete-holdings/omission rules. Missing rows remain unknown until proven otherwise.
6. Build effective-dated CUSIP/ISIN-to-security/listing identity, including ADRs, share classes, mergers, splits, ticker changes, inactive and delisted securities.
7. Measure coverage across the separate broad PIT U.S. common-equity universe. The hand-curated 335-name F80 set is retained only for legacy comparability and is not a survivorship-free market universe.
8. Measure the number of independent registrant clusters, fund series, securities, report vintages and nonzero short positions by quarter; estimate attrition at every stage.
9. Capture actual public receipt or conservatively document the EDGAR-acceptance/next-full-session convention. Bulk ZIP publication is not a substitute for filing-level knowledge time.

If the five-filing raw pilot or broader stratified sample shows negligible coverage, unstable series identity or non-reproducible vintages, archive the hypothesis rather than expanding it.

## 6. Economic test — only after admission

If all source gates pass, preregister a chronological event/cross-sectional test:
- fixed negative direction: increased short exposure predicts lower forward residual returns; no post-hoc sign reversal;
- predeclared horizons (5, 20, 63 and 126 trading sessions) reported together with multiplicity control; no horizon shopping;
- residualize/stratify against trailing 20/60/120-session returns, volatility, ADV/liquidity, size, beta and sector to separate information from return-chasing;
- compare against lagged price-only controls and frozen LTM/F80 on the same eligible securities, signal dates, exposure, turnover constraints and realistic costs;
- report gross and net returns, drawdown/tail risk, capacity, coverage and missingness;
- cluster/block bootstrap by formation date and registrant; leave-one-registrant, leave-one-fund-series and leave-one-issuer-out;
- chronological expanding/rolling OOS only; the legacy holdout remains `CONSUMED_NOT_PRISTINE` and is not reused;
- require a separate untouched prospective confirmation before any production promotion.

No minimum or maximum holding period is imposed. The predeclared horizon set is a diagnostic family, not a requirement to trade at any one horizon.

## 7. Current disposition

| Gate | Status |
|---|---|
| Distinct from Phase 27N/27O long-side signal | PASS |
| Public archive history identified | PASS — 28 quarterly archives |
| Direct-short examples observed | PASS — selected rows in one filing |
| Five raw filings downloaded and hashed | NOT VERIFIED |
| Complete deterministic holdings parse | NOT VERIFIED |
| First public receipt / vintage history | NOT VERIFIED |
| Series and amendment lineage | NOT ESTABLISHED |
| Effective-dated broad security identity | NOT ESTABLISHED |
| Broad PIT universe coverage | NOT ESTIMATED |
| Alpha test authorized | NO |

**Human dependency:** configure the authorized GitHub Actions secret `SEC_CONTACT_EMAIL`. The Phase 193 workflow is fail-closed and must send zero SEC requests while this secret is empty. Do not use a placeholder or hard-coded email.

**Controls:** no return test, no alpha test, no bootstrap/LOO, no holdout use, no data purchase, no vendor contact, no universe or production change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Sources and repository evidence

- SEC N-PORT data sets: https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets
- SEC N-PORT README: https://www.sec.gov/files/nport_readme.pdf
- Federal Register delay of N-PORT amendments (2025-04-22): https://www.govinfo.gov/content/pkg/FR-2025-04-22/html/2025-06861.htm
- Phase 191: `research/PHASE191_SEC_NPORT_REGISTERED_FUND_SHORT_EXPOSURE_PIT_FEASIBILITY_2026-11-07.md`
- Phase 192: `research/PHASE192_NPORT_DIRECT_SHORT_EQUITY_SAMPLE_DISCOVERY_2026-11-07.md`
- Phase 193: `research/PHASE193_NPORT_RAW_FILING_ACCEPTANCE_TIME_AUDIT_2026-11-07.md`
- Phase 217: `research/PHASE217_SEC_NPORT_FULL_SUBMISSION_TEXT_SHORT_ROW_PILOT_2026-11-08.md`
- Phase 218: `research/PHASE218_NPORT_PUBLICATION_VINTAGE_AND_SECURITIES_LENDING_SEMANTICS_AUDIT_2026-11-08.md`

**Conclusion:** preserve this as a genuinely different short-side hypothesis, but do not confuse a documented short position with informed bearish trading. The next useful evidence is raw, hash-verified, complete filings and a reproducible PIT panel—not another selected example or a premature return backtest.
