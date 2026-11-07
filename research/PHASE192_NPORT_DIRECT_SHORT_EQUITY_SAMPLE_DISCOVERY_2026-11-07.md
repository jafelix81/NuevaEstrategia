# Phase 192 — SEC N-PORT direct short-equity row discovery

**Audit date:** 2026-11-07  
**Disposition:** DISCOVERY_PASS_RAW_RETRIEVAL_PENDING  
**Scope:** purposive source/schema discovery only; no returns or alpha test.

## Executive result

Phase 191 established that the current N-PORT schema has a non-derivative payoff-profile field but did not verify an actual short-equity row. Phase 192 materially advances that gate: SEC-hosted, search-indexed `primary_doc.xml` excerpts expose **11 complete direct-short common-equity row excerpts across four accessions (2020, 2022, 2024 and 2025)**, plus one partial 2023 filing excerpt.

The complete excerpts consistently show `payoffProfile=Short`, `assetCat=EC` (equity-common), `issuerCat=CORP`, `invCountry=US`, share units (`NS`), negative balance, negative USD value and negative percentage of net assets.

Examples include GPS, COTY, TEX and OXY in the 2020 accession; CARR, CAT, CVX and CTAS in 2022; KMX and EQT in 2024; and a 2025 row with CUSIP 31428X106, balance -141,878 shares and reported value -USD 34.59 million. The 2023 excerpt confirms the Short/EC/CORP/US field combination, but the issuer/security fields were not captured and it is not counted among the 11 complete rows.

This is meaningful evidence that the proposed variable exists in actual historical filings—not just in form instructions. It is **not** evidence that the positions are informed directional bets, nor that the signal predicts returns.

## Evidence and source discipline

The sample is purposive and discovery-driven, not random. Filing year is taken from the accession; report dates are not inferred. The SEC-hosted XML URLs are recorded in the machine-readable evidence ledger.

Three SEC archive-directory listing timestamps were also observed (2020-08-21 12:55:43; 2023-09-29 14:46:20; 2025-05-28 16:04:35). These strings are retained only as directory observations. Their timezone and relationship to the authoritative acceptance timestamp were not reconciled, so they are **not** used as PIT availability times.

**Important retrieval limitation:** the full raw XML files could not be retrieved and hashed in this phase. The current evidence is search-indexed excerpts of SEC-hosted XML, not a deterministic parse of complete filing bytes. The phase therefore does not claim raw-file integrity, full filing identity, or amendment lineage.

## Narrow interpretation

The first economic hypothesis remains limited to direct non-derivative common-equity short exposure. It excludes derivatives, debt, preferred equity, non-corporate issuers and non-US investment-country rows. Even `invCountry=US` does not prove a US-listed ordinary common share; an effective-dated listing/security crosswalk is still required.

A reported short may represent hedging, arbitrage, relative value, liquidity management or a directional view. Do not call this short interest, securities-lending volume, a named hedge-fund book or “smart money” without qualification.

The earlier Phase 27O long-side share-accumulation dose-response remains killed in its tested form. Its results are neither reused nor treated as evidence against this separate short-exposure hypothesis.

## Admission gates

| Gate | Phase 192 result |
|---|---|
| Actual SEC XML short-row discovery | PASS — purposive excerpts |
| Full raw XML retrieval and SHA-256 | NOT VERIFIED |
| Deterministic full-filing parser | NOT VERIFIED |
| SEC-HEADER / filing-index acceptance-time reconciliation | NOT VERIFIED |
| Append-only NPORT-P/A version ledger | NOT VERIFIED |
| Fund-series / share-class deduplication | NOT VERIFIED |
| Historical CUSIP-to-listing crosswalk | NOT ESTABLISHED |
| Active and delisted security universe | NOT ESTABLISHED |
| Broad PIT universe admission | NOT ADMITTED |
| Incremental alpha versus frozen LTM/F80 | NOT AUTHORIZED |

## Next gate

1. Retrieve the complete raw XML and filing-index record for the five accession discoveries, retaining immutable bytes, SHA-256, accession, form, filing date, report date and SEC-HEADER acceptance timestamp.
2. Parse every `invstOrSec` node deterministically. Reconcile payoff profile, asset category, issuer category, country, balance, units, currency value, percentage, CUSIP, ISIN and ticker against the SEC bulk tables and the filing itself.
3. Add a stratified sample of NPORT-P/A amendments. Preserve every accession as an append-only version; never backdate a corrected holding.
4. Resolve `SERIES_ID` as the portfolio unit (not registrant CIK or share class), then test identifier continuity and listing status against an effective-dated historical security master, including delisted/relisted names.
5. Only after those gates pass, preregister changes in short exposure and breadth of funds opening/increasing versus reducing/covering positions. Control for prior returns, liquidity, volatility and options flow. Compare stock-return and, if appropriate, option-return outcomes separately against frozen LTM/F80 using chronological validation, identical exposure/costs, block/cluster bootstrap, leave-one-fund/issuer-out and an untouched prospective holdout.

**Controls:** no raw bulk archive download; no raw XML hash; no prevalence estimate; no return/alpha test; no bootstrap/LOO; no holdout use; no production or universe change; no data purchase or vendor contact. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Official SEC filing evidence

- [2020 NPORT-P primary XML — accession 0001752724-20-163166](https://www.sec.gov/Archives/edgar/data/1408970/000175272420163166/primary_doc.xml)
- [2022 NPORT-P primary XML — accession 0001145549-22-056239](https://www.sec.gov/Archives/edgar/data/1511699/000114554922056239/primary_doc.xml)
- [2023 NPORT-P primary XML — accession 0001145549-23-060491](https://www.sec.gov/Archives/edgar/data/811030/000114554923060491/primary_doc.xml)
- [2024 NPORT-P primary XML — accession 0001145549-24-075135](https://www.sec.gov/Archives/edgar/data/1000351/000114554924075135/primary_doc.xml)
- [2025 NPORT-P primary XML — accession 0001145549-25-033457](https://www.sec.gov/Archives/edgar/data/1467631/000114554925033457/primary_doc.xml)
- [SEC Form N-PORT Data Sets](https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets)
- [SEC N-PORT Data Sets Readme](https://www.sec.gov/files/nport_readme.pdf)
