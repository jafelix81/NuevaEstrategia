# Phase 96 — Revalidation of the Phase 35 13D/G issuer-side panel

**Date:** 2026-11-05  
**Scope:** offline reanalysis of the completed Phase 35 GitHub Actions artifact and known SEC positive controls. No SEC crawl, no forward returns, no feature construction.

## Executive decision

**REJECT Phase 35 run 41915300321 / artifact 13378568483 as an issuer-level 13D/G event panel.** Preserve it only as a CIK-submissions discovery/filer-side diagnostic. The artifact again assigns a known Morgan Stanley filing about another issuer to Morgan Stanley's ticker/CIK. It therefore cannot be used for subject-issuer event studies, feature construction or alpha tests.

This does not invalidate the separate role-aware Phase 84/89/91/93 sample. The two pipelines must not be conflated or merged.

## 1. Artifact and method inspected

- Workflow run: https://github.com/jafelix81/NuevaEstrategia/actions/runs/41915300321
- Job: 126874047512, completed successfully on 2026-11-05.
- Artifact: https://github.com/jafelix81/NuevaEstrategia/actions/runs/41915300321/artifacts/13378568483
- Artifact ID: 13378568483; ZIP SHA-256: `db1be2f91f10aab72e6e13dd1f3f10105d40800c7f3ea04b6e1c7d7b0256b55f`.
- Files: `phase28d_events.csv` (20,253 rows) and `phase28d_summary.json`.
- Summary method: issuer-specific SEC submissions using current and historical CIK crosswalks. It does not show a role-aware XML subject/filer validation for every row.
- Summary counts: 20,266 candidates, 20,253 resolved rows, 303 unique tickers/CIKs, 14,533 amendments, 19,667 event-date values, 13 primary-document resolution errors (HTTP 503), and zero submission errors.
- Event-date field coverage of 97.11% is not public-availability coverage. The filing's accepted timestamp and verified subject issuer are separate requirements.

## 2. Decisive positive-control failure

The artifact contains accession `0000895421-24-000178` as:

| Field | Phase 35 artifact |
|---|---|
| ticker | MS |
| issuer_cik | 0000895421 |
| form | SC 13G |
| filing date | 2024-02-12 |
| primary document | `abrdnGlobalASGI.txt` |

It also contains the linked amendment `0000895421-25-000185` as ticker MS / issuer_cik 0000895421 / SC 13G/A / filing date 2025-02-03.

The official SEC XML for the 2025 amendment identifies:
- submission filer CIK 0000895421 (Morgan Stanley);
- subject issuer CIK 0001793855 (abrdn Global Infrastructure Income Fund); and
- previousAccessionNumber `0000895421-24-000178`.

The amendment also states that the prior 2024 filing misstated its event date. Phase 35 assigns the accession-prefix/submitting filer CIK to the subject issuer and retains an event date of 2024-12-31 for the 2024 filing, later than its 2024-02-12 filing date. This is a known, material role and event-field error, not a cosmetic ticker mismatch.

Official SEC document: https://www.sec.gov/Archives/edgar/data/895421/000089542125000185/primary_doc.xml  
Prior repository correction: https://github.com/jafelix81/NuevaEstrategia/blob/phase87-13dg-filer-subject-correction/research/PHASE87_13DG_FILER_SUBJECT_IDENTITY_CORRECTION_2026-11-04.md

## 3. Interpretation

A CIK-specific submissions feed is a discovery route for filings associated with that CIK; it is not proof that the queried CIK is the subject issuer in every beneficial-ownership filing. A reporting person, adviser or submitting filer can file about a different issuer. The Phase 35 output's `issuer_cik` assignment is therefore not a safe issuer identity field.

The fact that 303 tickers/CIKs appear and 97.11% of rows contain an event date does not cure this identity defect. A panel can be complete in row count and still be wrong about the security whose event is being measured.

## 4. Required treatment

1. Mark Phase 35 run 41915300321 and artifact 13378568483 **DIAGNOSTIC ONLY — NOT SUBJECT-ISSUER VALIDATED**.
2. Exclude the entire Phase 35 event file from forward-return tests, signal panels, issuer-level merges and model training unless every row is rebuilt and independently role-validated.
3. Do not use accession-prefix CIK, queried submissions CIK, filer CIK or first-person 13G CIK candidate as a substitute for subject issuer CIK.
4. Use global master-index discovery only as a candidate generator. Parse SEC-HEADER SUBJECT COMPANY and FILED BY separately; reconcile structured XML issuerCik/filer CIK where available.
5. Preserve acceptance datetime as the conservative knowledge timestamp; event date is not public availability.
6. Keep Phase 84/89/91/93 raw artifacts and outputs separate from Phase 35. Phase 84's corrected sample had 600/600 submissions retrieved, 200/200 structured XML subject/filer/header concordance, 192/192 mandatory XML, 143/367 candidate rows classified filer-only, and no economic test.
7. Do not launch another SEC crawl solely to repeat this diagnosis. The failure is already demonstrated by a known positive control.

## 5. What remains valid

The Phase 35 artifact can still support discovery diagnostics about filings associated with candidate CIKs, provided its role ambiguity is explicit. It cannot support issuer-level ownership changes or return attribution.

The role-aware Phase 84/89/91/93 path remains a separate limited-sample feasibility result:
- 600/600 raw submissions retrieved and hashed;
- 224/224 target CIKs present in the index/path candidate set;
- 143/367 candidate-target rows were filer-only false positives;
- 200/200 structured XML subject, filer and form checks matched SEC-HEADER;
- 192/192 actual mandatory Schedule 13D/G XML documents were present after correcting the denominator;
- Phase 93 reparsed 200/200 structured filings with zero identity/hash errors and 17 regression tests passed.

That is evidence for a role-aware data pipeline, not evidence of predictive or economic value.

## 6. Decision

Phase 35 is closed as an issuer-event panel. Phase 84/89/91/93 remains a limited feasibility branch, with no forward returns authorized. The next binding research task is historical security/universe reconstruction, not another CIK-specific SEC submissions crawl.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
