# Phase 330 — SEC legacy cover-page table feasibility pilot

**Date:** 2026-11-12 UTC  
**Status:** COMPLETED — visible ticker-table fallback rejected for this sample  
**Research class:** historical identity-source feasibility; no return or alpha test.

## Executive decision

The 25 Phase 328 primary documents that lacked target inline-XBRL facts were retrieved again and compared byte-for-byte with their Phase 328 source hashes. All **25/25 documents were retrieved and all 25/25 SHA-256 hashes matched**.

A conservative HTML table parser examined the documents for a cover-page column explicitly labelled Trading Symbol (including Trading Symbol(s)). Result: **0/25 documents contained such a table; 0 visible ticker symbols were extracted; 0 candidate matches were obtained.**

This rejects the proposed visible-cover-page ticker-table fallback for this selected sample. It does not prove that no ticker mention exists anywhere in the filing text; the parser intentionally did not infer a ticker from narrative prose, company names, exchange names or third-party mappings.

## Reproducibility

- GitHub Actions: [43219017019](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43219017019) — **SUCCESS**.
- Offline regressions: **12/12 passed**.
- Pinned manifest: [phase330 legacy cover-page manifest](phase330_legacy_coverpage_manifest.csv), SHA-256 fb069328bad9e648a85d25264f26cc2a31146d10e14003d004f9725184d30cc7.
- Input source: Phase 328 artifact 13943024635, ZIP SHA-256 ed33844f2b9ec435a6ee7eaacbe86fc7001a167efdc2300b65fb6f18f1c24dd8.
- Result artifact: [13945795442](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43219017019/artifacts/13945795442), ZIP SHA-256 ac58ac2ce8ce496b3f8b51108b0ee94092bb07aad196395d958aadc74e075dec.
- Only parsed table metadata, source hashes and summary files were uploaded; no raw SEC documents were uploaded.

The first test run failed only because the regression expected a different deterministic sort order for two symbols. The assertion was corrected; the final 12-test run passed before any SEC retrieval was attempted.

## Results

| Event year | Documents | Hash verified | Trading Symbol header | Symbols extracted |
|---|---:|---:|---:|---:|
| 2006 | 7 | 7 | 0 | 0 |
| 2012 | 15 | 15 | 0 | 0 |
| 2023 | 2 | 2 | 0 | 0 |
| 2026 | 1 | 1 | 0 | 0 |
| **Total** | **25** | **25** | **0** | **0** |

All 25 documents contained HTML tables, but none exposed the explicit Trading Symbol column sought by this parser. A missing symbol column is classified as unknown, not as proof that the filer has no listed security.

A direct example is Clearwire Corporation's 2011 Form 10-K, filed in February 2012. Its cover page identifies Class A Common Stock under Section 12(b) and says there are no Section 12(g) securities, but does not provide a trading-symbol column. The cover page later references the NASDAQ Global Select Market without stating the ticker in the registration table: [SEC original filing](https://www.sec.gov/Archives/edgar/data/1442505/000144530512000337/clwr1231201110-k.htm).

## Interpretation

1. The SEC periodic XBRL facts from Phase 328 and visible legacy cover-page tables from Phase 330 both fail the historical-coverage gate as stand-alone ticker crosswalks.
2. For Form 4 event-level research, the Form 4 XML itself remains the primary event record: Phase 326/327 retrieved 282 of 283 sampled originals, and all 282 retrieved XML issuerTradingSymbol values agreed with their bulk-index candidate. The single missing Riverview accession remains quarantined.
3. Form 4's issuer symbol and transaction securityTitle are useful event-level fields, but they do not independently prove the legal listing/share-class relationship. The CIK relationship graph and corporate-action ledger remain necessary.
4. A ticker parser must not promote an exchange name (e.g., NASDAQ/NYSE), a security title (e.g., Class A Common Stock), or a company name into a ticker.
5. The 25-document sample is purposive and selected specifically because Phase 328 found no target inline-XBRL facts. It is not a universe-prevalence estimate.

## Decision and next gate

- **Kill** the assumption that a visible cover-page Trading Symbol table can backfill these 25 missing-XBRL documents.
- Keep visible class title and exchange text as possible supplementary evidence, but do not treat it as a ticker or permanent security identifier.
- Next, use Form 4 XML's own issuerTradingSymbol and securityTitle as event-level attributes, then build an effective-dated relationship layer from intervening 8-K/8-K/A, mergers, spin-offs, name changes, listing/delisting notices and co-filer/parent/subsidiary relationships.
- For broader historical security identity, continue evaluating historical exchange/security-master sources. Current symbol directories are not point-in-time histories. Databento remains unlicensed; no vendor contact or purchase was made.
- Retain the 95% broad-coverage admission gate. No crosswalk or universe-coverage admission.

## Controls

- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- No alpha/return test, bootstrap/LOO, chronological OOS or holdout use.
- No production, universe, capital or parameter change.
- No vendor contacted, no data purchased, no email sent and no raw SEC bytes uploaded.
