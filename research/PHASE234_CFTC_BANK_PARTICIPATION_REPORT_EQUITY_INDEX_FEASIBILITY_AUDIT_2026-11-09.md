# Phase 234 — CFTC Bank Participation Report: equity-index coverage, semantics, and PIT feasibility

**Date:** 2026-11-09  
**Decision:** \`CONDITIONAL_PROSPECTIVE_REGIME_RESEARCH_ONLY\`  
**Production baseline:** \`F80_TOP20_PARTIAL50_BASELINE_C20\` unchanged

## Executive decision

A separate CFTC source deserves a controlled place in the Smart Money research queue: the monthly **Bank Participation Report (BPR)**. Unlike the weekly COT/TFF categories, BPR reports aggregate gross long and short futures positions of U.S. and non-U.S. commercial banks. The current November 2026 futures report includes several broad U.S. equity-index futures.

This is **not** a stock-selection dataset and is not yet a historical PIT signal. The CFTC website retains only the most recent 25 months, publication is monthly, and the public page/schedule does not establish the exact first-receipt timestamp. The BPR is therefore rejected for a standalone historical alpha/backtest at this stage, but retained as a low-priority prospective market-regime candidate because the underlying exposure is directly related to broad equity-index futures.

No returns were tested and no signal was admitted.

## Repository and workflow pre-check

Before adding this phase:

- Inspected the latest 100 GitHub Actions runs: 87 successful, 1 failed, 12 cancelled; zero queued or in-progress.
- Latest completed run: Phase 231, run \`42568771468\`, successful.
- Phase 231 job \`full-row-reparse\` completed all 9 regression tests, downloaded and reparsed the public Cboe sample, uploaded metadata-only artifact \`13651429847\`, and explicitly kept sample/PIT/alpha admission false.
- Artifact SHA-256: \`b65e594b48b1467bf22aefecf7b9afab78f4a18e2caf47e30569a57453f0a924\`.
- The run log confirms 112,313 unambiguous rows and 3,304 ambiguous expirations quarantined; no raw rows, symbols, or contract keys were persisted.
- PR #13 and PR #14 remain open; PR #14 is based on the PR #13 research branch. The Phase 231 head is \`77c9eccf7c8a3fc423ac8f50dfc98007bf50d274\`.
- 131 branches were inventoried (100 on page 1, 31 on page 2).
- No workflow was running, and Phase 234 adds no \`pull_request\` trigger. Its prospective capture workflow is schedule/manual only and will not activate until the research branch reaches the repository default branch.

## Source semantics and feasibility

Official CFTC pages:

- [Bank Participation Reports index](https://www.cftc.gov/MarketReports/BankParticipationReports/index.htm)
- [Explanatory Notes](https://www.cftc.gov/MarketReports/BankParticipationReports/ExplanatoryNotes/index.htm)
- [Release Schedule](https://www.cftc.gov/MarketReports/BankParticipationReports/ReleaseSchedule/index.htm)
- [Historical Special Announcements](https://www.cftc.gov/MarketReports/BankParticipationReports/HistoricalSpecialAnnouncements/index.htm)
- [November 2026 BPR — Futures IN CONTRACT](https://www.cftc.gov/MarketReports/BankParticipation/deanov26f)

The CFTC's explanatory notes establish:

1. BPR is monthly and reports aggregate large-trader positions of banks in financial and non-financial futures markets.
2. Separate reports exist for futures and gross options; the options report is **not delta-adjusted**.
3. Only markets with at least five banks holding reportable positions are included.
4. Positions are divided into U.S. Banks and Non-U.S. Banks, with aggregate gross long and gross short positions.
5. Bank classifications derive from CFTC Form 40 responses and staff approval. If a trader is classified as a U.S. or Non-U.S. Commercial Bank in any one commodity, that designation applies to its positions in all commodities published in BPR. This is not a clean label for all institutional investors or all beneficial owners.
6. If either bank category contains fewer than four banks, the category bank count is suppressed and only the total bank count is shown. A blank category count must remain \`UNKNOWN\`, not zero.
7. The as-of date is typically the first Tuesday; publication is generally the first Friday shortly after 3:30 p.m. ET. If the first Tuesday is a federal holiday, the next Tuesday is used and publication moves to the following Friday.
8. The CFTC retains only the most recent 25 months on its public site.

The official special-announcements page records that BPR processing/publication was interrupted from October 1 through November 12, 2025 because of a lapse in appropriations, after which reports were published in chronological order. This is direct evidence that the nominal schedule is not a reliable substitute for a first-receipt log.

A separate CFTC announcement on October 27, 2026 concerns increasing the **COT Report** publication frequency. The current BPR index and release schedule still describe BPR as monthly. This audit does not assume that the COT change alters BPR.

## Current public coverage and worked sample

The current CFTC index exposes 25 months (November 2024 through November 2026). This is the site's retention window, not a long historical archive.

The November 2026 report has:

- Position/report date: **2026-11-03**.
- Scheduled release date: **2026-11-06**.
- Release target: first Friday shortly after **3:30 p.m. ET**.
- Exact first public receipt timestamp: **not established** by the report page or schedule.

The November report includes these broad equity-index futures:

| Contract | U.S. banks (long / short) | Non-U.S. banks (long / short) | Total banks | Market OI | Combined bank net / OI |
|---|---:|---:|---:|---:|---:|
| CME E-MINI S&P 500 | 39,925 / 71,568 | 15,383 / 273,885 | 26 | 1,986,532 | -14.61% |
| CME NASDAQ MINI | 19,891 / 5,310 | 6,753 / 18,858 | 21 | 292,587 | +0.85% |
| CME RUSSELL E-MINI | 15,033 / 7,130 | 25,910 / 13,945 | 22 | 449,399 | +4.42% |
| CBT DJIA x $5 | 0 / 1,865 | 6,719 / 20,335 | 11 | 87,410 | -17.71% |

\`Combined bank net / OI\` is calculated as \`(U.S. long + Non-U.S. long - U.S. short - Non-U.S. short) / market open interest\`. It is a descriptive transformation of the report, not a trade recommendation or evidence of directional skill. Banks can intermediate, hedge, or carry offsetting exposures.

The parser tests also preserve suppressed bank counts as \`None\`, keep actual zero positions as zero, require the market OI denominator, and reconcile the U.S. plus Non-U.S. positions to the report's total row.

## Economic role and hypothesis discipline

BPR has no issuer, ticker, CUSIP, or individual-stock mapping. It cannot provide cross-sectional coverage of the 335-ticker universe. At most, it can become a **broad market-regime overlay**.

If a sufficiently long prospective panel is eventually accumulated, the preregistered primary feature should be:

\`BPR_SP500_BANK_NET_OI = (U.S. bank net + Non-U.S. bank net) / E-mini S&P 500 market OI\`

Secondary diagnostics, not additional independent fishing opportunities:

- U.S.-bank net/OI.
- Non-U.S.-bank net/OI.
- U.S. versus Non-U.S. bank net divergence.
- Nasdaq/Russell/DJIA breadth or divergence, only where the contract is actually reported.

The economic hypothesis is narrow: bank aggregate exposure in equity-index futures may contain incremental information about broad risk appetite or hedging pressure. It is not assumed to be informed directional flow.

Any eventual test must compare incremental information against the frozen LTM/F80 baseline and the existing QQQ risk regime, controlling for QQQ/SPY trend, realized volatility, VIX, rates, and prior returns. The report date is not the availability date. The earliest modeled trade is the next regular XNYS session after the capture pipeline's recorded first receipt.

The current 25-month public archive and monthly frequency are insufficient for a credible standalone historical OOS conclusion. No return test is justified.

## Prospective capture design

A research-only workflow is added:

- Poll the CFTC BPR index every weekday at **20:35 UTC**. This is after 3:30 p.m. ET in both U.S. daylight and standard time.
- Polling every weekday, rather than only on the nominal first Friday, allows the capture pipeline to observe delayed reports and catch-up publication.
- Resolve the newest Futures link from the CFTC index, download the report page, parse its report date, and compute SHA-256.
- Store raw HTML by \`report_date + content hash\`; never overwrite a previous version.
- Store a separate receipt metadata record containing the pipeline's actual first-observed UTC/ET time, HTTP Date header (recorded but not used as availability), workflow run identifiers, report date, URL, and content hash.
- Manual dispatch is always marked non-PIT.
- A scheduled receipt is only a pipeline-availability candidate when it is observed on a weekday after 3:30 p.m. ET. The signal cannot be used before that receipt and cannot be traded before the next regular XNYS session.
- If CFTC revises a report, the new hash is appended as a new version; the earlier version and receipt remain intact.
- The workflow does not run on pull requests and will not activate until the branch is merged into the default branch.

No BPR raw snapshot has been captured yet. The workflow is staged in PR #14 and is not active on \`main\`.

## Decision

| Gate | Result |
|---|---|
| Official source and semantics | PASS |
| Broad equity-index futures present in current report | PASS |
| Historical archive depth | FAIL for long OOS (25 months only) |
| Exact historical first-receipt vintages | FAIL |
| Stock-level universe coverage | FAIL / not applicable |
| Prospective first-receipt capture design | IMPLEMENTED, awaiting merge to default branch |
| Predictive alpha | NOT TESTED |
| Production admission | NO |

**Final status:** \`CONDITIONAL_PROSPECTIVE_REGIME_RESEARCH_ONLY\`.

\`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen. No production changes, no universe changes, no paid data, no backtest, and no use of \`CONSUMED_NOT_PRISTINE\`.
