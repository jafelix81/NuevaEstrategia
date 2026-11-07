# Phase 153 — SEC Form 4/A cross-quarter lineage preflight

**Date:** 2026-11-06  
**Status:** BLOCKED — SEC contact identity required for adjacent-quarter bulk downloads

## What was completed

- Added a cross-quarter parent-candidate engine for Form 4/A. It uses issuer CIK, DATE_OF_ORIG_SUB, original Form 4 filing date, and reporting-owner CIK overlap. Only original Form 4 filings can be parent candidates; Form 4/A filings are excluded.
- Added multiset transaction-line comparison for Table I and Table II. Exact repeats are separated from same-coarse unmatched lines; the latter remain ambiguous because they may be additional transactions or amendments to existing rows.
- Corrected ZIP table selection to compare exact basenames. The prior suffix test accidentally matched DERIV_TRANS.tsv to NONDERIV_TRANS.tsv.
- Added 17 offline tests. All 17 passed locally on the current helper.
- Reused the immutable Phase 39 artifact (run 40606706518, artifact 12781850078; SHA-256 `203d7b1d2e29c999da318456af72e621cb30ef9a470d8f1610d088f9bebecb66`).

## Same-quarter reproduction only

These figures reproduce the Phase 152 same-quarter candidate baseline; they are **not** cross-quarter coverage results.

| Target quarter | Form 4/A | Unique same-quarter parent candidates | Ambiguous | No candidate in available window | Coverage |
|---|---:|---:|---:|---:|---:|
| 2012Q1 | 1,862 | 1,146 | 40 | 676 | 61.5467% |
| 2026Q3 | 627 | 341 | 7 | 279 | 54.3860% |

Both search windows are marked incomplete because the immediately preceding quarter was not available.

## ETON amendment regression

For issuer CIK 0001710340:

- Original: `0001437749-26-029196`
- Amendment: `0001437749-26-029308`
- Table I: four exact repeated candidate rows and one same-coarse unmatched row.
- Table II: one exact repeated candidate row and one same-coarse unmatched row.

The extra rows are not automatically called new transactions. A same-coarse row can be either a new transaction or a modified line. This conservative rule avoids turning amendment mechanics into artificial event flow.

## SEC download blocker

Two adjacent-quarter attempts returned HTTP 403:

- Run [42201178315](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42201178315): 2011Q4 download.
- Run [42201909289](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42201909289): 2026Q2 download.

The official [SEC Accessing EDGAR Data policy](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) asks automated clients to declare a User-Agent that identifies the requester and includes a contact email. The workflow's previous User-Agent identified the project but omitted the email. No personal email from commit metadata was reused and no address was fabricated.

The workflow now reads an authorized contact from the repository Actions secret `SEC_CONTACT_EMAIL`. If the secret is absent, it runs offline tests and uploads a blocked-status artifact without making further SEC requests. If configured, it uses the contact in the User-Agent and attempts the adjacent-quarter downloads.

**Human action to resume:** configure `SEC_CONTACT_EMAIL` in the repository's Actions secrets, then manually dispatch the Phase 153 workflow.

## Research decision

- No cross-quarter parent-link coverage result yet.
- No return or alpha test.
- No final holdout used.
- No vendor contacted or data purchased.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
