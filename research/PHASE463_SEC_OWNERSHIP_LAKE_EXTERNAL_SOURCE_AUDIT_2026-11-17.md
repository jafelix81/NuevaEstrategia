# Phase 463 — Independent SEC ownership lake and point-in-time audit

**Audit time:** 2026-11-17 20:18 UTC  
**Main HEAD at preflight:** `f2b0f813b14a47e4c042cae3669234192ec0feab` (Phase 462 merged)  
**Disposition:** retain the external SEC ownership lake only as a conditional secondary parser/crosswalk audit. Do not admit its normalized insider or 13F ticker fields as signals until the exact snapshot, transaction semantics, owner attribution and historical security identity are independently verified.

## 1. GitHub preflight

- Actions total: 7,708.
- Latest 100: 66 success / 33 failure / 1 cancelled.
- Explicit in-progress query: 0; queued query: 0.
- Branches: 295 (100 + 100 + 95 across three pages).
- Open PRs: 56; workflow files: 75.
- Latest run [44160407079](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44160407079), Phase 462 PR #123: offline-regression passed; live-capture skipped; no artifacts.
- Prior Phase 462 run [44160283721](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44160283721): offline-regression passed; live-capture skipped; no artifacts.
- PR #123 is merged as main HEAD `f2b0f813b14a47e4c042cae3669234192ec0feab`.
- No active run was duplicated or dispatched.

The last SEC Form 144 scheduled run remains [44083941814](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44083941814): offline tests passed, live capture failed, append/commit skipped, poll audit artifact uploaded. The current main workflow still contains the hourly `47 * * * *` cron and Phase 454 migration step. No later schedule-event run is present in the latest inventory; the 20:47 UTC slot is still in the future at this audit. Do not change the cron or add another poller.

The CFTC TFF weekday capture is scheduled for 22:25 UTC on 2026-11-17; it has not yet become due. Bootstrap rows remain ineligible. FINRA OAuth is still blocked by missing credentials; no API request should be made until the one-settlement validation is configured.

## 2. Official SEC source baseline

The SEC's official Insider Transactions Data Sets page currently lists 83 quarterly archives covering January 2006 through September 2026. The latest listed file is 2026 Q3 (8.26 MB). The SEC says the data are as-filed structured extracts, updated quarterly; filings after 5:30 p.m. Eastern on the last business day of a quarter roll into the next posting. The SEC also warns that the extracts may contain errors and omit metadata, and are not a substitute for the underlying filing.

Official index: https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets

This remains the authoritative bulk coverage index. The quarterly ZIP is a historical extract, not a live first-receipt feed.

## 3. External implementation examined

Reviewed the public repository `austin-starks/sec-ownership-disclosures`, package version 0.4.1 / repository commit `aaa6e7a8d8a00d22d221e288d9f2f3e0a6150625`, plus its README, METHODOLOGY, parser, tests, crosswalk and date utilities.

The project is useful as an independent implementation because it parses the same official SEC quarterly Form 3/4/5 and 13F data, preserves raw archive keys, checks file hashes in its published snapshot and exposes row-level availability. It is not an independent underlying information source; it is a secondary parser of SEC records.

**Version pin is not yet adequate.** The GitHub README reports 10,045,180 insider transaction legs through 2026Q2, while the Hugging Face dataset card advertises a 2026-10-27 snapshot with 10,128,966 legs. The exact current snapshot manifest, manifest SHA-256, per-file hashes and source-code commit were not downloaded and pinned in this run. Do not mix the repository README counts with a newer Parquet snapshot.

References:
- Source code: https://github.com/austin-starks/sec-ownership-disclosures
- Dataset card: https://huggingface.co/datasets/austin-starks/sec-ownership-disclosures
- Methodology: https://github.com/austin-starks/sec-ownership-disclosures/blob/main/METHODOLOGY.md

## 4. Form 4 transaction grain and owner attribution

The external parser explicitly produces:
- `insider_filings`: one row per accession × reporting owner;
- `insider_transactions`: one row per accession × transaction leg, not repeated per owner.

Its own unit test creates a filing with two reporting owners and one transaction, then asserts two filing rows and one transaction row. This is the correct non-duplicating row grain, but it does **not** provide a transaction-to-owner link. Joining those tables on accession alone would multiply transaction rows and falsely attribute the same transaction to every owner.

This independently corroborates Phase 461: multi-owner transaction lines remain quarantined unless the underlying filing provides explicit, line-level attribution. Single-owner filings can be retained at filing-owner grain. Owner counts are not independent-buyer counts.

## 5. Form 4 code P is not proof of an open-market execution

The external README describes `transactionCode = P` as an open-market purchase. The SEC's current Form 4 instructions define P as **“open market or private purchase”** of a non-derivative or derivative security. The code alone does not distinguish exchange execution from a private purchase.

The external parser retains `acquiredDisposed`, but its transaction parser does not ingest the quarterly `FOOTNOTES.tsv` member into the published transaction rows. It therefore cannot use its published transaction table alone to resolve private-vs-market execution. It also does not link a footnote to a transaction leg in that table.

Disposition:
- Require transaction code P and acquired/disposed = A before even considering a purchase.
- Keep derivative legs separate from common-equity purchases.
- Require verified footnote/filing evidence of an open-market execution before calling it an open-market candidate.
- P-only rows with unknown execution type remain `market_vs_private_unresolved`, not signal observations.

