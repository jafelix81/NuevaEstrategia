# Phase 126 — SEC 13D/G body-first issuer identity audit

**Date:** 2026-11-05  
**Status:** PASS — artifact-only identity adjudication  
**Workflow:** [42079214500](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42079214500)

## Source integrity

Phase 126 reconciled the immutable Phase 124/125 artifacts. All 600 raw SHA-256/accession/date checks passed. The sample contains 599 actual 13D/G submissions and one non-13D/G SEC TO-T/A index alias, quarantined from the 13D/G population. There were no new SEC requests.

The sample contains 497 legacy HTML and 102 structured XML filings. In the 102 XML rows, structured issuerCik matched the SEC-HEADER subject CIK in 102/102 cases. This supports a conditional XML path; it is not a universal validation.

## Two concrete legacy header/body issuer discrepancies

1. **Seritage / Dalal Street — accession 0001549575-20-000008.** The SEC-HEADER SUBJECT COMPANY and FILED BY both identify Dalal Street, LLC (CIK 1549575). The 13G cover page identifies Seritage Growth Properties and CUSIP 81752R100. A second filing, 0001193125-21-208169, carries the same body issuer and CUSIP but header subject CIK 1628063. This cross-filing anchor confirms that the first filing's header subject CIK cannot be treated as the issuer CIK.

2. **Nano Mobile / American Community Capital — accession 0001903596-22-000671.** The SEC-HEADER subject is American Community Capital, LP (CIK 1626837), and the filer is Igwealor Frank I (CIK 1945609). The 13D cover page identifies Nano Mobile Healthcare, Inc. and CUSIP 63010B200. The header has no former-company entry linking these names.

These are hand-adjudicated examples, not an estimate of the global header-error rate. The fact that a header subject CIK appears in the index/archive path does not prove that it is the issuer.

## Historical rename control — not an error

Accession 0001172661-24-001310 has header subject ArrowMark Financial Corp (CIK 1578987), with FORMER COMPANY recorded as StoneCastle Financial Corp. The 13G cover page still names StoneCastle Financial Corp and CUSIP 861780104. This is a valid historical name change under the same issuer CIK, not a subject/filer role mismatch. The filer CIK is 1483859.

This control is important: body/header name differences must not be counted as errors without checking former names, series/trust structure and corporate actions.

## Decision

> The manual legacy cases and Seritage cross-filing remain valid. Phase 126 used the pre-correction Phase 125 artifact; Phase 127 subsequently corrected XML CUSIP extraction. The XML issuerCik checks in Phase 126 are unaffected, and all hand-adjudicated CUSIPs are legacy cover-page values unchanged by Phase 127.

- Do not use legacy SEC-HEADER SUBJECT COMPANY CIK as an authoritative issuer CIK or as issuer-universe coverage.
- For legacy HTML, use body cover-page issuer name plus cover-page CUSIP as the starting identity; retain header subject/filer CIKs as separate provenance fields.
- For XML, use structured issuerCik only where present and validated.
- Require an effective-dated CUSIP/security crosswalk that handles share classes, ETF series, ADRs, renames, splits, mergers and delistings before joining returns.
- Preserve SEC acceptance timestamp separately from event date; the first tradable session after verified acceptance remains the conservative public-knowledge convention.

Only two discrepancies and one rename control were manually adjudicated; no broad automated body-issuer parser was promoted. No forward returns, alpha tests, vendor purchases or production changes were performed. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
