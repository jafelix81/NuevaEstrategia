# Phase 125 — SEC 13D/G cover-page CUSIP identity audit

**Date:** 2026-11-05  
**Status:** PASS — artifact-only feasibility audit  
**Workflow:** [42077788015](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42077788015)

## Scope and method

Re-audited the 599 actual 13D/G submissions from the Phase 124 hash-stratified sample; the one SEC TO-T/A index alias was excluded. The workflow consumed immutable Phase 124 artifacts and made no new SEC requests.

The legacy HTML parser now extracts only the first CUSIP value associated with the primary cover-page CUSIP label. It handles split HTML text nodes and CUSIP No., CUSIP Number and CUSIP Number(s) variants. CUSIPs appearing later in narrative, exhibits or amendment history are intentionally not used to fill a missing cover-page value. XML all-zero 000000000 is classified separately as a placeholder.

## Results

| Source | Rows | Unique checksum-valid | Checksum-invalid | Missing | Placeholder | Weighted valid coverage |
|---|---:|---:|---:|---:|---:|---:|
| Legacy HTML | 497 | 473 | 1 | 23 | 0 | 96.84% |
| Structured XML | 102 | 68 | 1 | 32 | 1 | 66.71% |
| **Total** | **599** | **541** | **2** | **55** | **1** | **91.36%** |

The 541 valid rows contain 524 distinct checksum-valid CUSIP strings. There are 525 (header_subject_cik, CUSIP) pairs because CUSIP 81752R100 appears with two different header subject CIKs. Phase 126 determines that both filings identify Seritage Growth Properties in the body, so the header-CIK collision is an issuer-role problem, not two securities.

The two checksum-invalid values are 584680106 (legacy HTML) and 50214C200 (XML). They remain quarantined; checksum failure is not repaired by guesswork. The one XML placeholder is 000000000.

## Methodological correction

The previous whole-document scan produced six ambiguous rows by combining cover-page CUSIPs with later CUSIPs from the filing body/exhibits, and one false token (SAUGUST26) from a CUSIP Number(s) layout. Restricting extraction to the primary cover page resolved the six multi-CUSIP cases, recovered split-node values, and removed the false token. This is the correct security-identity scope for the filing's cover page.

## Decision and limitations

- CUSIP coverage is now strong enough to proceed to an identity-crosswalk audit, not to a return test.
- CUSIP is not permanent. A valid checksum does not prove the issuer, share class, ticker, active listing, or historical tradability.
- Header subject CIK is not an authoritative issuer key for all legacy HTML 13D/G; Phase 126 confirms concrete exceptions.
- The sample is hash-stratified by filing-index strata. Weighted coverage is descriptive; no inferential confidence interval is claimed.
- No forward returns, alpha tests, vendor purchases or production changes. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
