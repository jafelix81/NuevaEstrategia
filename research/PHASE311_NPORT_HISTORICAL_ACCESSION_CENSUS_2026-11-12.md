# Phase 311 — SEC N-PORT historical accession census

**Audit date:** 2026-11-12 04:44 UTC  
**Final workflow:** [43156706936](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43156706936) — success  
**Artifact:** [13916331861](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43156706936/artifacts/13916331861)  
**Artifact ZIP SHA-256:** `b03abc72c5ed9d59005ccca9a1285169c6bac7b7a607e9f415ec4c0fe1a342be`  
**Disposition:** historical accession inventory passes; no holdings panel, PIT admission or alpha admission.

## Executive finding

The SEC quarterly EDGAR master indexes provide a low-cost, reproducible accession census across the public Form N-PORT history. All 28 quarters from 2019 Q4 through 2026 Q3 were downloaded and parsed. The final scope includes the two data-bearing filing types and the late-filing notice type, with the notice kept separate from holdings.

| Form type | Accessions | Treatment |
|---|---:|---|
| NPORT-P | 349,076 | Data-bearing monthly portfolio report |
| NPORT-P/A | 5,343 | Separate as-filed amendment vintage |
| NT NPORT-P | 696 | Late-filing notice only; never a holdings observation |
| **Total unique accessions** | **355,115** | **No duplicates across quarters** |

The two data-bearing types total **354,419 accessions**. The census covers **2,458 distinct registrant CIKs**. Filing dates range from **2019-10-22 through 2026-09-30**. All 28 expected quarterly indexes were retrieved; 28/28 archive hashes are in the artifact manifest.

The 5,343 NPORT-P/A accessions are 1.5075% of data-bearing accessions. This is an accession mix, **not** an estimate of the percentage of original filings amended: one original may have multiple amendments and the lineage is not yet resolved.

The 696 NT NPORT-P records are notice accessions, not holdings. They are retained for future reporting-gap and lateness analysis. Their count does not by itself establish how many reports were ultimately missing or late.

## Quarterly coverage

| Quarter | NPORT-P | NPORT-P/A | NT NPORT-P | Total accessions | Registrant CIKs |
|---|---:|---:|---:|---:|---:|
| 2019 Q4 | 8,998 | 119 | 0 | 9,117 | 1,357 |
| 2020 Q1 | 11,077 | 178 | 5 | 11,260 | 1,699 |
| 2020 Q2 | 12,038 | 197 | 18 | 12,253 | 1,948 |
| 2020 Q3 | 12,226 | 190 | 21 | 12,437 | 1,976 |
| 2020 Q4 | 12,069 | 416 | 46 | 12,531 | 1,979 |
| 2021 Q1 | 11,804 | 101 | 15 | 11,920 | 1,926 |
| 2021 Q2 | 12,317 | 200 | 50 | 12,567 | 1,950 |
| 2021 Q3 | 12,146 | 122 | 18 | 12,286 | 1,950 |
| 2021 Q4 | 12,214 | 281 | 22 | 12,517 | 1,940 |
| 2022 Q1 | 12,109 | 201 | 11 | 12,321 | 1,900 |
| 2022 Q2 | 12,676 | 158 | 5 | 12,839 | 1,942 |
| 2022 Q3 | 12,465 | 191 | 50 | 12,706 | 1,949 |
| 2022 Q4 | 12,510 | 116 | 22 | 12,648 | 1,951 |
| 2023 Q1 | 12,388 | 120 | 11 | 12,519 | 1,931 |
| 2023 Q2 | 12,885 | 278 | 9 | 13,172 | 1,945 |
| 2023 Q3 | 12,602 | 323 | 12 | 12,937 | 1,938 |
| 2023 Q4 | 12,480 | 384 | 26 | 12,890 | 1,930 |
| 2024 Q1 | 12,277 | 224 | 75 | 12,576 | 1,906 |
| 2024 Q2 | 12,955 | 272 | 4 | 13,231 | 1,920 |
| 2024 Q3 | 12,884 | 289 | 18 | 13,191 | 1,933 |
| 2024 Q4 | 12,709 | 51 | 12 | 12,772 | 1,940 |
| 2025 Q1 | 12,536 | 186 | 52 | 12,774 | 1,916 |
| 2025 Q2 | 13,396 | 93 | 5 | 13,494 | 1,931 |
| 2025 Q3 | 13,093 | 78 | 28 | 13,199 | 1,940 |
| 2025 Q4 | 13,239 | 57 | 32 | 13,328 | 1,939 |
| 2026 Q1 | 13,106 | 38 | 4 | 13,148 | 1,938 |
| 2026 Q2 | 14,055 | 352 | 9 | 14,416 | 1,947 |
| 2026 Q3 | 13,822 | 128 | 116 | 14,066 | 1,955 |