Official SEC code definition: https://www.sec.gov/files/form4.pdf and https://www.sec.gov/edgar/searchedgar/ownershipformcodes.html

## 6. Ticker and security identity

The external Form 3/4/5 parser sets `resolvedTicker` by parsing the filer-entered `issuerTradingSymbol` text. Its resolver takes the first symbol from a list such as `LEN, LEN.B`; it does not use an effective-dated issuer-CIK × security-class master. This is a useful display/join hint, not canonical historical security identity. It can misprice a transaction when the actual `securityTitle` refers to a different class.

For our frozen 335-name universe, retain the Phase 453/455 identity gates: issuer CIK, actual security/class, effective dates, listing history and historical universe membership must be independently verified. Do not accept a free-text ticker normalization as proof.

## 7. 13F CUSIP-to-ticker crosswalk inconsistency

The external project correctly documents that 13F holdings are CUSIP-keyed, and its `resolveHoldingTickers` helper supports `fromDate`/`toDate` spans. Its README warns that an undated CUSIP/ticker pair is only safe for a security that never changed symbols.

However, the public `examples/resolve-tickers.ts` builds pairs from one N-PORT quarter (2025Q2) and passes those undated pairs directly to all parsed 13F rows. The example therefore does not demonstrate a historically safe 2013-to-present mapping. The published snapshot's actual span-generation provenance was not independently verified.

Decision:
- Do not admit `resolvedTicker` for historical 13F until the exact effective-dated span source and vintage are pinned.
- Require CUSIP + class/title + a date-covering symbol span; unresolved rows stay null.
- Treat N-PORT and OpenFIGI as crosswalk inputs requiring conflict adjudication, not automatic truth.
- 13F remains a lagged, long-only, manager-aggregated holdings snapshot, not trade flow.

## 8. Availability clock

The external quarterly parser sets `availableAt` to end-of-day on SEC `FILING_DATE` in America/New_York. This is conservative for next-session historical research and avoids using the transaction date or 13F period-of-report as availability. It is not an exact intraday timestamp and does not certify when a quarterly bulk ZIP was originally downloaded.

Its separate daily XML parser uses EDGAR `ACCEPTANCE-DATETIME` plus a 60-second epsilon. That is a stronger clock for prospective/daily filings, but the daily refresh path is distinct from the quarterly Parquet snapshot.

Our rule:
- Quarterly bulk `FILING_DATE` EOD: next-session use only, after verifying the filing was publicly disseminated that date.
- Daily XML `ACCEPTANCE-DATETIME + epsilon`: potentially intraday only after independent receipt/availability validation.
- Never use `transactionDate` or `periodOfReport` as the disclosure-availability clock.
- Preserve amendments as new versions; never overwrite the original.

## 9. Research disposition

| Component | Decision |
|---|---|
| External SEC lake as secondary parser/crosswalk audit | Conditional candidate |
| P-only “open-market buying” feature | Killed as specified |
| Multi-owner transaction-to-owner inference | Killed without explicit line link |
| Free-text `resolvedTicker` as canonical identity | Rejected |
| Undated 13F CUSIP-to-ticker pairs for historical joins | Rejected |
| 13F manager ownership/crowding | Conditional slow-moving hypothesis |
| Quarterly filing-date EOD availability | Conservative next-session clock only |
| Published snapshot as a source of live first-seen events | Rejected |

No external dataset bytes were downloaded or committed. The runtime could inspect public GitHub source and web documentation but could not retrieve SEC/Hugging Face binary archives directly. No transaction sample was independently reconciled in this phase.

## 10. Next gates

1. Pin one exact Hugging Face `snapshot.json` vintage, its SHA-256, generation time, per-file hashes and corresponding source-code commit.
2. Obtain only small representative Form 3/4/5 samples (legacy 2006/2012, 2023 schema era and 2026Q3) through a permitted runner; compare accession × row-SK grain and code/owner counts against SEC originals.
3. Reconcile transaction P/A rows against original filing XML and footnotes; preserve private/unknown cases as non-signals.
4. Reconcile multi-owner forms against Phase 459–461 gates; no accession-only owner join.
5. Rebuild ticker identity from issuer CIK, security title/class and effective-dated security master for the frozen universe.
6. For 13F, validate historical CUSIP spans at 2013Q2, 2022Q4 and latest available window; do not use the one-quarter undated example mapping.
7. Only after coverage, PIT, identity and row-grain gates pass, test incremental information against frozen LTM/F80 with identical exposure, costs, chronological OOS, bootstrap and LOO.

No alpha, forward-return, OOS, bootstrap or LOO test was run. No source or signal was admitted. `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, capital, exposure, holdout and production remain frozen.

## 11. Validation

Phase 463 adds a fail-closed, offline-only gate module and unit tests for:
- quarterly end-of-day New York availability;
- no same-day intraday use of date-only bulk data;
- single-owner versus multi-owner attribution;
- P/A plus explicit open-market evidence;
- free-text ticker identity;
- effective-dated CUSIP spans;
- immutable snapshot pinning;
- 13F holdings-versus-trade-flow distinction.

The workflow performs no external requests and does not ingest or redistribute SEC/vendor data.
