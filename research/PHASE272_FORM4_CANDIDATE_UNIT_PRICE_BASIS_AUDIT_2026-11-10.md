# Phase 272 — Form 4 candidate unit-of-analysis, owner-role and price-basis audit

**Date:** 2026-11-10 UTC  
**Source:** immutable Phase 39 SEC Form 3/4/5 artifact; no new SEC requests  
**Mode:** descriptive source-quality audit only; no return, alpha, PIT or holdout test

## Executive decision

Phase 271's high-precision screen produces candidate **transaction rows**, not independent insider events. The same issuer/owner/accession can contribute many rows; the sample also contains ten-percent-owner-only filings, an entity-form reporting-owner name, zero reported prices, and explicit share-basis-restatement footnotes. These must be separated before constructing an event signal.

**Do not use Phase 271 row counts as signal counts, do not assign zero economic value to zero reported prices, and do not interpret every single-owner accession as an individual director/officer purchase.** Keep Form 4 conditional and non-PIT/non-alpha.

## 1. Reproducible source

- Phase 39 Actions run: [40606706518](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40606706518)
- Artifact: [12781850078](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40606706518/artifacts/12781850078)
- Outer ZIP SHA-256: 203d7b1d2e29c999da318456af72e621cb30ef9a470d8f1610d088f9bebecb66
- 2012Q1 inner ZIP SHA-256: 0cac6f943813dae94c20ecc8bca63fda692e2b8ac6d02ce2c322ab411f45c357
- 2026Q3 inner ZIP SHA-256: a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3

Phase 272 reproduces Phase 271's exact eligibility rules and exact row totals. No SEC endpoint was queried and no new filing bytes were downloaded.

## 2. Row counts are not independent events

| Measure | 2012Q1 | 2026Q3 |
|---|---:|---:|
| Candidate transaction rows | 102 | 85 |
| Unique accessions | 47 | 59 |
| Unique issuers | 16 | 31 |
| Unique reporting owners | 25 | 45 |
| Issuer-owner groups | 25 | 46 |
| Issuers with multiple reporting owners | 6 | 9 |
| Rows in accessions with multiple transaction rows | 74 (72.5%) | 41 (48.2%) |
| Largest transaction rows in one accession | 11 | 12 |

The accession is the disclosure/knowledge unit, not each transaction row. A filing can report multiple trades executed on different dates. Those trade dates do not make each line separately public at the trade date.

### Concentration of transaction rows

| Row concentration | 2012Q1 | 2026Q3 |
|---|---:|---:|
| Largest issuer share | 47.1% | 14.1% |
| Top two issuer share | 63.7% | 25.9% |
| Effective issuer count (inverse HHI) | 3.789 | 15.405 |
| Largest reporting-owner share | 47.1% | 17.6% |
| Top two reporting-owner share | 57.8% | 31.8% |

These HHI/effective-count figures are descriptive row-concentration measures, not independent sample sizes or statistical power estimates.

## 3. Owner roles must be separate hypotheses

The SEC reporting-owner relationship flags split as follows:

| Relationship class | 2012Q1 rows | 2026Q3 rows |
|---|---:|---:|
| Director and/or officer | 52 | 72 |
| Ten-percent-owner only | 48 | 12 |
| Other/mixed | 2 | 1 |

The 48 ten-percent-owner-only rows in 2012Q1 all belong to one issuer/one reporting owner (Onteco). The 12 ten-percent-owner-only rows in 2026Q3 belong to one issuer and one reporting owner whose name matches a legal-entity suffix heuristic. That heuristic is a diagnostic, not a definitive legal-entity classifier.

Therefore, director/officer buying and ten-percent-owner activity should be separate candidate families. A ten-percent holder can be an entity or an individual and should not be pooled automatically with directors/officers.

## 4. Price and share-basis integrity

### 2012Q1

- 48/102 candidate rows have TRANS_PRICEPERSHARE = 0. Treat these as **unquantifiable/unknown**, not zero-dollar purchases.
- 47 of those 48 zero-price rows are Onteco; the remaining row is Community Bank Shares of Indiana.
- 31 rows across 8 accessions for one issuer have footnotes saying share counts were converted/adjusted to apply to the issuer's most recent quarterly/annual report. This is an explicit share-basis restatement warning; do not combine those reported quantities with unadjusted historical prices or market volumes.
- Onteco contributes 48 rows across 11 accessions but only one reporting owner; 47 rows have zero reported price and 31 carry the share-basis-restatement flag.

### 2026Q3

