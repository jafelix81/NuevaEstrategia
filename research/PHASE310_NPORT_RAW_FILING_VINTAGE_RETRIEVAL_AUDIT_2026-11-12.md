# Phase 310 — SEC N-PORT raw filing, acceptance-clock and direct-short reconciliation

**Audit date:** 2026-11-12  
**Final workflow:** [43154326395](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43154326395) — success  
**Artifact:** [13915126393](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43154326395/artifacts/13915126393)  
**Artifact ZIP SHA-256:** `f4827e6065b76bb2f8d4c6287e2026cf1b6eb06f136a407d6295ab530e47ef98`  
**Disposition:** raw bytes, acceptance metadata and direct-short positive controls reconciled for 5/5 purposive filings; series identity present for 4/5; no strict PIT or alpha admission.

## Executive finding

The earlier Phase 193 attempt was blocked because the SEC contact secret was absent. Phase 310 reran the five-accession retrieval after the secret became available, preserved the exact public bytes before semantic parsing, and completed the raw-file audit.

The SEC complete-submission text stores acceptance time as an SGML tag, for example `<ACCEPTANCE-DATETIME>20250528160435`, not as a colon-delimited field. The prior parser expected a colon and therefore falsely reported the acceptance time as missing. This parser defect is corrected.

All five accessions now have:
- the accession directory JSON;
- the filing detail HTML page;
- the complete submission text;
- the primary N-PORT XML;
- SHA-256 hashes for all four files;
- reconciled accession, form and acceptance timestamp;
- matching acceptance time on the SEC filing detail page and the directory `last-modified` metadata;
- a conservative next-full-XNYS-session candidate.

All 11 preselected positive-control CUSIPs were found on sign-concordant direct-short rows. The five filings contain 327 sign-concordant U.S. corporate common-equity short rows under the narrow parser definition. These are fund-reported portfolio snapshots, not market-wide short interest and not proof of informed trading.

## Accession-level results

| Filing year | Accession | Period of report | SEC acceptance (ET) | Conservative next full XNYS session | Series ID | Sign-concordant direct-short rows |
|---|---|---|---|---|---|---:|
| 2020 | `0001752724-20-163166` | 2020-06-30 | 2020-08-21 12:55:43 | 2020-08-24 | `S000062084` | 100 |
| 2022 | `0001145549-22-056239` | 2022-07-31 | 2022-09-15 14:23:22 | 2022-09-16 | `S000052217` | 46 |
| 2023 | `0001145549-23-060491` | 2023-07-31 | 2023-09-29 14:46:20 | 2023-10-02 | `S000043717` | 27 |
| 2024 | `0001145549-24-075135` | 2024-09-30 | 2024-11-26 13:55:59 | 2024-11-27 | `S000000849` | 86 |
| 2025 | `0001145549-25-033457` | 2025-03-31 | 2025-05-28 16:04:35 | 2025-05-29 | **Not present** | 68 |
| **Total** | **5 accessions** | | | | **4/5 present** | **327** |

The SEC filing detail page and the primary-document `last-modified` value match the SGML acceptance time in 5/5 cases. The acceptance date also matches the filed-as-of date in 5/5 cases. The 2025 filing has no series or class identifier in either the primary XML or filing detail HTML; it remains fund/CIK-level only and is not promoted to a series-level time series.

The report-to-acceptance delays are 52, 46, 60, 57 and 58 calendar days respectively. This reinforces that the position date is not the knowledge date and that any future signal must use filing availability, not `PERIOD OF REPORT`.

## Direct-short parser contract

The narrow candidate definition is:
- `payoffProfile=Short`;
- `assetCat=EC`;
- `issuerCat=CORP`;
- `invCountry=US`;
- `units=NS`;
- negative `balance`, `valUSD` and `pctVal`.

The expected CUSIP controls were 4 in 2020, 4 in 2022, none preselected in 2023, 2 in 2024 and 1 in 2025. All 11 expected CUSIPs were found on rows whose units and three numeric signs were concordant. The 2023 filing independently passed its minimum-row control.

This is a purposive parser/lineage positive-control sample. It is not a random sample, not an estimate of how often funds report short positions, and not a prevalence estimate.

## Timestamp interpretation

The SEC `ACCEPTANCE-DATETIME` and the filing detail page's `Accepted` value are now reconciled. The accession directory's primary-document `last-modified` timestamp also matches in this sample.

These are acceptance/filing metadata clocks. They do **not** establish the exact first public receipt by every market participant. The next XNYS session shown above is a deliberately conservative execution candidate strictly after the acceptance date; it is not evidence that the filing was first disseminated at that instant. No same-session execution is authorized.

## Technical validation

- Final workflow [43154326395](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43154326395) passed.
- 14 Phase 193 regressions and 9 Phase 310 regressions passed (23 total).
- Five accessions retrieved; 20 raw files staged in the 90-day artifact; 1,722,110 raw bytes.
- SHA-256 hashes recorded in `phase310_nport_raw_vintage_validation_result_2026-11-12.json`.
- The raw filing bytes were not committed to the repository.
- An intermediate regression run failed because its synthetic index-listing fixture omitted the newly required filing-index HTML entry. The fixture was corrected; the final run passed. No SEC data were lost or altered.

## Research disposition

**Partial admission only.** Raw retrieval, header identity, acceptance-time reconciliation and expected short-CUSIP sign controls pass. Series identity is partial (4/5), so the five filings are not yet a complete series-level panel.

The source remains a candidate for a later fund-reported short-exposure-change hypothesis, not a trading signal. A position level is not a trade; it may reflect hedging, portfolio construction or other constraints. The public disclosure lag is material. A meaningful test must compare changes between successive as-filed vintages, preserve each NPORT-P/A as a separate correction state, map securities with an effective-dated CUSIP/ISIN crosswalk, and use only data available after the filing clock.

### Required next gates

1. Build a complete accession inventory for public NPORT-P and NPORT-P/A from the SEC's 2019–2026 history; do not infer coverage from these five purposive filings.
2. Expand to a stratified sample across filing years, registrants, fund sizes and series structures, including delisted securities.
3. Resolve the 2025 no-series case or explicitly keep it at CIK/fund level; never invent a series key.
4. Preserve original filings and every amendment as append-only vintages; distinguish a correction from a new position change.
5. Build effective-dated CUSIP/ISIN/security identity and universe-coverage audits.
6. Only after those gates, test position changes versus frozen LTM/F80 with strict chronological validation, realistic execution delay and identical exposure/costs. Bootstrap/LOO and OOS are mandatory if a signal survives.

No return or alpha test, bootstrap, LOO, chronological OOS, or holdout use occurred. F80, production, universe, capital and parameters remain unchanged. No data purchase, vendor contact or email was made.

## Source documents

- [2020 NPORT-P filing](https://www.sec.gov/Archives/edgar/data/1408970/000175272420163166/0001752724-20-163166-index.html)
- [2022 NPORT-P filing](https://www.sec.gov/Archives/edgar/data/1511699/000114554922056239/0001145549-22-056239-index.html)
- [2023 NPORT-P filing](https://www.sec.gov/Archives/edgar/data/811030/000114554923060491/0001145549-23-060491-index.html)
- [2024 NPORT-P filing](https://www.sec.gov/Archives/edgar/data/1000351/000114554924075135/0001145549-24-075135-index.html)
- [2025 NPORT-P filing](https://www.sec.gov/Archives/edgar/data/1467631/000114554925033457/0001145549-25-033457-index.html)
