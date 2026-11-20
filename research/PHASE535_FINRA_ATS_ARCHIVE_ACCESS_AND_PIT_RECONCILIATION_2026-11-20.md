# Phase 535 — FINRA ATS historical archive access, schema and PIT reconciliation

**Date:** 2026-11-20  
**Status:** completed — archive endpoint returned HTTP 530; no alpha test authorized  
**Branch:** `phase535-finra-ats-archive-access-audit`

## Executive decision

FINRA's ATS Transparency website is a distinct and potentially longer historical source than the Query API's rolling `weeklySummaryHistoric` endpoint. The official FINRA ATS website guide documents weekly, security-by-ATS reports, a machine-download page, and an archive index that can be filtered by year. The guide's first report week is May 12–16, 2014. This could extend the usable security-level ATS panel roughly two years earlier than the OTC Transparency API history documented in Phase 36/100.

This is a source-feasibility lead, not yet a verified archive-coverage pass. The current page requires a user certification according to FINRA's guide. Phase 535 deliberately performs GET-only inspection and does not click, submit, or accept any certification/terms control. The live result will determine whether the archive can be inspected without user action.

## 1. Correct the historical licensing assumption

The 2014 ATS fee schedule is stale. FINRA's 2015 rule filing SR-FINRA-2015-023 proposed deleting Rule 4553 and making ATS data publicly available at no charge, with implementation on July 13, 2015. The contemporaneous FINRA ATS website guide, version 3.0 dated July 13, 2015, says its revision removed fee-related functionality and documents the machine-download workflow.

Therefore do not repeat the old $12,000 professional / $18,000 vendor fee schedule as a current FINRA ATS archive price. This does **not** waive the current website's certification and terms of use; those must be respected.

## 2. What the archive contains

The official FINRA ATS Transparency Website User Guide (version 3.0, July 13, 2015) documents:

- Weekly equity volume and trade counts by security and by ATS/MPID.
- Report categories: NMS Tier 1, NMS Tier 2 and OTC.
- Tier 1 NMS reports published on a two-week delay; other NMS and OTC reports on a four-week delay.
- A Download tab with historical published reports filterable by year.
- A machine-download page at `https://ats.finra.org/TradingDetailFileArchive/TradingDetailFilesDownloadGrid`; the guide instructs automated consumers to parse the HTML table `tblTrading`.
- Delimited report columns: `Report_Type`, `Symbol`, `Issue_Description`, `ATS_Description`, `ATS_MPID`, `Shares`, `Shares_Last_Updated`, `Trades`, and `Trades_Last_Updated`.

The guide's example shows a report for the week beginning 2014-05-26 and a downloadable historical report list for 2015. The first reports covered the week of 2014-05-12 to 2014-05-16. This supports a possible 2014 start, but the current archive index and actual files still need live verification.

## 3. Distinguish three FINRA sources

| Source | Grain | History / PIT | Decision |
|---|---|---|---|
| ATS Transparency download archive | Security × ATS/MPID × week | Potentially 2014+; report delay and row update dates; live access pending | Highest-priority public off-exchange candidate |
| Query API `weeklySummaryHistoric` + production `weeklySummary` | Security × ATS/non-ATS aggregate × week | Historic rolling four years plus production rolling 12 months; Phase 100 sample has `initialPublishedDate` | Reproducible recent panel; no multi-decade history |
| Query API `blocksSummary` | ATS/MPID × month, market-wide | 123 monthly partitions 2016-06 through 2026-08 in the Phase 36 live artifact; has `initialPublishedDate` | Not a stock-selection source |

### Critical correction: blocksSummary has no ticker dimension

The Phase 36 live artifact's complete metadata contains no `issueSymbolIdentifier` or other security identifier. Its rows are by ATS MPID, month and block-size category. The earlier stock-level B1–B3 hypotheses for `blocksSummary` are therefore killed: there is no defensible join to an individual stock. Keep it only as a possible market-wide ATS/block-regime descriptor, which would be a separate and lower-priority hypothesis.

## 4. Reconcile with Phase 100's live API evidence

The completed Phase 100 audit (run [41978867803](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41978867803), artifact [13394110956](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41978867803/artifacts/13394110956)) retrieved ten week/tier partitions, 968,139 rows total, and reconciled every retrieved row count to FINRA's `Record-Total`.

Across the five sampled weeks (2022-01-03, 2023-01-09, 2024-01-08, 2025-01-06, 2025-10-20):

