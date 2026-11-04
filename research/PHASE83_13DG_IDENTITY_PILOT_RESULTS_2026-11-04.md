# Phase 83 — SEC 13D/13G subject/filer identity pilot results

**Date:** 2026-11-04  
**Branch:** phase82-13dg-global-index-coverage-audit  
**Run:** [41893546069](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41893546069)  
**Artifact:** [13353988656](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41893546069/artifacts/13353988656)  
**Artifact ZIP SHA-256:** `8257ee70811f07ab5ae933c1a86e524b290622e832594b69d0b53f3ec0fdf74d`

## Decision

**The preregistered Phase 83 data gate failed.** Do not reinterpret this as a parser failure and do not retroactively relax the gate. The failure is specifically that a *unique current-universe CIK hit in the unlabelled index/path pair is not necessarily the subject issuer*. The header identifies the roles and exposes a workable role-aware resolution hypothesis, which Phase 84 will validate on a larger disjoint sample.

No forward returns, alpha test, feature selection or production change was performed.

## Results

| Check | Result |
|---|---:|
| Stratified complete submissions | 120/120 |
| Fetch/parse errors | 0 |
| SEC header parse rate | 100% |
| Accession/form/filing-date concordance | 100% |
| Subject and filer CIK presence | 100% |
| Subject CIK present in master-index or archive-path CIK set | 100% |
| Structured XML rows | 40 |
| XML issuer = header SUBJECT COMPANY | 40/40 |
| XML filer = header FILED BY | 40/40 |
| Raw complete submissions saved | 120/120 |
| Header ACCEPTANCE-DATETIME present and parseable | 120/120 |

The sample was balanced across 13D/13G, originals/amendments, timing regimes, and index candidate/control classes: 44 unique-candidate, 32 ambiguous and 44 control accessions.

### Why the preregistered gate failed

Among 44 unique-candidate accessions:
- 11/44 (25%) had the candidate CIK in the SEC header SUBJECT COMPANY role.
- 33/44 (75%) had the candidate CIK only in the FILED BY role. These are filer-only false positives for issuer-event discovery.

Among 32 ambiguous accessions:
- 32/32 contained a current-universe CIK in the subject role.
- These accessions also had a current-universe CIK in the filer role; the header is required to distinguish both.

Across all 76 candidate accessions, 43 contained a current-universe subject CIK, 33 were filer-only false positives, and 32 contained both a subject and a filer CIK from the current candidate set. All candidate CIKs in the sample were attributable to header subject/filer roles; no unresolved candidate CIK remained.

The result confirms that the master-index CIK and archive-path CIK are **candidate locators only**. A unique CIK hit must never be promoted to issuer identity without the SEC header role.

## Timestamp and PIT boundary

All 120 SEC headers contained a 14-digit ACCEPTANCE-DATETIME. The artifact preserves raw submission bytes, SHA-256 and UTC retrieval time. The acceptance value is an Eastern wall-clock timestamp; it must be converted using America/New_York daylight-saving rules. Phase 83 did not independently verify public dissemination latency. Any later economic test must use a conservative next-session availability rule unless exact public availability is separately established.

## Interpretation

Phase 83 validates the parser and subject/filer role extraction on this sample, but **does not pass the preregistered unique-candidate identity gate**. It does not establish historical F80 membership, historical ticker-to-CIK lineage, universe coverage or alpha.

The role-aware hypothesis is narrower: if the subject CIK is reliably present in the global index/path candidate set, complete-submission SEC headers can separate true subject-issuer filings from filer-only false positives. Phase 84 is designed to test that hypothesis on 600 new, disjoint observations, preserving the original Phase 83 result.

## Next gate

Phase 84 will use a 600-filing hash-stratified sample from the frozen Phase 82 index artifact, excluding all 120 Phase 83 accessions. It will separately test:
1. Subject-target recall in the master-index/archive-path candidate set.
2. Subject/filer role resolution and the filer-only false-positive rate.
3. Header accession/form/date concordance and acceptance timestamp conversion.
4. Mandatory structured XML presence and issuer/filer concordance.
5. Raw bytes, SHA-256 and UTC retrieval reproducibility.

A passing Phase 84 gate authorizes only the next historical subject-side coverage and event-normalization audit. It does not authorize forward-return testing or production use.
