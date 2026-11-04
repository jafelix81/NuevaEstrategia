# Phase 87 — 13D/13G filer-versus-subject correction

**Audit date:** 2026-11-04  
**Input run:** [Phase 35 run 41878429289](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41878429289)  
**Artifact:** [phase35-13dg-pit-event-crosswalk-audit, ID 13363886486](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41878429289/artifacts/13363886486)  
**Artifact ZIP SHA-256:** `823ea348d8bbe51ec37a12e4aa306f63d69ab40b37687bb3bafac768e3f27ef7`  
**Decision:** **REJECT Phase 35 artifact as a subject-issuer event panel.** Retain it only as a filer-side retrieval/parser diagnostic. No economic test is authorized.

## 1. Why the latest Phase 35 output is not issuer-level

The audited script calls `https://data.sec.gov/submissions/CIK{cik}.json` for each current ticker-to-CIK candidate, stores that queried CIK as `issuer_cik`, and downloads the filing's primary document. That endpoint is an entity's own submissions history; it does not enumerate every third-party 13D/13G filing in which that entity is the subject company.

The parser does not consistently replace this with the structured `issuerCik` from 13D/13G XML or a role-validated SEC header `SUBJECT COMPANY` field. For XML primary documents, the generic `CENTRAL INDEX KEY` regex may not match, leaving the submissions-query CIK in the `issuer_cik` column. The resulting ticker can therefore identify the reporting person/filer, not the subject issuer.

### Confirmed SEC positive control

Artifact row `0000895421-24-000178` is labelled `ticker=MS`, `issuer_cik=895421`, filing date 2024-02-12, primary document `abrdnGlobalASGI.txt`.

The official SEC XML for the linked follow-on accession [0000895421-25-000185](https://www.sec.gov/Archives/edgar/data/895421/000089542125000185/primary_doc.xml) explicitly records:
- `previousAccessionNumber = 0000895421-24-000178`;
- `issuerCik = 0001793855`;
- `issuerName = abrdn Global Infrastructure Income Fund`;
- reporting persons include Morgan Stanley and Morgan Stanley Smith Barney LLC.

The same SEC XML says the prior filing dated February 12, 2024 incorrectly stated its event date as December 31, 2024 instead of December 31, 2023. This independently demonstrates both a filer/subject misattribution (Morgan Stanley is the reporting person; ASGI is the subject) and why amendments must be linked and interpreted before using event dates.

This is a direct counterexample to treating the Phase 35 `ticker=MS` row as a Morgan Stanley issuer event. It is not a marginal parser-quality issue; it invalidates subject-universe attribution for this extraction method.

## 2. What the artifact actually contains

The run completed technically and produced 20,266 distinct accession rows, but those counts describe the queried-CIK submissions extraction, not 20,266 validated subject-issuer events.

| Audit item | Result |
|---|---:|
| Rows / distinct accessions | 20,266 / 20,266 |
| Distinct ticker labels / queried CIKs | 303 / 303 |
| Forms 13D, 13D/A, 13G, 13G/A | 215 / 1,209 / 5,509 / 13,333 |
| Amendments | 14,542 (71.76%) |
| Event-date field present | 19,680 (97.11%) |
| Current SEC ticker map source | 20,069 rows (99.03%) |
| External fallback ticker map source | 197 rows (0.97%) |

These figures are descriptive of the extracted filer-side rows only. They must not be reported as F80 issuer coverage, subject-issuer recall, or a historical 13D/13G panel. The extraction window is 2020-10-01 through 2026-09-30, and the 335-name list still lacks a historical active-membership ledger.

## 3. Additional defects found in the same artifact

### 3.1 Business-day lag function is invalid

The source function computes a negative date range when event date precedes filing date; Python's `range(negative)` is empty, so it returns `-1` for virtually every earlier event. In the artifact:
- 19,539 rows have `filing_lag_business_days = -1`;
- 139 rows have zero;
- no row has a positive lag;
- two rows have event date after filing date.

The lag column is unusable and must be recomputed from validated dates. Event date is not the PIT knowledge timestamp; filing/acceptance availability governs signal timing.

### 3.2 One row per accession is not a reporting-person panel

The extraction writes one row per accession. Its `first_text` and `first_num` helpers return only the first regex match, rather than retaining every reporting person and each person's separate ownership/power values. Artifact coverage is sparse: reporting-person name 17.28%, reporting-person type 49.55%, and purpose text 1.29%. The parser must preserve all reporting-person rows from structured XML and link them to the filing and subject issuer.

### 3.3 Historical submission errors are silently swallowed

The old-submissions JSON loop catches exceptions and continues without recording them. Consequently, `submission_errors=0` does not establish that every historical submissions file was retrieved. A replacement pipeline must log each failed accession/JSON URL and reconcile expected versus retrieved counts.

### 3.4 Event-date anomalies require amendment-aware handling

Two artifact rows have event dates later than their filing dates. The ASGI positive control is a documented original-filing error later described in an SEC amendment. Do not simply drop future event dates or overwrite originals: retain raw values, follow `previousAccessionNumber` links, and create a versioned event-state history with each version's own filing/acceptance knowledge time.

## 4. Required replacement architecture

1. Use the global Phase 82 master-index candidate set for discovery; do not use target-CIK submissions endpoints as a proxy for subject-side filing discovery.
2. Fetch complete submissions and parse SEC header roles separately: submitter, `FILED BY`, `SUBJECT COMPANY`, and all reporting persons.
3. Parse structured 13D/13G XML fields including issuer CIK, issuer name, all reporting-person nodes, ownership/voting/dispositive fields, event date, amendment number, and `previousAccessionNumber`.
4. Reconcile subject CIK against the frozen candidate CIKs and historical security identity. Report subject recall, filer-only false positives, unresolved identities, and issuer-level coverage by year and form.
5. Build an amendment graph; preserve original filings and later corrections as distinct knowledge-time versions. Never use a later amendment to rewrite what was knowable at an earlier signal date.
6. Use acceptance time converted with `America/New_York` DST rules, then a conservative next-session availability/execution rule unless public dissemination latency is independently verified.
7. Only after identity, historical universe, and PIT gates pass may a preregistered economic hypothesis be tested against frozen LTM/F80.

## 5. Current execution boundary

- Phase 83's original 120-filing gate failure remains archived and unchanged.
- Phase 84's disjoint 600-filing role-aware pilot is running as [run 41914491120](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41914491120); it is the next valid identity gate. No overlapping SEC crawl should be launched while it runs.
- Phase 69 Form 144 incremental scan was not executed; its guarded live job was skipped.
- No forward returns, feature selection, alpha test, vendor purchase, or production change was made.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

**Final decision:** Phase 35 run 41878429289 passed its retrieval job but failed the subject-identity research gate. Do not use its 20,266 rows as issuer events. Advance only through the role-aware global-index route and amendment-aware XML reconstruction.
