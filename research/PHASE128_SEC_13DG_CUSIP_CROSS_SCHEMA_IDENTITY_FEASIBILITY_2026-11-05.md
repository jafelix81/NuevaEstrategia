# Phase 128 — SEC 13D/G CUSIP cross-schema identity feasibility

**Date:** 5 November 2026  
**Status:** PASS — artifact-only cross-schema identity audit validated by GitHub Actions.

## Question

Can the filing sample itself provide enough repeated CUSIP links between legacy HTML and structured XML to build an internal issuer/security identity bridge, without a licensed security master?

## Immutable inputs

- Phase 124 sample: run `42073725379`, artifact `13436764625`, SHA-256 `85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc`.
- Phase 127 corrected CUSIP audit: run `42079517644`, artifact `13438903901`, ZIP SHA-256 `b80d15d736ba6c45f4f3c5dd569604175e221414b31a28fd58a62010a805c166`.
- No new SEC requests are required.

## Preliminary results

The 599 actual filings contain 571 unique checksum-valid CUSIP rows representing 553 distinct valid CUSIPs. Eighteen CUSIPs repeat across multiple filings:

| Repeated-group source mix | Groups |
|---|---:|
| Legacy HTML only | 14 |
| Structured XML only | 2 |
| Legacy HTML + XML | 2 |
| Total | 18 |

Only two of 553 unique valid CUSIPs (0.36%) bridge legacy HTML and structured XML:

- `90290N109`: USA Compression Partners, LP; legacy 2017Q1 and XML 2025Q3; subject/issuer CIK 1522727 and normalized issuer names agree.
- `G38644103`: GigaCloud Technology Inc; legacy 2024Q4 and XML 2026Q2; subject/issuer CIK 1857816 and normalized issuer names agree.

A separate legacy-only group, `81752R100`, contains two Seritage Growth Properties cover pages with the same CUSIP and body issuer name but different SEC-HEADER subject CIKs (1549575 and 1628063). This reproduces the Phase 126 legacy header-role exception.

## Legacy body-name parser probe — not promoted

The current heuristic returns candidate issuer names for 442/497 legacy filings (88.9% apparent yield). However, 82 of those candidates contain obvious separator or boilerplate contamination (including dashed/underscored rules, SEC heading text, “1934”, amendment text, converter text or address/footer fragments). The remaining 360 candidates are still unvalidated; they are not a reliable 72.4% coverage claim. The parser remains exploratory and is not promoted as an identity source.

## Decision

The SEC filing sample provides two clean cross-schema CUSIP/issuer identity links, which are useful controls but far too sparse to create a historical security master. The Seritage group separately confirms that legacy SEC-HEADER subject CIK can be wrong even when body issuer name and CUSIP are consistent.

Do not infer historical ticker identity from header CIK or CUSIP alone. Continue only if an effective-dated external/permanent security crosswalk can be obtained without unapproved data purchases, or if a sufficiently broad independent public crosswalk is found. The current internal SEC filing overlap is insufficient for broad 2016–2026 issuer/security mapping.

No forward returns, alpha tests, vendor purchases, vendor contacts or production changes were performed. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Reproducibility

- [Phase 124 source sample](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42073725379)
- [Phase 127 corrected CUSIP audit](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42079517644)
- [Phase 128 auditor](phase128_sec_13dg_cusip_cross_schema_identity_audit.py)
- [Regression tests](test_phase128_sec_13dg_cusip_cross_schema_identity_audit.py)


- [Phase 128 Actions run](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42080440140)
- Artifact: `13439559366`; ZIP SHA-256 `aed19dba803bd47f9ac6a846807d93a778b05bad3cf637c18936e1d3593fb22b`.
- Final CI: 15 Phase 124 tests, 21 Phase 125 tests, 7 Phase 126 tests and 9 Phase 128 tests passed; 600/600 raw hashes verified; no audit errors.
