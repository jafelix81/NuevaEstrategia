# Phase 239 — CFTC TFF prospective capture and publication-regime audit

**Date:** 2026-11-09  
**Research branch:** `phase231-cboe-option-quotes-full-row-reparse`  
**Decision:** prospective capture protocol implemented; no historical PIT or alpha admission.

## Executive decision

The CFTC Traders in Financial Futures (TFF) report is a viable *broad-market positioning* research source, not a stock-level Smart Money feed. It provides weekly (currently) gross long, short and spreading positions for Dealer/Intermediary, Asset Manager/Institutional, Leveraged Funds and Other Reportables across financial futures markets.

The CFTC's public data history reaches 2006-06-13, but its FAQ says a complete historical list of release dates is not available; only the most recent 13 months of release dates are listed. Report date is not publication date. This prevents a strict historical PIT reconstruction for most of the archive. The correct next step is prospective capture, not a backdated return test.

I extended the existing Phase 234 BPR capture workflow to capture both TFF streams. I did **not** create a second CFTC workflow. The existing weekday schedule and concurrency lock are reused.

## 1. Official source and current report

The current CFTC COT page links two current TFF comma-delimited files:

- Futures only: https://www.cftc.gov/dea/newcot/FinFutWk.txt
- Futures and options combined: https://www.cftc.gov/dea/newcot/FinComWk.txt

The live files currently show report/as-of date **2026-11-03**. The CFTC release schedule lists **2026-11-06** as the corresponding scheduled publication date. The CFTC states that reports are released at 3:30 p.m. Eastern, usually Friday, and usually contain the preceding Tuesday's positions.

The CFTC's TFF variable-name page documents **87 fields**. They include open interest, gross long/short/spreading positions and changes for the four TFF categories, percentages of open interest, trader counts, concentration fields, contract units and contract-market identifiers.

Official references:

- COT landing page and methodology: https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
- Release schedule: https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm
- TFF variable names (87 fields): https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalViewable/cotvariablestfm.html
- Current futures-only file: https://www.cftc.gov/dea/newcot/FinFutWk.txt
- Current futures-and-options file: https://www.cftc.gov/dea/newcot/FinComWk.txt

## 2. What the categories do — and do not — mean

The four TFF categories are:

1. Dealer/Intermediary
2. Asset Manager/Institutional
3. Leveraged Funds
4. Other Reportables

These are not named institutions, beneficial owners or verified "informed money." The CFTC says trader classification is based on the predominant business purpose self-reported on Form 40 and reviewed for reasonableness; CFTC staff does not know the specific reason for each position. Individual trader classifications are not published.

The COT universe also has a reporting threshold: contract markets with fewer than 20 reportable traders can disappear from the report. An absent market is therefore not a zero position. The CFTC says the TFF historical data begin on 2006-06-13, but there is no primary key in the dataset; a composite key must be constructed from report date and contract-market fields, with historical identity caveats.

The current TFF files are long-format reports. The two streams are kept separate. Futures-and-options combined positions incorporate options calculations and must not be averaged with futures-only positions.

## 3. Descriptive current snapshot — not a signal

I transcribed four representative rows from the current official files into regression fixtures: the S&P 500 Consolidated row from each stream and a Canadian Dollar control row from each stream. The parser accepts all four as 87-field rows. This is a row-level schema/semantic check, **not** a full-file download or full-file validation.

For the 2026-11-03 S&P 500 Consolidated row, gross long minus gross short, divided by the stream's own open interest, gives:

| TFF category | Futures only net | Futures only / OI | Futures + options net | Combined / OI |
|---|---:|---:|---:|---:|
| Dealer/Intermediary | -693,326 | -34.43% | -701,177 | -23.60% |
| Asset Manager/Institutional | +930,713 | +46.22% | +917,568 | +30.88% |
| Leveraged Funds | -366,870 | -18.22% | -345,246 | -11.62% |

Open interest is 2,013,852 in the futures-only row and 2,970,924 in the combined row. These are descriptive positions from one report date. The two denominators differ because the combined stream includes options-equivalent positions; the ratios are not interchangeable. Category divergence is a hypothesis generator, not evidence that one category is informed or that the position predicts future returns.

## 4. Publication-regime change: do not assume TFF is already semiweekly

On 2026-10-27, the CFTC announced a plan to move COT publication from once to twice weekly by the end of 2026: Monday data on Wednesday and Wednesday data on Friday, both at 3:30 p.m. ET.

There are two unresolved points:

- The current official release-schedule page, checked 2026-11-09, still describes the usual Friday release and lists the existing weekly 2026 schedule.
- The press release frames the change as responding to agricultural-market feedback. It does not explicitly state whether or when the TFF financial-futures files will move to the same cadence.

