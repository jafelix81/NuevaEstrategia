# Phase 161 — SEC 13D/G previousAccessionNumber one-to-many semantics audit

**Date:** 2026-11-06  
**Status:** COMPLETED — targeted public-XML counterexample; Phase 160 parent interpretation superseded  
**Scope:** Determine whether a structured filing's \`previousAccessionNumber\` can be treated as an issuer/security-level parent without inspecting the referenced submission.

## Executive finding

A targeted set of eight public SEC Schedule 13G/A XML filings reuses the exact same \`previousAccessionNumber\`:

\`0001445546-21-002430\`

The eight child filings span **five distinct issuer CIKs and eight distinct CUSIPs**. Four child records refer to different series/classes under First Trust Exchange-Traded Fund VIII (issuer CIK 0001667919); the remaining records include Morgan Stanley Emerging Markets Domestic Debt Fund, abrdn Australia Equity Fund, Winmark Corporation and BNY Mellon Strategic Municipal Bond Fund.

This is a direct counterexample to treating the field as a unique issuer/security parent pointer. It may be a reused common anchor, a filer/workflow-level reference, or a malformed/stale value; this audit does not infer which explanation is correct. The referenced 2021 submission itself has not yet been inspected.

**Decision:** retain \`previousAccessionNumber\` as provenance and an accession-level reference only. Do not use it alone to collapse filings, construct issuer amendment chains, or backdate ownership state. Parent continuity remains unverified until the referenced document's SEC header/XML and effective-dated security identity are compared with each child.

## Targeted source sample

| Child accession | Issuer CIK | Issuer | Security class | CUSIP |
|---|---|---|---|---|
| 0001445546-25-002780 | 0001667919 | First Trust Exchange-Traded Fund VIII | FT Vest U.S. Small Cap Moderate Buffer ETF - November | 33740F342 |
| 0001445546-25-002771 | 0000904112 | Morgan Stanley Emerging Markets Domestic Debt Fund, Inc. | Common | 617477104 |
| 0001445546-25-002779 | 0001667919 | First Trust Exchange-Traded Fund VIII | FT Vest U.S. Small Cap Moderate Buffer ETF - May | 33740F466 |
| 0001445546-25-004973 | 0001667919 | First Trust Exchange-Traded Fund VIII | FT Vest U.S. Equity Deep Buffer ETF - September | 33740F680 |
| 0001445546-26-007700 | 0001667919 | First Trust Exchange-Traded Fund VIII | FT Vest U.S. Equity Moderate Buffer ETF - November | 33740U687 |
| 0001445546-26-008202 | 0000779336 | abrdn Australia Equity Fund, Inc. | Common | 003011111 |
| 0001445546-26-008249 | 0000908315 | Winmark Corporation | Common | 974250102 |
| 0001445546-26-008161 | 0000855887 | BNY Mellon Strategic Municipal Bond Fund, Inc. | Common | 09662E109 |

All eight official SEC XML documents show the same \`previousAccessionNumber\`. Source URLs are preserved in the fixture:
- https://www.sec.gov/Archives/edgar/data/1184765/000144554625002780/primary_doc.xml
- https://www.sec.gov/Archives/edgar/data/904112/000144554625002771/primary_doc.xml
- https://www.sec.gov/Archives/edgar/data/1184765/000144554625002779/primary_doc.xml
- https://www.sec.gov/Archives/edgar/data/1667919/000144554625004973/primary_doc.xml
- https://www.sec.gov/Archives/edgar/data/1184765/000144554626007700/primary_doc.xml
- https://www.sec.gov/Archives/edgar/data/779336/000144554626008202/primary_doc.xml
- https://www.sec.gov/Archives/edgar/data/1184765/000144554626008249/primary_doc.xml
- https://www.sec.gov/Archives/edgar/data/1184765/000144554626008161/primary_doc.xml

The sample is targeted, not random. It demonstrates reuse and invalidates an unconditional one-to-one interpretation; it does not estimate how often the problem occurs across all 13D/G amendments.

## Reconciliation to Phase 160

Phase 160 correctly established that 30 of 32 sampled accession strings were present in the 43-quarter global master index, with one additional match after canonical zero-padding. It also correctly recorded filing-family/date checks and candidate-CIK overlap.

However, index presence and candidate-CIK overlap do **not** prove that the referenced accession is the predecessor for the same issuer/security. In the counterexample above, the same reference is reused across unrelated issuer CIKs and distinct securities.

Therefore:
- Keep the 30/32 result as an accession-reference lookup result only.
- Supersede the phrase “primary explicit parent pointer” as an issuer/security-level conclusion.
- Reclassify the single Phase 160 subject-CIK mismatch as an unresolved role/identity exception, not the only possible continuity issue.
- Do not reconstruct amendment state from the previous accession field alone.

The 32 values were unique **within the Phase 124 sampled child set**. That local uniqueness does not establish global uniqueness or issuer-level uniqueness.

## Conservative state-machine rule

A child filing can be linked to a parent filing for issuer/security-state reconstruction only after:
1. The referenced accession document is retrieved and its issuer/subject CIK is parsed from the document, not inferred from the accession prefix or master-index candidate CIKs.
2. The child and parent issuer identities agree, or an independently sourced legal-entity continuity record explains the difference.
3. The security class/CUSIP agrees, or an effective-dated corporate-action/security-master bridge explains the transition.
4. The parent filing family and acceptance chronology are consistent.
5. The amendment's legal effect (restatement, add-only, confidentiality release, or other correction) is independently classified.

A same-issuer/same-CUSIP match is only a continuity candidate; it is not proof that the disclosed positions are comparable after splits, mergers, class changes or other corporate actions. Until all gates pass, retain the pointer as a raw reference and quarantine state transitions.

## CI and reproducibility

- Targeted fixture: eight SEC XML source records embedded in \`research/phase161_13dg_previous_accession_semantics_audit.py\`.
- Offline tests: 14 deterministic unit tests.
- No SEC download, vendor request, price/return data, forward-return test, bootstrap/LOO, OOS test, or final-holdout access.
- No production or F80 change.

## Next gate

Inspect accession \`0001445546-21-002430\` and compare its actual subject/security scope against the eight children. If the source remains inaccessible under the repository's declared SEC User-Agent policy, use only a permitted, reproducible retrieval route; do not infer the parent from index CIKs or a third-party summary.



## Final CI execution

- Final-head run: [42258657865](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42258657865), commit `2297a44abfcd5f4ee4842e92e801bedb0ae73865`.
- Job `audit`: success; Python compilation passed; **14/14 offline regression tests passed**; targeted audit recomputed; artifact [13523024322](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42258657865/artifacts/13523024322) uploaded (SHA-256 `3e6b1996d1736ecac3874796abc10b3d1ed7e48841d0a68b1b81c65457265125`).
- No external SEC request was made by this workflow; the eight source records are a targeted public-XML fixture.