- `initialPublishedDate` was non-null for 100% of symbol-aggregate rows.
- Observed initial publication lag was 21 calendar days for T1 and 35 days for T2 in these samples, rather than treating the nominal two-/four-week delay as an exact timestamp.
- The union of T1 and T2 symbol aggregates overlapped 94.63%–99.10% of the legacy F80 335 names in these five sampled weeks. This is a comparability diagnostic only; the 335 names were manually selected and are not a representative broad-market universe.
- 1,882 symbol-aggregate rows had `lastUpdateDate` later than `initialPublishedDate`. A final current snapshot must not be backdated to its initial publication; use a validated later knowledge date or historical vintages.
- The 2022-01-03 T2 partition had two symbol-bearing rows without a symbol.
- The 2025-01-06 T2 partition had two conflicting duplicate-key groups for LND (ATS and OTC symbol aggregates). These remain unresolved.
- The strict data/integrity gate did not pass; PIT vintage history remains conditional. No forward returns or alpha tests were run.

The full Phase 100 audit is a feasibility sample, not proof of complete historical coverage or vintage reproducibility.

## 5. Phase 535 live test and safety

The new one-shot GitHub Actions workflow performs GET-only inspection of the official machine-download index. It:

- Does not log in, submit forms, click or accept FINRA terms.
- Stops if a user-certification/terms gate is present.
- Parses only the `tblTrading` index and, only if directly accessible without certification, samples up to six earliest/latest report files across report types.
- Keeps only metadata, hashes, row counts, symbol/MPID coverage diagnostics and schema checks; it does not persist raw FINRA files or rows.
- Does not use the F80 335 overlap as a broad-market coverage gate.

Live result: **HTTP 530 — blocked/unavailable from GitHub Actions**. The endpoint returned an 8,177-byte HTML response with text/html; no tblTrading index or report links were exposed. The script did not attempt a browser challenge, submit certification, or retry through another identity. No report file was downloaded. The completed run is [44824072120](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44824072120), with metadata-only artifact [14672703365](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44824072120/artifacts/14672703365). Offline tests passed 5/5. An initial run failed only because the workflow omitted the requests dependency; it was added and the corrected run passed.

## 6. PIT rules

The archive download schema contains per-row `Shares_Last_Updated` and `Trades_Last_Updated`, but no explicit `initialPublishedDate`. The report index includes a report-level `Last Updated` field, not a first-publication timestamp.

Do not use report week as the signal date. Do not assume the nominal two-/four-week delay is the exact first public timestamp. Before any alpha test:

1. Reconcile archive report weeks and per-row update dates against API `initialPublishedDate`/`lastUpdateDate` for overlapping weeks.
2. Establish whether the archive's `Last Updated` and per-row update dates are public-availability dates or merely ATS submission/update dates.
3. Preserve initial publication and every later revision separately where possible.
4. If only final snapshots are available, make them eligible no earlier than a conservative, independently validated final-update knowledge date and the next executable session.
5. Keep unresolved duplicate/missing-symbol rows out of the feature panel; never silently sum or deduplicate them.
6. Join symbols through a point-in-time security master, not ticker alone.

If the archive cannot expose historical first-publication/vintage information, it may still support a conservative final-snapshot test, but it does not pass strict historical PIT.

## 7. Pre-registered economic hypotheses (not assumptions)

Only after archive coverage, identity, revisions and PIT pass:

- H1: abnormal ATS share of total consolidated volume predicts future returns beyond LTM/F80, size, liquidity, volatility and recent return.
- H2: changes in ATS participation add information beyond its level.
- H3: concentration across ATS MPIDs contains incremental information beyond aggregate ATS share.
- H4: ATS/non-ATS divergence adds information, but must not be interpreted as buy/sell direction.
- H5: any apparent effect disappears after controlling for contemporaneous return/volume, in which case it is return-chasing rather than informed activity.

The data measure reported ATS activity, not aggressor direction, beneficial ownership or investor sophistication. An ATS/MPID is a venue/reporting entity, not the ultimate investor.

## 8. Current disposition

- FINRA ATS archive: **conditional candidate; automated archive access blocked by HTTP 530**. A user-authorized download or a FINRA-approved alternate delivery path is required to verify the 2014+ archive.
- FINRA `weeklySummaryHistoric`: **recent historical source validated for feasibility, but strict row-integrity/PIT-vintage gates remain open**.
- FINRA `blocksSummary`: **killed for stock selection; market-regime-only parking lot**.
- FINRA daily short-volume stock-selection implementation: killed in Phase 100; final holdout remains unused.
- No Smart Money signal admitted.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; no parameter, exposure, cost, holdout or production changes.

## 9. Existing FINRA Query API alternative and legal boundary

