# Phase 217 — SEC N-PORT full-submission-text direct-short row pilot

**Audit date:** 2026-11-08  
**Disposition:** `FULL_SUBMISSION_TEXT_ROW_PILOT_PASS_RAW_HASH_PENDING`  
**Scope:** one public NPORT-P filing; line-referenced source verification only. No returns or alpha test.

## Executive result

Phase 192 found direct-short common-equity rows in search-indexed excerpts from five accessions, but none of the complete raw XML files had been retrieved or hashed. This phase advances one of those accessions — **0001145549-25-033457** — by inspecting the SEC-hosted complete submission text file, which embeds the primary NPORT-P XML.

The filing is **ACAP Strategic Fund**, registrant CIK 0001467631, for period **2025-03-31**. The SEC filing index lists the complete submission text at 238,101 bytes and the primary XML at 236,779 bytes. The SEC header records acceptance at **2025-05-28 16:04:35 ET**. The report-to-filing lag is **58 calendar days**. The first full regular session after the acceptance timestamp is **2025-05-29**, a conservative candidate daily boundary, but first public receipt is not independently captured.

I verified **23 selected, line-referenced** non-derivative common-equity short rows. Each selected row has:
- `title=Common Stock`, `units=NS`, `payoffProfile=Short`;
- `assetCat=EC`, `issuerCat=CORP`, `invCountry=US`;
- a nine-character CUSIP;
- negative share balance, USD value and percentage of fund net assets.

This is not an exhaustive parse of every holding and is not a representative sample. The 23 rows were selected across the complete text by source line range.

## Selected row examples

| Issuer | CUSIP | Shares | Reported short value (USD) | % fund NAV |
|---|---|---:|---:|---:|
| Tesla | 88160R101 | -990,915 | -256,805,531 | -3.154% |
| ServiceNow | 81762P102 | -217,698 | -173,318,086 | -2.129% |
| Salesforce | 79466L302 | -470,686 | -126,313,295 | -1.551% |
| Fair Isaac | 303250104 | -49,546 | -91,370,751 | -1.122% |
| Choice Hotels | 169905106 | -645,523 | -85,712,544 | -1.053% |
| General Mills | 370334104 | -1,111,902 | -66,480,621 | -0.816% |
| Johnson & Johnson | 478160104 | -399,912 | -66,321,406 | -0.814% |
| Electronic Arts | 285512109 | -408,752 | -59,072,839 | -0.725% |
| Gartner | 366651107 | -138,778 | -58,250,678 | -0.715% |
| Ford Motor | 345370860 | -5,343,367 | -53,593,971 | -0.658% |
| Public Storage | 74460D109 | -173,578 | -51,950,160 | -0.638% |
| Dropbox | 26210C104 | -826,365 | -22,072,209 | -0.271% |
| FedEx | 31428X106 | -141,878 | -34,587,019 | -0.425% |

The full 23-row fixture, including exact values and SEC text line ranges, is in `phase217_nport_full_submission_text_short_row_pilot.json`.

## New cross-check against Phase 192

Phase 192 had recorded CUSIP **31428X106** in the 2025 accession but could not capture its security name from the search excerpt. The complete submission text identifies it as **Fedex Corporation** and confirms:
- 141,878 shares short;
- reported value -USD 34,587,018.84;
- -0.4247602977% of fund net assets;
- `payoffProfile=Short`, `assetCat=EC`, `issuerCat=CORP`, `invCountry=US`.

The archive-directory timestamp recorded in Phase 192 (2025-05-28 16:04:35) matches the SEC-HEADER acceptance timestamp in this one filing. Treat this as a single-case corroboration only, not proof that directory timestamps are generally reliable first-publication timestamps.

## Identifier and interpretation cautions

The filing also contains short common-stock rows where CUSIP is `N/A` but an ISIN is present (Sally Beauty and H&R Block). These are preserved as identifier exceptions, not dropped or assigned fabricated CUSIPs. It also contains a foreign-format CUSIP/ISIN example (GLOBALFOUNDRIES) with `invCountry=US`. Therefore `invCountry` is not a listing-venue field, and the historical CUSIP/ISIN-to-listing crosswalk remains mandatory.

The positions belong to one registered fund's reported portfolio. A short position may be directional, hedging, relative-value, arbitrage or liquidity management. It is not public short interest, securities-lending utilization, a hedge-fund-wide position, or proof of informed trading.

## Admission gates

| Gate | Result |
|---|---|
| Complete SEC submission text inspected | PASS — one accession |
| 23 selected direct-short common-equity examples | PASS — line-referenced |
| SEC-HEADER acceptance timestamp | PASS |
| Report-to-filing lag | 58 calendar days |
| First public receipt capture | NOT VERIFIED |
| Complete submission-text SHA-256 | NOT VERIFIED |
| Raw primary XML SHA-256 | NOT VERIFIED |
| Deterministic full-filing parser | NOT VERIFIED |
| NPORT-P/A append-only version lineage | NOT VERIFIED |
| Fund series identity/deduplication | NOT ESTABLISHED |
| Effective-dated CUSIP/ISIN-to-listing crosswalk | NOT ESTABLISHED |
| Historical active/delisted universe | NOT ESTABLISHED |
| Prevalence or broad-universe coverage | NOT ESTIMATED |
| Incremental alpha versus frozen LTM/F80 | NOT AUTHORIZED |

**Important reproducibility limit:** the web-accessible SEC complete submission text was inspected and line-referenced, but the file was not downloaded into the research runtime and no raw SHA-256 was computed. The JSON fixture is a manually transcribed evidence ledger, not a raw-file parser. The 23-row count is a selected evidence sample, not the total number of short rows in the filing.

## Next gate

1. Configure the authorized `SEC_CONTACT_EMAIL` repository secret.
2. Retrieve the complete `.txt` and `primary_doc.xml` bytes for all five Phase 192 accessions; record SHA-256, accession, SEC-HEADER acceptance, report date and file metadata.
3. Parse every `invstOrSec` deterministically, including non-US, derivative, CUSIP-missing and identifier-exception rows; reconcile XML against the complete submission and SEC bulk dataset.
4. Add a stratified sample across fund series and filing years, preserving each NPORT-P/A as an append-only vintage.
5. Resolve series identity, effective-dated security/listing identity and delisted coverage before any stock-level feature.
6. Only then preregister changes in direct short exposure/breadth and compare them with prior returns, liquidity, volatility and options flow. Use chronological OOS, identical exposure/costs, block/cluster bootstrap and leave-one-fund/issuer-out. Do not use the consumed legacy holdout.

**Controls:** no return/alpha test, no bootstrap/LOO, no holdout use, no production/universe change, no data purchase or vendor contact. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Official SEC sources

- Complete submission text: https://www.sec.gov/Archives/edgar/data/1467631/000114554925033457/0001145549-25-033457.txt
- Filing detail index: https://www.sec.gov/Archives/edgar/data/1467631/000114554925033457/0001145549-25-033457-index.html
- Primary XML: https://www.sec.gov/Archives/edgar/data/1467631/000114554925033457/primary_doc.xml
- Phase 192 evidence: `research/phase192_nport_direct_short_equity_sample_discovery.json`
