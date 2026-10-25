# Phase 35 — SEC 13D/13G PIT crosswalk result

Date: 2026-10-25

## Execution
- GitHub Actions run: 40205738099
- Job: 121271998421
- Status: success
- Artifact: phase35-13dg-pit-event-crosswalk-audit
- Artifact SHA-256: 82e6aec09d72b29183ce3d9e6a290e1e9250e96f3d7bcd174b7be573513b136f

## Historical coverage
The audit used the frozen 335-name universe and SEC submissions from 2020-10-01 through 2026-09-30, with filing_date as the PIT knowledge date.

- CIKs selected: 307 / 335
- Unresolved tickers: 27 / 335
- Resolved filings: 19,363
- Unique issuers resolved: 279 / 335 (83.3%)
- Non-amendment filings: 5,480 across 276 tickers
- Initial filings: 5,273 SC 13G + 207 SC 13D
- Amendments: 13,883 / 19,363 (71.7%)
- Filing-date range: 2020-10-01 to 2026-09-30
- Ownership percentage present in 98.65% of resolved rows
- Shares beneficially owned present in 82.85% of resolved rows

Issuer coverage by calendar year: 2020 76, 2021 251, 2022 263, 2023 266, 2024 275, 2025 219, 2026 262.

## Data-quality finding
The parser did not recover event/acquisition dates from the audited filings (`event_date_available = 0` in the summary). This is not itself fatal because the research uses filing_date as the PIT knowledge date, but it prevents a clean filing-lag diagnostic and reinforces the rule that acquisition/event dates must never be used for signal timing.

The SEC endpoint audit also encountered 25 submission errors, predominantly HTTP 429 rate limits. These errors were not silently treated as successful coverage.

## Decision
**FEASIBILITY GATE FAILED for production / identical-exposure alpha testing.**

The resolved issuer coverage is only 83.3% of the frozen 335-name universe, with 27 unresolved names and meaningful year-to-year variation. Because the project requires identical exposure and does not permit silently shrinking the universe to make a Smart Money signal look better, no 13D/13G alpha test is authorized from this dataset.

This is a data-feasibility failure, not evidence that 13D/13G has no predictive value. A future attempt would require a deterministic historical issuer-identity solution that materially improves worst-period coverage and resolves the SEC rate-limit/retrieval reliability issue.

## Research discipline
- No threshold optimization was performed.
- No OOS return claim was made.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- 13D/13G is parked rather than forced into the model.

## Next priority
Return to the options / market-microstructure path, with emphasis on a historical dataset that can satisfy PIT, delisted-symbol, universe-coverage, and timestamp requirements before any economic test is run.