The HTTP 530 result applies to the separate `ats.finra.org` machine-download archive. It does not mean the FINRA Query API is unavailable. The Query API is already a more reproducible route for the recent history, but it does not supply the potential 2014+ extension.

### 9.1 Query API history and filter constraints

Official FINRA documentation describes:
- `otcMarket/weeklySummary`: rolling 12 months.
- `otcMarket/weeklySummaryHistoric`: a rolling four-year historical window; data older than one year is static and should not be repeatedly re-downloaded.
- The historical endpoint accepts one of `weekStartDate`, `historicalWeek`, or `historicalMonth`, plus optional `tierIdentifier`. No other fields can be used to filter the historical dataset.

The repository has already tested the symbol-filter limitation:
- Phase 521: `domainFilters` on `issueSymbolIdentifier` returned HTTP 400.
- Phase 522: `issueSymbolIdentifier = EQUAL` as a `compareFilter` also returned HTTP 400.

Therefore the historical symbol-week panel requires full week/tier partitions and in-memory filtering; a targeted 335-symbol query is not supported.

### 9.2 Existing live coverage evidence — do not repeat

- Phase 100 sampled 10 partitions / 968,139 rows. Every page reconciled to FINRA `Record-Total`; `initialPublishedDate` was present for 100% of symbol-aggregate rows in the sample. Observed publication lags were 21 calendar days for T1 and 35 for T2. The sample also found 1,882 rows updated after initial publication, two symbol-missing rows and two conflicting LND duplicate-key groups.
- Phase 518 retrieved 50 incremental weeks / 3,497,002 rows, reconciled all pagination and all 50 publication clocks, and extended the combined panel to 259 consecutive weeks from 2021-11-15 through 2026-10-26.
- These results establish a useful recent weekly panel, not a fully revision-reproducible 2014+ archive. The final/current values cannot be backdated to `initialPublishedDate` where `lastUpdateDate` is later. The aggregate HHI return-test path already failed its predeclared chronological sample gate. The symbol-week panel remains deferred until effective-dated identity, historical active-universe membership and survivorship-aware returns are available.

### 9.3 Terms and safe use

FINRA's current API Terms of Service (last updated 2026-03-19) govern Query API access. The Equity Specific Terms (last updated 2022-12-20) state that an individual may obtain a Public credential for public data and limit use to non-commercial personal or professional purposes. They permit derivative/Resultant Data, with redistribution subject to FINRA attribution, no charge and no further redistribution by recipients.

The general API terms require use of FINRA-issued credentials and the Licensed APIs; they prohibit scraping/harvesting or bulk copying through other processes, unauthorized access, and security-feature bypass. They also contain a restriction concerning algorithms/products/services that compete with FINRA products or services. These terms are not a blanket clearance for a firm's commercial workflow or public distribution of raw data.

No new credential was created and no terms were accepted in this phase. The earlier Phase 518 workflow used the repository's existing `FINRA_API_TOKEN` secret; its credential owner and acceptance record were not inspected. Do not publish raw FINRA rows or participant identifiers in this public repository. Keep any future API use within the accepted credential's authorized purpose and applicable terms.

### 9.4 Final source decision

- `ats.finra.org` machine archive: **blocked in GitHub Actions (HTTP 530); no challenge bypass, scraping workaround, login or certification submission.** Revisit only if FINRA supplies an authorized alternate delivery path or the user obtains the reports through an authorized process.
- Query API: **retained as a recent, approximately five-year weekly source**, subject to publication-vintage, duplicate/missing-row, identity and universe gates. It does not extend the validated panel to 2014.
- No full-partition re-extraction is authorized now. The existing evidence is sufficient to defer the symbol-week panel until identity and return-source prerequisites are resolved.
- No signal, alpha test or strategy change is admitted.

## Official sources

- FINRA [ATS Transparency Website User Guide, version 3.0 (July 13, 2015)](https://www.finra.org/sites/default/files/ATS-transparency-data-website-user-guide-version3.pdf)
- FINRA [SR-FINRA-2015-023 — deletion of Rule 4553 / ATS data made public at no charge](https://www.finra.org/sites/default/files/rule_filing_file/SR-FINRA-2015-023.pdf)
- FINRA [Weekly Summary API documentation](https://developer.finra.org/docs/api-explorer/query_api-equity-weekly_summary)
- FINRA [dataset catalog](https://developer.finra.org/catalog)
- Phase 36 live `blocksSummary` artifact: [run 40340466922](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40340466922), [artifact 12658048654](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40340466922/artifacts/12658048654)
- Phase 100 weekly ATS revalidation: [run 41978867803](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41978867803), [artifact 13394110956](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41978867803/artifacts/13394110956)
