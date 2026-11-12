# Phase 343 — SEC Form 4 high-precision cohort: candidate-specific event-time identity audit

**Status:** first hosted retrieval completed, but reconciliation halted on a SEC bulk-date normalization defect; corrected rerun pending.  
**Population:** 2026Q3 high-precision Form 4 cohort from the Phase 342 official SEC bulk archive.  
**Pre-registered denominator:** 85 candidate rows, 59 accessions, 31 issuer CIKs and 48 issuer-CIK × filing-date event units.  
**Research boundary:** identity/availability audit only; no return, alpha, OOS, bootstrap/LOO or holdout test.

## Question

Does the high-precision 2026Q3 Form 4 purchase cohort have a reproducible mapping from each transaction's original Form 4 security title to a same-CIK TradingSymbol + Security12bTitle + SecurityExchangeName triple in the latest supported periodic XBRL filing strictly before the Form 4 filing date?

The 41.67% Phase 341 crosswalk rate is not extrapolated: its 72-accession sample has zero accession and zero issuer-CIK overlap with the Phase 342 high-precision 2026Q3 cohort.

## Method

1. Re-download the official 2026Q3 SEC Insider Transactions archive and require its SHA-256 to equal Phase 342's pinned source hash.
2. Re-run the Phase 342 high-precision screen and require exact reproduction of 85 rows / 59 accessions / 31 issuers / 48 issuer-date event units.
3. Retrieve all 59 original Form 4 submissions. Verify accession, form, filing date, header/XML issuer CIK, and exact issuer-symbol agreement between the bulk archive and original XML.
4. Match every candidate transaction row to exactly one original non-derivative XML transaction row using normalized title, date, code, ownership direction, acquired/disposed flag, shares and price. Re-run the explicit-open-market footnote and exclusion screen against original XML footnotes; missing referenced footnotes fail closed.
5. For each of the 48 issuer-CIK × filing-date units, select the latest supported SEC periodic filing strictly before the Form 4 filing date. Require an anchor age of 1–365 calendar days for event-time identity.
6. Retrieve the exact XBRL instance (or primary inline-XBRL HTML fallback), hash it, and accept a class crosswalk only when TradingSymbol, Security12bTitle and SecurityExchangeName occur in the same XBRL context, the symbol matches exactly, and the transaction title passes the controlled instrument-class comparison.
7. Preserve class-axis and multi-listing-axis members. Multiple exchange contexts for the same unique class are retained as multiple listings; multiple compatible security classes remain ambiguous.
8. Keep event-time identity separate from transaction-date identity. A periodic anchor after the underlying transaction but before Form 4 disclosure may support a disclosure-time study, but not a transaction-date claim.

## Required output

The hosted artifact will contain the pinned bulk ZIP, original Form 4 submissions, SEC submissions JSON, periodic filing indexes/instances, response headers, SHA-256 manifest, row-level crosswalk, accession summary and event-unit summary.

## Decision rules

- Unavailable or mismatched source bytes are quarantined.
- No fuzzy ticker or title joins.
- Missing/ambiguous class, exchange or context evidence remains unresolved.
- SecurityExchangeName=NONE is preserved as a no-national-exchange status; it is not silently treated as missing or as a listed exchange.
- SEC acceptance time and date-only FILING_DATE are not claimed to be exact first-public receipt.
- No event study begins in this phase. A later price-coverage phase must use the first full exchange session strictly after the official Form 4 filing date unless exact public availability is independently established.


## Hosted execution diagnostic and correction (2026-11-12)

- Initial hosted attempts [43271361011](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43271361011) and [43271791093](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43271791093) passed all 11 offline regressions and downloaded the pinned 2026Q3 archive. They did **not** produce a candidate identity result.
- The second attempt halted at `periodic_anchor_not_strictly_pre_filing:102109:24-SEP-2026`. SEC bulk `FILING_DATE`/`TRANS_DATE` values use `DD-MON-YYYY` (for example `24-SEP-2026`), while the prior code compared them lexicographically with ISO dates and passed them to `date.fromisoformat`. The same raw date also reached the original-submission header reconciliation, so Form 4 retrievals were not yet proven by that run.
- Corrective change 1: normalize bulk filing and transaction dates to canonical ISO before Form 4 header checks, transaction-row matching, prior-periodic selection and strict temporal comparisons. If a selected periodic filing is not strictly prior after normalization, quarantine that event unit instead of aborting the entire cohort; no look-ahead row can pass.
- The corrected run then exposed a second validation error: SEC filing-header `CENTRAL INDEX KEY` is the filer CIK (typically a reporting owner), not necessarily the issuer CIK. The issuer identity is validated against `issuer/issuerCik` in the ownership XML; the header CIK must match either that issuer or one of the XML reporting-owner CIKs. The earlier equality-only issuer check was invalid and is replaced with this explicit role check.
- Raw original Form 4 submission bytes are now written to the artifact immediately after retrieval, before parsing or identity checks, so a quarantined record remains reproducible even if a later step fails.
- Added regression tests for SEC date normalization, equivalent bulk/XML transaction keys, prior-periodic selection across a mixed-format event date, and issuer-versus-reporting-owner header CIK semantics. The uploaded failure artifact [13968634062](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43271791093/artifacts/13968634062) contains the pinned archive and response headers only; it contains no row-level crosswalk or coverage result.
- A corrected hosted run is required before any Phase 343 identity coverage is reported.

## Controls

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No production, universe, capital or parameter changes. No security master or strict PIT source admission. No data purchase or vendor contact.