A machine-readable copy is committed as `PHASE311_NPORT_QUARTER_SUMMARY_2019Q4_2026Q3.csv`.

## Parser and accession controls

The final parser handles both SEC master-index path patterns observed in the history:

- `edgar/data/{registrant_cik}/{18-digit-accession}/...`
- `edgar/data/{registrant_cik}/{10-2-6-accession}.txt`

The accession prefix must **not** be required to equal the registrant CIK. The SEC's EDGAR Public Dissemination specification states that the accession's first ten digits identify the submitting entity (the filer or a filing agent) and are not necessarily related to CIKs within the filing. The index path CIK is checked against the master-index registrant CIK; the accession is parsed independently.

The parser also splits the fixed first CIK field separately and the trailing four columns from the right, preventing a pipe character in a registrant name from shifting the form/date/filename columns. Exact form tokens are required; unrelated forms with similar prefixes are excluded.

Final regression suite: **13/13 passed**. Earlier failed attempts exposed and corrected (1) legacy dashed accession filenames, (2) the distinction between filing-agent and registrant CIK, and (3) a newline error in the pipe-name regression fixture. An earlier two-form census was superseded after the SEC Readme's NT NPORT-P subtype was identified. The final run is the authoritative three-form result. One queued superseded run was cancelled; no census output from that run was used.

## Data feasibility and limitations

The SEC's Form N-PORT data page covers October 2019–September 2026, lists 28 quarterly ZIP datasets, and states that the datasets are updated quarterly and include only publicly available filings disseminated by the Commission. It describes Form N-PORT as monthly portfolio-holdings reporting, while the bulk datasets are quarterly postings. Filings after 5:30 p.m. Eastern on the last business day of a quarter are included in the subsequent posting.

The 28 bulk datasets listed by the SEC total approximately 11.38 GB. This phase did **not** download those holdings datasets. Instead, it downloaded 28 compressed quarterly master indexes totalling 98,553,317 bytes, sufficient for a full accession census and deterministic sample selection. This is an inventory optimization, not a substitute for the holdings data.

The SEC's Readme documents the `SUBMISSION` table with accession as primary key and fields including filing date, subtype and report date; `FUND_REPORTED_INFO` includes series identity; `FUND_REPORTED_HOLDING` contains holding-level fields including CUSIP, balance, currency value, percentage of net assets and payoff profile; and `IDENTIFIERS` contains ISIN, ticker and other identifiers. The structured schema is promising for a fund-reported position panel.

Coverage is not universal institutional ownership: Form N-PORT excludes money market funds and SBICs, and the public dataset only includes filings disseminated by the SEC. The position date is not the knowledge date. The quarterly dataset posting clock is not the individual filing's first-public timestamp. Raw accession acceptance metadata must be retained, and the first-public interval remains unresolved.

## Deterministic QA sample

The artifact contains **56 sample candidates**: one SHA-256-minimum accession per quarter for each data-bearing type (28 NPORT-P and 28 NPORT-P/A). The sample has 56 unique accessions and 54 distinct registrant CIKs. It is deterministic and reproducible, but it is **not** a representative prevalence sample. NT NPORT-P notices are inventoried but excluded from the holdings sample.

## Research decision and next gate

N-PORT is promoted to a **high-priority data-feasibility candidate**, not to a predictive signal. It has broad historical filing coverage, structured security identifiers and explicit fund-reported long/short position fields. Its material disclosure delay, limited registrant universe, amendments, missing series identifiers and security-identity history remain central risks.

Next phase: download the 56 stratified complete submissions; hash raw bytes before parsing; reconcile accession, form, registrant CIK, filing date and acceptance timestamp; parse series/class identity and holding-level short rows; measure CUSIP/ISIN/ticker completeness and sign concordance by period/form; and preserve each amendment as a separate vintage. Do not infer trades from position levels. Do not build a security-level time series until amendment lineage, effective-dated security identity, filing availability and F80-universe coverage pass.

No return/alpha test, bootstrap, LOO or chronological OOS test occurred. No holdout was used. F80, production, universe, capital and parameters remain frozen. No data purchase, vendor contact or email was made.

## Sources

- [SEC Form N-PORT Data Sets](https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets)
- [SEC Form N-PORT Readme](https://www.sec.gov/files/nport_readme.pdf)
- [SEC EDGAR Public Dissemination Service Technical Specification](https://www.sec.gov/files/info/edgar/pdsdissemspec051310.pdf)
