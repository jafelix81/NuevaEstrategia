# Phase 302 — SEC Form 4/A daily-index and PAC/correction clock audit

**Date:** 2026-11-12 UTC  
**Branch:** phase302-form4a-daily-index-pac-clock-audit  
**Status:** COMPLETED_2023_FORM4A_DAILY_INDEX_PAC_CLOCK_AUDIT

## Objective

Extend the Phase 281/283/295 daily-index knowledge-date pilot to the Phase 301 intermediate-era Form 4/A sample. Measure whether original and amendment accessions appear on the same or different daily-index dates, preserve SEC-HEADER acceptance chronology separately, and avoid treating date-granular indexes as exact first-public timestamps.

## Sample and source integrity

The deterministic Phase 301 sample was retained without changing case selection:

- 32 cases: 24 unique owner-overlap candidates and 8 ambiguous parent sets.
- 71 unique original/amendment documents: 48 documents from the 24 unique pairs plus 23 candidate-parent documents across the ambiguous cases.
- SEC Form 345 bulk archives: 2022Q4, 2023Q1 and 2023Q2. All three matched their pinned SHA-256 hashes.
- All 71 complete-submission files were downloaded, hashed and SEC-header reconciled for accession, form and filing date.
- The daily-index window for each accession comprised the prior business day as a negative control, the filing date, and the next three business days. Windows were deduplicated across accessions.

## Results

| Measure | Result |
|---|---:|
| Complete-submission documents downloaded | **71/71** |
| SEC headers reconciled | **71/71** |
| Daily index files expected | **121** |
| Daily index files downloaded and parsed | **121/121** |
| Raw daily-index bytes | **90,998,369** |
| HTTP/retrieval errors | **0** |
| Index parse/write errors | **0** |
| Accessions with complete-window, identity-matched index | **71/71** |
| Accessions with first observed index date equal to filing date | **71/71** |
| Later index-date sightings | **0** |
| Pre-filing negative-control sightings | **0** |
| SEC acceptances at/after 16:00 ET | **42/71** |
| SEC acceptances at/after the 17:30 ET Form 3/4/5 cutoff | **19/71** |
| SEC acceptances at/after 18:00 ET | **14/71** |
| SEC acceptances at/after 20:00 ET | **7/71** |
| SEC acceptances at/after 21:30 ET | **1/71** |
| SEC acceptances at/after 22:00 ET | **0/71** |

All 71 accession windows were complete. The earliest observed daily-index date within each complete window matched the SEC bulk filing date (zero calendar-day lag). Of the 71 acceptances, 19 occurred at or after 17:30 ET, the special same-day filing-date threshold for Forms 3, 4 and 5; 14 were at/after 18:00, seven at/after 20:00, and one at/after 21:30. None was accepted at/after 22:00 ET. The SEC states that Forms 3/4/5 accepted after 17:30 and before 22:00 retain that day's filing date and are disseminated by 22:00; EDGAR filing hours end at 22:00 ET. The SEC also says daily indexes are built nightly starting around 22:00 and may take hours to complete. Thus same-filing-date index membership is consistent with the rule, but does not establish the precise intraday moment the filing became public or whether it was available before the market close.

### Original/amendment daily-index ordering

| Pair-level daily-index status | Pairs |
|---|---:|
| Parent index date precedes amendment index date | **23** |
| Same daily-index date; intraday order unresolved | **1** |
| Amendment index date precedes candidate parent | 0 |
| Incomplete/missing index clock or acceptance-order conflict | 0 |

The 24 unique candidate pairs all passed the SEC acceptance chronology check. In the one same-index-date pair, acceptance timestamps do not establish first-public ordering; the pair remains intraday-unordered. The eight ambiguous parent sets remain ambiguous, and no parent was assigned.

## Interpretation and limitations