The capture therefore polls every weekday after 3:30 p.m. ET. This is robust to either weekly or semiweekly publication without assuming that the TFF schedule has changed.

References:

- CFTC Release 9316-26 (2026-10-27): https://www.cftc.gov/PressRoom/PressReleases/9316-26
- Current 2026 release schedule: https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm

## 5. Capture protocol

The existing Phase 234 BPR workflow is extended; no duplicate workflow is added.

- Existing schedule: 20:35 UTC, Monday–Friday. This is 15:35 EST / 16:35 EDT, after the CFTC's 15:30 ET target.
- Existing concurrency group is retained, so overlapping CFTC capture runs do not race.
- Both TFF streams are fetched separately from the current CFTC index links.
- Exact response bytes are SHA-256 hashed before deterministic gzip storage. Decompression must reproduce the original response bytes.
- The index HTML is also retained by content hash.
- The parser fails closed unless each data row has exactly 87 fields, report/as-of dates agree and are uniform, the stream label matches, required position/OI fields are valid, and the composite contract-market key is unique.
- Explicit zero trader counts remain zero; a dot or blank remains UNKNOWN.
- HTTP Date is recorded as metadata but is **not** treated as first availability.
- Every version is append-only. A changed hash for the same report date is a revision, not a new report.

PIT classifications:

| Observation | Treatment |
|---|---|
| First scheduled capture for a stream | Baseline state only; usable only after receipt; not a release event |
| Later report date first seen by scheduled capture | New report; usable from pipeline observation time |
| Same report date, new hash | Revision; state-only pending correction semantics |
| Unchanged hash | No new snapshot/event |
| Older report date/rollback | Stored as non-PIT |
| Manual dispatch or nonqualifying time | Non-PIT; does not advance scheduled baseline |

The earliest decision session is the first regular XNYS session strictly after the pipeline observation. Under the existing EOD discipline, the earliest execution is that session's close. This is a conservative *known-by our pipeline* timestamp, not a claim about the CFTC's exact first public publication time.

The workflow is not active on the default branch yet. The first scheduled capture after the stacked PR chain reaches main will be baseline-only for each stream. No TFF raw snapshot has been captured in this phase.

## 6. Parser and regression validation

**29/29 local tests passed.** Coverage includes:

- Synthetic futures-only and combined 87-field rows.
- Four official sample rows from the current CFTC files, including S&P 500 futures-only and combined.
- Wrong stream, wrong width, mixed dates, duplicate contract key, invalid OI and negative position rejection.
- Missing/suppressed trader count versus explicit zero.
- Safe extraction of the two CFTC links.
- Timezone-aware receipt checks and 15:30 ET schedule boundary in both EST and EDT.
- Baseline, new-report, revision, unchanged, manual and rollback PIT classifications.
- Exact gzip round-trip, raw SHA-256, HTTP Date non-use, independent stream state, manual-baseline isolation and index-snapshot deduplication.

The current full files were **not** downloaded or persisted in this phase; the official live sample rows validate the documented schema only. No hosted Phase 239 CI run is claimed. The updated workflow will run the 29-test suite before capture once active on the default branch.

## 7. Research hypothesis — pre-registered, not tested

Primary candidate for later study:

`(AssetManagerLong - AssetManagerShort - (LeveragedFundsLong - LeveragedFundsShort)) / OpenInterest`

Use the **S&P 500 futures-only** stream as the primary definition. Keep the futures-and-options combined stream as a separate sensitivity series; never average the two.

This is a broad-market regime hypothesis only, not an individual-stock selection feature. Candidate controls include QQQ risk state, prior SPY/QQQ returns (1/5/20/63 sessions), realized volatility, VIX regime and trend. The test must distinguish prediction from return-chasing and use only observations after the pipeline's known-by timestamp.

No return test is authorized until a prospective, multi-regime panel and a pre-registered power/precision plan exist. Later evaluation must use chronological/purged validation, identical exposure and costs versus frozen LTM/F80, time-block bootstrap and LOO diagnostics. The consumed legacy holdout is prohibited.

## 8. Decision and guardrails

- TFF: conditional prospective broad-market regime candidate only.
- Historical PIT admission: **FAIL** for the long archive because historical release-date coverage is limited to the latest 13 months.
- Prospective capture: implemented in the existing BPR workflow; not yet active on main and no snapshot exists.
- Alpha admission: **NO**.
- No return/backtest, bootstrap/LOO, chronological OOS or holdout test in Phase 239.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No production or universe changes, no data purchase and no vendor contact.

