# Phase 485 — SEC 13D/G index-header subject/filer identity parser

**Date:** 2026-11-18  
**Purpose:** turn the Phase 484 identity finding into a fail-closed parsing rule without making live SEC requests.

## New source-level confirmation

The SEC accession index-header for 0000895421-24-000178 contains separate blocks:

- SUBJECT COMPANY: abrdn Global Infrastructure Income Fund, CIK 0001793855.
- FILED BY: Morgan Stanley, CIK 0000895421.
- ACCEPTANCE-DATETIME: 20240212095001.

Official SEC source: [index-headers.html](https://www.sec.gov/Archives/edgar/data/1793855/000089542124000178/0000895421-24-000178-index-headers.html).

This is stronger than relying on the primary Schedule 13G body alone. The header explicitly separates the subject issuer from the filer and provides the CIKs in structured metadata.

## Parser behavior

Added a pure offline parser that:

1. Extracts the SEC-HEADER payload.
2. Separates SUBJECT COMPANY and FILED BY blocks.
3. Extracts each block's company name and CENTRAL INDEX KEY independently.
4. Cross-checks FILED BY CIK against the accession prefix.
5. Returns a verified subject/filer identity only when both blocks are present, both CIKs are valid, and the filer CIK matches the accession.
6. Never infers a ticker from a CIK; ticker mapping remains a separate effective-dated CUSIP/security-master task.
7. Quarantines missing, duplicate, malformed or mismatched identity blocks.

## Validation scope

The new tests use a compact fixture transcribed from the public SEC index-header structure and exercise missing blocks, missing CIKs, duplicate blocks, invalid accession and filer/accession mismatch. No live SEC API request, raw filing capture, price request or market-data artifact is produced.

## Research decision

This parser is a necessary building block, not a completed rebuild of all 20,266 rows. Phase 28D/35 remains quarantined until the original accession set is reprocessed through the SEC index-header subject/filer blocks and a point-in-time security/CUSIP mapping. Do not use the existing stored ticker or queried CIK as a substitute.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No event study, return test, backtest, OOS, bootstrap or LOO was run.