- All 85 rows have a positive reported price field and no detected share-basis-restatement footnote under this conservative text rule.
- 28/85 reported-field products are below $10,000; 66/85 below $100,000; 84/85 below $1,000,000.
- These are TRANS_SHARES × TRANS_PRICEPERSHARE diagnostics only. They are not ADV-scaled, executable notional, or market-impact estimates.

### Two examples that expose the unit problem

1. **2012 Onteco:** 48 rows / 11 accessions / 1 reporting owner; 47 zero reported prices and 31 share-basis-restatement rows. The raw row count substantially overstates the number of independent owner/issuer disclosures, and its reported size fields are not fit for naïve notional scaling.
2. **2026 Income Opportunity Realty Investors:** 12 transaction rows occur in one accession from one ten-percent owner whose name is entity-form. Transaction dates run from 2026-06-04 through 2026-06-23, while the filing date is 2026-07-06. This is one filing-time disclosure event containing a multi-date trade history, not 12 separately public signals. Actual acceptance time is not joined here.

A further 2026 example has one reporting owner across two issuers and 10 accessions (15 transaction rows). That is repeated activity by one owner, not a multi-insider cluster.

## 5. Reported-value proxy (strictly descriptive)

The proxy excludes missing/zero/negative prices and rows with explicit share-basis-restatement wording.

| Measure | 2012Q1 (53 rows) | 2026Q3 (85 rows) |
|---|---:|---:|
| Median reported-field product | $8,775 | $31,636.80 |
| 75th percentile (nearest rank) | $85,117.50 | $65,000 |
| 90th percentile (nearest rank) | $249,358.56 | $243,682.65 |
| Below $10,000 | 27 | 28 |
| Below $100,000 | 41 | 66 |

This does not establish economic commitment relative to market capitalization or liquidity. A survivorship-free, corporate-action-consistent ADV20 source is still required before any scaling or market-impact claim.

## 6. Point-in-time and event-state limitations

- The bulk FILING_DATE is date-only. Phase 272 does not join every candidate accession to EDGAR acceptance time.
- The accession, not the transaction row, is the public-information event. After-close filings must not be backdated to the transaction date or filing date without an acceptance-time/calendar rule.
- Phase 152's amendment work remains mandatory: Form 4/A can repeat unchanged lines, add lines, change lines or retract prior lines. Amendments are state updates at their own acceptance times, not fresh copies of all trades.
- No effective-dated share-class/listing join or frozen-universe coverage is measured.
- The footnote screen remains text-based and requires stratified manual adjudication; absence of excluded wording is not proof of discretion.

## 7. Decision and next gates

**Phase 271 is retained as a candidate-generation screen only. Phase 272 adds mandatory diagnostics; neither phase admits strict PIT, stock selection or alpha.**

Before any event study:

1. Build an accession-level immutable event ledger with EDGAR acceptance time and original filing hash.
2. Resolve Form 4/A parent accessions and line-level additions/changes/repeated lines/tombstones.
3. Split director/officer, ten-percent-owner-only (individual vs entity where verified), and other/unknown populations.
4. Treat zero/missing price as unknown; quarantine explicit share-basis restatements from notional scaling; reconcile corporate actions.
5. Manually adjudicate a stratified footnote sample and measure screen precision/recall.
6. Map issuer CIK to effective-dated share class/listing and measure coverage against the frozen universe.
7. Obtain an authorized survivorship-free daily market-data denominator.
8. Only then test incremental information versus frozen LTM/F80 with identical exposure/costs, clustered inference, bootstrap/LOO and chronological OOS. Do not reuse the consumed legacy holdout.

Bulk SEC retrieval remains blocked by the missing authorized SEC_CONTACT_EMAIL secret. No address was guessed, no SEC request was sent, and no credential was created.

## 8. Controls

- No forward-return test, alpha, bootstrap/LOO, chronological OOS or holdout test.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- Production, universe, capital and parameters unchanged.
- No data purchase, vendor contact or SEC request.

## Files

- [Phase 272 auditor](phase272_form4_candidate_unit_price_basis_audit.py)
- [Phase 272 tests](test_phase272_form4_candidate_unit_price_basis_audit.py)
- [Phase 272 result](phase272_form4_candidate_unit_price_basis_audit_result.json)
- [Phase 272 workflow](../.github/workflows/phase272_form4_candidate_unit_price_basis_audit.yml)
- [Phase 271 report](PHASE271_FORM4_EXPLICIT_OPEN_MARKET_PURCHASE_SCREEN_AUDIT_2026-11-10.md)