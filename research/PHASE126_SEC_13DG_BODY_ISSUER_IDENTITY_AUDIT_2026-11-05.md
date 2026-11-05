# Phase 126 — SEC 13D/G body-first issuer identity audit

**Date:** 5 November 2026  
**Status:** PASS — artifact-only identity adjudication with legacy header exceptions.

## Result

The audit reprocessed the immutable Phase 124 sample and Phase 125 CUSIP artifact. It verified 600/600 raw submission hashes and accession/date identities, quarantined one SEC index alias, and adjudicated 599 actual 13D/G filings. There were no audit errors.

| Check | Result |
|---|---:|
| Actual 13D/G filings | 599 |
| Legacy HTML filings | 497 |
| Structured XML filings | 102 |
| XML issuer CIK = SEC-HEADER subject CIK | 102/102 |
| SEC-HEADER subject CIK present | 599/599 |
| Header subject CIK = filer CIK | 6/599 |

The 102/102 XML agreement is encouraging but sample-specific; it is not proof that the header role is universally correct.

## Two confirmed legacy header/body issuer discrepancies

1. **Seritage Growth Properties** — accession `0001549575-20-000008`. SEC-HEADER SUBJECT COMPANY and FILED BY both identify Dalal Street, LLC (CIK 1549575), while the 13G cover page identifies Seritage Growth Properties with CUSIP `81752R100`.
2. **Nano Mobile Healthcare, Inc.** — accession `0001903596-22-000671`. SEC-HEADER SUBJECT COMPANY identifies American Community Capital, LP. (CIK 1626837), FILED BY identifies Igwealor Frank I (CIK 1945609), while the cover page identifies Nano Mobile Healthcare, Inc. with CUSIP `63010B200`.

The Seritage example has an especially useful cross-filing control: accession `0001193125-21-208169` identifies Seritage in both the header and cover page with the same CUSIP `81752R100`, but its header subject CIK is 1628063 rather than 1549575. The same cover-page issuer/CUSIP therefore appears with two different SEC-HEADER subject CIKs.

## Rename control — not a mismatch

Accession `0001172661-24-001310` was initially treated as another possible discrepancy. The SEC header shows subject CIK 1578987, current name ArrowMark Financial Corp., and former conformed name StoneCastle Financial Corp. The cover page still says StoneCastle Financial Corp.; CUSIP is `861780104`. The filer CIK is 1483859. This is a same-CIK historical name change, not an issuer-role error.

The parser initially prefixed a standalone “COMMISSION” line to the cover-page name. The parser now excludes that boilerplate, and the regression suite covers it.

## Interpretation

- SEC-HEADER SUBJECT COMPANY CIK cannot be the sole issuer locator for legacy HTML 13D/G.
- Body cover-page issuer name and CUSIP/class information are necessary cross-checks for legacy submissions.
- These are two hand-adjudicated exceptions plus one rename control, not an estimate of the global header-error rate.
- Structured XML issuer CIK matched the header subject CIK in all 102 sampled XML filings.

## Limits and decision

CUSIP is not permanent and requires effective-dated corporate-action, share-class, ADR, successor and delisting-aware mapping. The 600-row sample is drawn from a filing index, not a historical eligible-security universe; no inferential confidence interval is claimed. Only four legacy cover pages were manually adjudicated; no broad body-issuer parser has been promoted.

No forward returns, alpha tests, paid data, vendor contacts, or production changes were performed. **Phase 126 passes identity-exception adjudication, not the permanent security-identity or PIT gates.** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Reproducibility

- [Phase 126 Actions run](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42079214500)
- Artifact: `13438773715`, SHA-256 `24b5795afa6cd0d858345976cfa29410c887f7ff79ababda4b0951ba86bdee53`
- [Auditor](phase126_sec_13dg_body_issuer_identity_audit.py)
- [Tests](test_phase126_sec_13dg_body_issuer_identity_audit.py)
