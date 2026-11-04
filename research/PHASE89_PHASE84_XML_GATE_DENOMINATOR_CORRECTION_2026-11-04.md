# Phase 89 — Phase 84 XML-gate denominator correction and offline replay

**Date:** 2026-11-04  
**Branch:** phase89-phase84-xml-gate-correction  
**Source run:** [41914491120](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41914491120)  
**Source artifact:** phase84-13dg-role-aware-identity-validation, artifact 13364856424  
**Artifact SHA-256:** b807be9099e1a777c232f6d50b341e8e714585dc4da5fe993e833c2051494b16

## Finding

The Phase 84 live retrieval completed all 600/600 SEC submissions with zero fetch errors. The workflow exited with code 2 because one record was incorrectly included in the mandatory Schedule 13D/13G XML denominator.

Accession 0001104659-26-057293 was labelled SC 13D/A in the master-index candidate row, so its inherited form_family=13D placed it in the mandatory-XML timing regime. The actual SEC-HEADER identifies the submission as SC TO-T/A (a tender-offer filing), not a Schedule 13D/13G. It should not be counted as a mandatory Schedule 13D/13G XML filing. The parser had correctly preserved the actual header form; the denominator used the wrong field.

The original run and artifact are preserved unchanged. The correction uses the actual SEC-HEADER form and filing date whenever the submission was retrieved. For an unretrieved submission, it conservatively falls back to the master-index form/date so a failed retrieval cannot disappear from the denominator.

## Recomputed Phase 84 evidence from the saved 600-filing artifact

| Check | Result |
|---|---:|
| Complete submissions retrieved | 600/600 |
| Fetch errors | 0 |
| Subject CIKs in the 319-CIK target set | 224 |
| Target subject CIKs present in index/path candidate set | 224/224 |
| Target subject candidate misses | 0 |
| Candidate-target accessions | 367 |
| Unique-candidate rows | 232 |
| Unique-candidate rows resolved to target subject | 89/232 (38.36%) |
| Index-ambiguous rows resolved to target subject | 135/135 |
| Filer-only candidate false positives | 143/367 (38.96%) |
| Unresolved candidate rows | 0 |
| XML documents parsed | 200 |
| XML subject/header concordance | 200/200 |
| XML filer/header concordance | 200/200 |
| Actual mandatory Schedule 13D/G XML | 192/192 present |
| SEC-HEADER acceptance timestamps | 600/600 valid |
| Raw-file SHA-256 and retrieval UTC | 600/600 valid |
| HTTP 200 | 600/600 |

Accession, filing-date and form concordance were 100%, 100% and 99.83%, respectively. The single form mismatch is the same tender-offer record; overall form concordance remains above the preregistered 99.5% threshold.

The previous Phase 84 denominator was 193 and counted 192 XML documents (99.48%), narrowly failing the 99.5% gate. The corrected, form-aware denominator is 192 and all 192 required XML documents are present (100%). This is a denominator correction, not a relaxation of the threshold.

## Candidate-population estimate

The Phase 83/84 post-stratified descriptive estimate remains approximately 52.06% target-subject accessions and 47.94% filer-only false positives among 34,400 candidate accessions. It has no inferential confidence interval and is a feasibility estimate only. It must not be represented as a population-parameter estimate or evidence of predictive behavior.

## Interpretation and boundary

The corrected pilot supports the proposition that global master-index/archive-path CIK pairs can discover target-subject filings for the current 319-CIK candidate list, provided the SEC-HEADER SUBJECT COMPANY and FILED BY roles are parsed separately. Candidate CIK overlap alone is not enough: approximately 39% of candidate-target rows in this sample were filer-only.

This is not an alpha result. The following remain hard gates:

1. Historical ticker/CIK/security continuity and point-in-time active-universe membership. The 319 current CIK candidates do not reconstruct the original 335-name F80 selection rule or historical membership.
2. Deterministic predecessor/amendment chain reconstruction using exact accession links, with original events separated from amendments and corrected event dates retained as disclosures rather than silently overwriting prior knowledge.
3. Reporting-person and group normalization; multiple filers and joint-filing groups must not be collapsed into a single institution without evidence.
4. Separate 13D and 13G hypotheses. Neither form nor a filer label is proof of informed trading.
5. Conservative knowledge time: acceptance datetime is converted from America/New_York to UTC; absent independently verified dissemination time, signals must become usable no earlier than the next regular session.

No forward returns, feature tuning, alpha inference, vendor purchases or production changes were performed. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Reproduction

The Phase 89 workflow downloads the immutable Phase 84 artifact and replays all 600 saved raw submissions offline. It verifies raw SHA-256 hashes, parser reproducibility, header/XML concordance and the corrected XML denominator. It performs no SEC network requests and uses no forward returns.


## Replay implementation note

The first offline replay attempt passed all 27 regression tests and verified the source artifact digest, but stopped before producing a summary because the prior weighted-estimate summary stores combined Phase 83/84 counts rather than the Phase 83-only fields. The replay now reads the frozen Phase 83 per-stratum role-count file directly and the Phase 82 population stratum counts from the original summary. No SEC requests were repeated; this was a replay-input schema correction only.