1. The sample supports a reproducible daily-index knowledge-date bound for these 71 accessions. It does not establish exact first-public receipt.
2. The sample contains no acceptance at/after 22:00 ET. Because EDGAR's filing window closes at 22:00 ET, the next test should not seek impossible after-22:00 acceptances; it should target the 17:30–22:00 Form 4/4-A window and filings whose transmission misses the cutoff and receives a next-business-day filing date.
3. The sample is purposive and inherited from Phase 301; it is not a prevalence estimate for all Form 4/4-A filings.
4. The daily index cannot order an original and amendment that share one index date.
5. SEC-HEADER acceptance time is not an exact public-receipt timestamp and must not replace a missing daily-index observation.
6. Unique parent links remain metadata-corroborated rather than authoritative accession foreign-key relationships.
7. Reporting-owner sets are accession-level; they do not establish transaction-line-to-individual-owner attribution.
8. Effective-dated issuer/security-class identity, inactive/delisted coverage and broad-universe price coverage remain open.

**Conservative research rule:** use the earliest index date only when the entire requested window was retrieved and parsed and the index identity matches issuer, form and filing date. For any later test, do not enter before the close of the next full XNYS session after that index date. If the index window is incomplete or identity fails, the event is unavailable; do not fall back to filing date or acceptance time.

## Validation and reproducibility

Final GitHub Actions run: [43127646850](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43127646850).

- Phase 153 regression: 17 tests.
- Phase 299 regression: 6 tests.
- Phase 300 regression: 6 tests.
- Phase 301 regression: 6 tests.
- Phase 302 regression: 13 tests.
- **Total: 48 tests passed.**

Artifact: [13904715073](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43127646850/artifacts/13904715073). It contains the three bulk archives, 71 complete submissions, 121 raw daily indexes, manifests and result JSON. Compressed artifact size: 44,933,819 bytes. SHA-256: e1be6ae8cf030d9e80769d93ce1d96d08e399cd3fb3f4b4fc826da20247628b5.

Two preliminary attempts failed before any SEC request: the first regression omitted the 2023-07-04 federal holiday from the test calendar; the second exposed a missing repository-root import path. Both were corrected. The final run includes an additional fail-closed guard requiring both parent and amendment index identities to be window-verified before pair-clock comparison.

## Official SEC timing references

- SEC, [Determine the Status of My Filing](https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/determine-status-my-filing): EDGAR operating hours are 06:00–22:00 ET; Forms 3/4/5 accepted after 17:30 and before 22:00 receive the same day's filing date and are disseminated by 22:00.
- SEC, [Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data): daily indexes are updated nightly starting around 22:00 ET and usually complete within a few hours; it describes the special treatment of Ownership Forms 3/4/5 and later-business-day PAC handling.

## Decision and next gate

**Decision:** retain Form 4/A as a conditional public-data candidate. Do not admit strict PIT, a stock-selection feature or alpha.

Next gate:
- Build a targeted, stratified sample across multiple historical periods with Form 4/4-A acceptances in the 17:30–22:00 ET window, especially 21:30–22:00, plus submissions that miss the 22:00 cutoff and receive a next-business-day filing date.
- Capture filing date, acceptance time, daily-index first observed date and same-day/next-business-day index appearances.
- Inspect same-day correction/PAC sequences separately; daily-index date alone cannot order them intraday.
- Continue effective-dated issuer/security-class identity and owner/transaction attribution.
- Only after these source gates pass, preregister a fresh chronological test against frozen LTM/F80 with identical exposure/costs, date/issuer/owner-clustered bootstrap, LOO, multiplicity control and a new prospective holdout.

## Controls

- Strict PIT admitted: **false**.
- Exact first-public timestamp verified: **false**.
- Return/alpha test: **not run**.
- Bootstrap/LOO and chronological OOS: **not run**.
- Holdout used: **false**; legacy holdout remains consumed and is not reused.
- F80, production, universe, capital and parameters: **unchanged**.
- Vendor contact/data purchase/license: **none**.
- Email sent: **no**; the configured contact was used only in the SEC User-Agent.
- PR opened/merged: **none**.
