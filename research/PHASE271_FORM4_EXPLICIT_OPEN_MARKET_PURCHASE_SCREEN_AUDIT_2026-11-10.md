# Phase 271 — SEC Form 4 explicit-open-market purchase screen

**Date:** 2026-11-10 UTC  
**Source:** immutable Phase 39 SEC Form 3/4/5 artifact; no new SEC requests  
**Mode:** historical source/semantics audit only; no returns or alpha test

## Executive decision

A conservative, transaction-row footnote screen can isolate a small set of Form 4 original Table I purchase rows whose filed footnotes explicitly describe an open-market purchase and do not disclose private, plan, or common mechanical/compensation language. The screen also requires acquired direction, direct ownership, one reporting owner, a common-stock title, and (after the April 1, 2023 checkbox effective date) an explicitly false AFF10B5ONE value.

This is a **high-precision / low-recall candidate screen**, not proof of discretionary informed buying. Form 4 transaction code P means “open market or private”; absence of a private/plan footnote does not prove that the transaction was discretionary or executed in a public market. AFF10B5ONE=false excludes only a filing marked as Rule 10b5-1(c); it does not rule out every other trading plan.

## Reproducible source

- Phase 39 Actions run: [40606706518](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40606706518)
- Artifact: [12781850078](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40606706518/artifacts/12781850078)
- Outer ZIP SHA-256: `203d7b1d2e29c999da318456af72e621cb30ef9a470d8f1610d088f9bebecb66`
- 2012Q1 inner ZIP SHA-256: `0cac6f943813dae94c20ecc8bca63fda692e2b8ac6d02ce2c322ab411f45c357`
- 2026Q3 inner ZIP SHA-256: `a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3`

The artifact was downloaded from the existing GitHub Actions archive and parsed locally. The outer and both inner hashes matched the previously adjudicated Phase 39/150/151 source. No new SEC request, vendor contact, or data purchase occurred.

## Population and results

Population: original Form 4 submissions only (`DOCUMENT_TYPE=4`), Table I non-derivative rows (`NONDERIV_TRANS`), `TRANS_FORM_TYPE=4`, code `P`, acquired/disposed `A`. Form 4/A, Form 5-type rows, sales, and derivative Table II rows are excluded from this screen.

| Screen stage | 2012Q1 rows | 2026Q3 rows |
|---|---:|---:|
| Original Form 4 Table I P/A rows | 6,702 | 5,007 |
| Footnote explicitly says open market | 188 | 224 |
| No explicit private wording | 186 | 224 |
| No explicit plan / 10b5-1 / ESPP wording | 160 | 158 |
| No explicit mechanical / compensation wording | 160 | 144 |
| Direct ownership | 138 | 109 |
| Exactly one reporting owner | 109 | 97 |
| Common-stock title | **102** | **85** |
| AFF10B5ONE explicitly false (post-2023 gate) | not available | **85** |

Final screen:

- **2012Q1:** 102 rows, 47 accessions, 16 issuer CIKs (1.52% of the 6,702-row base). AFF10B5ONE did not exist in this schema, so plan status is **UNKNOWN**, never false.
- **2026Q3:** 85 rows, 59 accessions, 31 issuer CIKs (1.70% of the 5,007-row base). All 85 have AFF10B5ONE explicitly false under the SEC field encoding (0/false).

The two quarters are endpoint samples only. These counts do not establish continuous quarterly coverage, coverage of the frozen investable universe, or independent observations: multiple rows can belong to one accession and multiple accessions can belong to one issuer.

## Interpretation and failure controls

1. **P is not a clean discretionary-buy code.** The SEC's transaction-code definition includes open-market *or private* purchases. The screen therefore requires transaction-row footnote evidence of “open market”.
2. **Footnote text is not a complete intent classifier.** Missing disclosure does not prove no plan, private element, or compensation arrangement. Broad “plan” and mechanical-term exclusions deliberately sacrifice recall.
3. **AFF10B5ONE has a structural break.** Pre-April 1, 2023 absence is UNKNOWN. Post-effective-date false means no Rule 10b5-1(c) affirmative-defense checkbox was indicated; it does not prove absence of a non-Rule-10b5-1 arrangement or prove discretionary timing.
4. **Amendments are not new trades.** This screen excludes Form 4/A from the base event population. Phase 152's line-level amendment audit remains mandatory before building an amendment-aware event ledger.
5. **PIT is not admitted.** The quarterly bulk table's FILING_DATE is date-only. This phase does not reconcile acceptance timestamps for every candidate accession. Knowledge must begin at the actual EDGAR acceptance/public-availability time, with after-close filings first tradable on the next eligible session.
6. **Identity and coverage remain open.** Issuer CIK is the primary issuer key; the issuer-level trading symbol is not a permanent share-class identifier. Exact frozen-universe overlap and class mapping are not measured.
7. **No market-impact scaling.** Dollar value and transaction size are not promoted because a survivorship-free, corporate-action-consistent ADV20 denominator remains unavailable.

## Decision

**Retain Form 4 as a conditional filing-time event source, but do not admit this screen to strict PIT, stock selection, or alpha.** The high-precision subset is sparse in both endpoint samples and still requires manual semantic adjudication, full accession acceptance-time coverage, cross-quarter amendment lineage, effective-dated security identity, frozen-universe coverage, and a market-liquidity denominator.

No forward-return test, bootstrap/LOO, chronological OOS, or holdout test was run. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; production, universe, capital and parameters are unchanged. The legacy holdout remains `CONSUMED_NOT_PRISTINE` and unused.

## Files

- [Auditor](phase271_form4_open_market_purchase_screen.py)
- [Tests](test_phase271_form4_open_market_purchase_screen.py)
- [Aggregate result](phase271_form4_open_market_purchase_screen_result.json)
- [Workflow](../.github/workflows/phase271_form4_open_market_purchase_screen.yml)

## Next gates

1. Use an authorized SEC contact identity to retrieve the adjacent/continuous quarterly datasets; do not guess or reuse commit metadata as the SEC User-Agent contact.
2. Reconcile acceptance timestamps for every candidate accession and retain the original filing bytes/hash.
3. Resolve Form 4/A parent accessions across quarter boundaries and diff transaction lines; amendments are state updates, not independent flow.
4. Manually adjudicate a stratified sample of footnote classifications and measure screen precision/recall before any event study.
5. Join issuer CIK to effective-dated share class/listing and quantify coverage against the frozen universe.
6. Obtain an authorized survivorship-free daily market-data denominator before scaling purchase value or ADV.
