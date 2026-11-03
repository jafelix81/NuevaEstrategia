# Phase 35 — 2025Q1 Global Subject Census XML Pilot Results

Date: 2026-11-03  
Branch: `phase35-13dg-issuer-attribution-repair`  
Workflow: [41724414979](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41724414979)  
Job: 126225315601  
Artifact: `phase35-global-subject-census-xml-2025q1` (ID 13274405289; 4,286,454 bytes; SHA-256 `9cbcb2b7c9f19d008e56bbbd882ce7009f9628d0ed9a3f7c28930827feadd591`)  
Code commit: `a08c6417dcc5f12c76455ec83c10ea4acb0bf451`

## Decision

**PASS — 2025Q1 structured-XML subject/filer identity feasibility only.**  
**NOT PASSED — historical coverage, reporting-group identity, amendment normalization, or economic testing.**

The pilot correctly separates the subject issuer from the submission filer for the 2025Q1 structured-XML sample. It does not establish historical F80 membership or an economic owner/group key. No forward returns were used.

## Census and identity results

The official 2025Q1 SEC master index contained 16,629 Schedule 13D/G rows and 8,318 unique accessions:

| Form | Accessions |
|---|---:|
| SC 13D | 269 |
| SC 13D/A | 1,204 |
| SC 13G | 2,230 |
| SC 13G/A | 4,615 |
| **Total** | **8,318** |

The frozen candidate list has 335 tickers; current SEC mapping resolved 307 candidate CIKs and left 27 tickers unresolved. This is a current candidate mapping, not a historical security master.

The pilot selected 1,100 accessions whose master-index CIK pair intersected the candidate CIK set, plus 206 deterministic non-target validation accessions. It requested 1,306 primary XML files; 1,299 parsed and seven returned 404s. All seven errors were in the non-target validation sample.

| Metric | Target-relevant sample | Non-target validation |
|---|---:|---:|
| Subject CIK present | 100.00% | 96.60% |
| Submission-filer CIK present | 100.00% | 96.60% |
| Subject and filer both in master-index CIK pair | 100.00% | 96.60% |
| XML form agrees with master index | 99.46% overall | 99.46% overall |

The fixed Truist/Federated fixture passed: submission filer CIK 0000092230; subject issuer CIK 0001849998.

### Subject-side versus filer-side counts

This distinction is essential. Of the 1,100 target-relevant accessions:

- 242 filings have a subject issuer CIK in the current candidate universe.
- Those 242 filings represent 142 distinct subject issuer CIKs.
- 904 filings have a submission-filer CIK in the candidate universe.
- 858 are filer-only cross-issuer filings: the filer is a candidate, but the subject issuer is not.

Therefore, the 1,100 count is a discovery union, **not** the number of filings about F80 candidate companies. Only the 242 subject-side records belong in the target-subject sample for this quarter.

Target-subject composition:

| Form | Filings | Distinct subject CIKs |
|---|---:|---:|
| SC 13D | 4 | 4 |
| SC 13D/A | 25 | 15 |
| SC 13G | 49 | 44 |
| SC 13G/A | 164 | 109 |
| **Total** | **242** | **142 across families** |

There are 16 unique subjects with at least one 13D-family filing and 130 with at least one 13G-family filing; four subjects appear in both families. These are one-quarter disclosure counts, not universe-coverage estimates or evidence of trading activity.

## Reporting-person identity: a new, unresolved 13G issue

The schema-aware parser correctly reads the 13G element names, including optional `reportingCik`. In this target-subject sample, however, none of the 474 13G reporting-person records contains an explicit reporting CIK. This is consistent with the SEC schema making that field optional; it is not evidence that the parser should substitute the submission filer automatically.

For comparison, explicit reporting-person CIK coverage in the 13D sample is:

- 13D originals: 7/8 reporting persons (87.5%).
- 13D amendments: 37/73 reporting persons (50.7%); the XML includes explicit no-CIK flags for many records.

A deterministic *candidate* crosswalk was evaluated on the saved CSV, without writing inferred CIKs back into the source data:

1. Normalize Unicode, punctuation and case.
2. Remove a fixed list of legal-entity suffixes and a leading “THE”.
3. For reporting persons marked as individuals (type IN), allow token-order reversal; for entities, preserve token order.
4. Match the normalized reporting-person name to the official master-index name for the XML submission-filer CIK.
5. Accept a candidate link only when exactly one reporting person matches within the filing.

Results:

| Sample | 13G filings | One unique filer-to-person name match | Ambiguous | No match |
|---|---:|---:|---:|---:|
| Target-subject | 213 | 203 (95.3%) | 2 | 8 |
| Non-target validation | 100 | 91 (91.0%) | 2 | 7 |

For single-reporting-person filings, the unique match rate was 120/125 (96.0%) in the target-subject sample and 48/53 (90.6%) in the non-target sample.

These are **candidate-link coverage rates, not measured precision**: the validation sample does not provide independent ground truth for the identity of every reporting person. The rule must be frozen and tested on separate quarters, with manual review of mismatches and ambiguous cases, before any imputed filer-to-person CIK can be used. In multi-person filings, identifying one filer does not identify the other persons or establish an economic group.

13G group markers are also incomplete: among original 13G filings, 34 had all markers missing, one had all persons marked “a”, and 14 had all persons marked “b”; among 13G/A filings, 107 had all markers missing, 11 had all “a”, 45 all “b”, and one mixed/partial case. A reporting-person-set fingerprint remains only a checksum, not a group key.

## Amendment lineage

| Form | Amendments | Explicit previousAccessionNumber | Missing |
|---|---:|---:|---:|
| SC 13D/A | 25 | 19 (76.0%) | 6 |
| SC 13G/A | 164 | 126 (76.8%) | 38 |

The 13D/A missing-pointer cases remain unresolved and require document-level investigation. The 13G/A schema allows the predecessor field to be optional. Where present, treat it as an explicit lineage pointer; do not assume it always points to the immediately preceding amendment. Only two predecessor links landed inside this quarter's target-subject sample; both matched the same subject issuer and submission filer as the amendment. The remaining links require a multi-quarter accession history.

The parser currently does not emit the 13G `amendmentNo` field. Add it before building a deterministic fallback lineage procedure. Missing pointers must remain unresolved unless a separately preregistered issuer + class/CUSIP + reporting-person identity rule yields exactly one predecessor.

All 242 target-subject event dates were parseable and no event date was later than its filing date in this sample. Nevertheless, event date is not KnowledgeDate. KnowledgeDate remains the master-index filing date; the signal date must be strictly later.

## Gates

| Gate | Status |
|---|---|
| 2025Q1 master-index discovery | PASS |
| Structured XML subject/filer role extraction | PASS for this pilot and its fixed validation sample |
| XML form agreement | PASS |
| Current candidate-CIK mapping | PARTIAL: 307/335; 27 unresolved |
| Historical active-universe membership | NOT TESTED |
| 13G reporting-person CIK/group identity | NOT PASSED |
| 13D/13G original-amendment lineage | NOT PASSED |
| Pre-structured-XML legacy HTML/TXT subject identity | NOT TESTED |
| Economic test / forward returns | NOT AUTHORIZED |

## Next work

1. Extend the pilot to separate 2025Q2 and 2025Q3 samples. Freeze the filer-to-reporting-person name-crosswalk rule before those validation runs.
2. Add and test `amendmentNo`; audit all missing 13D/A predecessor pointers and distinguish root accession from immediate prior amendment.
3. Extend the global master-index census across 2025Q2–Q4 and 2026Q1; preserve quarter-specific raw-index hashes and filing-date KnowledgeDates.
4. Develop a separate legacy HTML/TXT parser and verify subject CIK against filing-detail metadata for pre-structured-XML history. Do not project the 2025 XML result backwards.
5. Resolve the 27 candidate tickers and construct a PIT historical ticker/CIK/CUSIP/listing-status panel before claiming F80 universe coverage.
6. Only after those gates pass, normalize 13D and 13G mechanisms separately and execute the preregistered incremental test versus frozen LTM/F80.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No economic alpha claim, threshold selection, horizon selection, or portfolio change is permitted from this pilot.
