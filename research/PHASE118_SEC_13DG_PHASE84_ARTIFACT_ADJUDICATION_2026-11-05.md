# Phase 118 — SEC 13D/13G Phase 84 artifact adjudication

Date: 2026-11-05  
Status: **PASS_WITH_INDEX_ALIAS_QUARANTINE**  
Scope: artifact-only re-audit; no SEC network requests and no forward-return calculations.

## 1. Why this adjudication was necessary

Phase 84 (`41914491120`, branch `phase84-13dg-role-aware-identity-validation`) retrieved all 600 stratified complete submissions, saved all raw files, and passed the offline tests. Its live job ended with `data_gate=FAIL` because the mandatory-XML check was 192/193 = 99.482%, just below the 99.5% threshold. The original summary also reported 599/600 form concordance (99.833%), with every other gate passing.

The apparent missing XML row was accession `0001104659-26-057293`. The Phase 84 sample classified it as `SC 13D/A` from one SEC quarterly master-index row and placed it in the `13d_mandatory_xml` stratum. The raw SEC submission does **not** describe a 13D/G filing:

- SEC-HEADER `CONFORMED SUBMISSION TYPE`: `SC TO-T/A`.
- Document types: `SC TO-T/A` and `EX-99.(A)(5)(B)`.
- No 13D/G document is present.

The frozen Phase 82 raw `master_2026Q2.idx` contains three rows for this same accession: two `SC TO-T/A` rows and one `SC 13D/A` row, all pointing to the same accession archive submission. This is an index-level cross-form alias, not a missing mandatory XML attachment for an actual 13D/G submission. It is a control row, not one of the 367 target-CIK candidate rows.

## 2. Reproducible re-audit

The Phase 118 script independently re-opened the Phase 84 and Phase 82 ZIP artifacts. It recomputed raw-file hashes and sizes, re-parsed the SEC submission header and document types, re-derived the acceptance timestamp from the raw SEC header in `America/New_York`, and rechecked the role/XML metadata.

| Check | Result |
|---|---:|
| Phase 84 raw submissions present | 600/600 |
| Raw SHA-256 recomputed and matched | 600/600 |
| Raw byte lengths matched metadata | 600/600 |
| HTTP 200 | 600/600 |
| Acceptance UTC recomputed from raw SEC header | 600/600 |
| Retrieval timestamps parse as offset-aware UTC | 600/600 |
| Present XML subject/header matches | 200/200 |
| Present XML filer/header matches | 200/200 |
| Unresolved index/header/document form conflicts | 0 |

The one index/header mismatch is quarantined only after the actual SEC header and all document types agree that it is non-13D/G. A conflicting 13D/G document would remain unresolved and fail the gate; the code does not silently quarantine such a case.

## 3. Corrected form and XML gate

| Metric | Original Phase 84 denominator | After form adjudication |
|---|---:|---:|
| Rows in 13D/G-index sample | 600 | 599 actual 13D/G submissions + 1 quarantined alias |
| Master-index/header form matches | 599/600 | 599/599 actual 13D/G rows |
| Mandatory-XML stratum rows | 193 | 192 actual 13D/G rows |
| Mandatory XML present | 192/193 | 192/192 |
| Mandatory XML missing | 1 | 0 |

The correct result is **PASS_WITH_INDEX_ALIAS_QUARANTINE**, not a source-wide failure. The original Phase 84 run remains recorded as failed under its original gate; Phase 118 is a separate, reproducible adjudication of its immutable artifact.

## 4. Role-resolution findings retained from Phase 84

The 600-row sample contains 367 rows where either the subject or filer CIK intersects the current 319-CIK candidate list. The SEC header roles resolve all 367:

| Candidate class / role | Rows |
|---|---:|
| Unique candidate resolved to subject | 89 |
| Unique candidate resolved to filer only | 143 |
| Ambiguous candidate resolved to subject | 135 |
| Ambiguous candidate resolved to filer | 0 |
| **Total candidate rows** | **367** |

Thus the unweighted sample has 224 subject-role rows (61.04%) and 143 filer-only rows (38.96%). The existing post-stratified descriptive estimate across 34,400 candidate accessions is 17,906.9 subject-target accessions (52.06%) and 16,493.1 filer-only false positives (47.94%). The estimate has no inferential confidence interval and is not alpha evidence.

All 224 sampled subject-role rows have index-candidate coverage. This is conditional on the candidate population intersecting the **current** 319-CIK map; it does not establish global subject-issuer recall, recover historical CIK/ticker lineages, or prove historical F80 membership. The 135 ambiguous rows are resolved using SEC-HEADER roles, not by treating the master-index CIK or archive-path CIK as the issuer by assumption.

## 5. Decision and next gate

**Decision:** promote the Phase 84 role-aware filing retrieval/parser result to the next data-normalization gate, with the one non-13D/G index alias quarantined. Do not repeat the 600-filing live retrieval solely to rescue the 99.5% threshold; the immutable artifact resolves the issue.

Before any forward-return test, the next gate must still establish:

1. Deterministic subject issuer, filer, reporting-person and reporting-group identities.
2. Original/amendment lineage using explicit SEC links where available; amendments are not independent events by default.
3. Separate 13D and 13G event families and a reproducible ownership-state transition; unknown direction remains unknown.
4. Historical CIK-to-security identity and active/delisted security membership by signal date. The current 319-CIK map is not a PIT security master.
5. Quarter-by-quarter eligible-event coverage and exclusion reasons.
6. A conservative knowledge-time rule: the SEC acceptance timestamp is reproducible, but public dissemination time is not independently established here; use the next trading session after acceptance unless a stronger publication-time source is validated.

No forward returns, feature selection, alpha inference, purchases, or production changes were performed. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## 6. Reproduction

Inputs (downloaded immutable GitHub Actions artifacts):

- Phase 84 artifact `13364856424`, ZIP SHA-256 `b807be9099e1a777c232f6d50b341e8e714585dc4da5fe993e833c2051494b16`.
- Phase 82 artifact `13353118959`, ZIP SHA-256 `e925ad8fe9792f27e570b9e882dff772bb67d9edd67f1c93404a198faab80985`.

Run:

```bash
python research/phase118_sec_13dg_phase84_adjudication.py \
  --phase84-zip phase84.zip \
  --phase82-zip phase82.zip \
  --output phase118_adjudication.json
python -m unittest -v research.test_phase118_sec_13dg_phase84_adjudication
```

The script performs no network calls. Seven offline unit tests passed locally; the repository workflow runs the same tests on push.
