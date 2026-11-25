# Phase 614 — SEC 13F prospective first-seen Atom feed capture

**Audit cutoff:** 2026-11-25 05:20 UTC  
**Branch:** \`phase614-sec-13f-first-seen-feed-capture\`  
**Disposition:** implementation prepared for prospective metadata-only capture; offline CI passed 23/23. No live SEC request, filing XML download, holdings extraction, return test or signal was performed in this phase.

## 1. Repository and Actions preflight

The repository was inspected before creating this branch. At the preflight cutoff:

- Main HEAD: \`f3057b6c843013cd63e9b9b16799732c25e669a7\`.
- Latest 100 Actions runs: 69 successful and 31 failed; all were completed.
- Explicit in-progress query: 0.
- Explicit queued query: 0.
- The first branch-list page returned 100 branches; the relevant Phase 20C, FINRA, SEC 13F and options branches were reviewed. No old branch was merged or replayed.
- Existing draft PR #230 (Phase 613) remains unmerged. Phase 614 is intentionally based on main and does not depend on PR #230, so the prospective collector can be reviewed independently.

No workflow was dispatched, rerun, cancelled or duplicated.

## 2. Latest source-specific runs, jobs, logs and artifacts

| Source | Run / artifact | Verified result |
|---|---|---|
| FINRA Reg SHO | [45550366574](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45550366574) / [14992784656](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45550366574/artifacts/14992784656) | Offline regression and live-capture jobs succeeded. The artifact was downloaded and parsed: 7/7 HTTP-200 daily files were rejected; 14 duplicate-symbol occurrences / 14 extra rows across BCPC and TPC; zero accepted files, first-seen events or eligible signals. Raw rows and volume values were not persisted. |
| CFTC TFF | [45550124780](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45550124780) / [14992729209](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45550124780/artifacts/14992729209) | Prospective-capture job succeeded. No new reports or revisions; 3,043 rows remain unchanged; latest report date 2026-11-17; zero signal-eligible historical rows. |
| SEC Form 4 | [45533818624](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45533818624) / [14986800169](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45533818624/artifacts/14986800169) | Offline and live jobs succeeded. 593 canonical new accession events, 1,273 accession observations, 669 same-feed repeat occurrences, nine cross-feed repeats, 24 structured transaction-detail rows and 10 owner rows appended. Descriptive Form 144/Form 4 crosswalk: 11 rows. Zero signal-eligible rows. |
| SEC Form 144 | [45523407949](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45523407949) / [14981126978](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45523407949/artifacts/14981126978) | Offline and live jobs succeeded. 135 new accessions and 912 new detail rows; cumulative ledger 659 accessions / 4,503 detail rows; 218 bounded detail backfills remain; zero signal-eligible rows. Phase 549 negative-control refresh identified four sell-to-cover/tax-withholding notices for one issuer totaling 2,253,270 proposed units; these are not executions and were not admitted as bearish signals. |

The FINRA workflow's successful conclusion means the fail-closed diagnostic completed, not that market files were accepted. The CFTC successful conclusion means the poll completed without a new report; it does not authorize historical backfill as point-in-time evidence.

## 3. Why SEC 13F is the next free prospective source

The SEC's official [RSS Feeds page](https://www.sec.gov/files/about/secrss.shtml) explains that Latest Filings search results can be subscribed to as RSS and filtered by form type. The [Accessing EDGAR Data guide](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) documents EDGAR's 6:00 a.m.–10:00 p.m. ET business-day filing window and a total 10-request/second fair-access limit.

The SEC's [Form 13F Data Sets page](https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets) provides quarterly structured holdings data from July 2013 onward, but those datasets are not a substitute for a prospective first-seen ledger. They are as-filed historical extracts and are published quarterly.

The collector therefore uses the public Latest Filings Atom feed only for prospective metadata. Four separate exact-form filters are used:

- 13F-HR
- 13F-HR/A
- 13F-NT
- 13F-NT/A

This avoids relying on undocumented prefix behavior to include amendments. Feed entries are deduplicated by accession for canonical events, while every observed occurrence remains in the accession-observation ledger.

## 4. Capture and integrity contract

The new collector:

1. Polls each form-family feed with 100 entries per page.
2. Uses the existing SEC fetch helper and its throttled, declared project User-Agent; no new secret or credential is required.
3. Uses the prior accession watermark or a validated feed-timestamp boundary. It fails closed if pagination repeats, timestamps are non-monotonic, or a boundary cannot be found within 50 pages.
4. Treats the first poll as a baseline with no lower interval bound.
5. Records poll start/end, per-page receipt upper bound, response hash, page offset, accession, form, filing date and the filing-index URL.
6. Retains the archive-path CIK only as \`feed_path_cik_unverified\`; it does not call this a verified manager identity.
7. Records the 06:00 ET filing-date legal floor and a conservative knowledge upper bound only when the poll interval is bounded.
8. Treats Atom \`updated\` as an unverified consistency timestamp, not as the exact SEC acceptance time or public-release time.
9. Never downloads filing XML/text or INFOTABLE holdings, and never creates a return or signal feature.

The metadata flags for manager identity, security identity, historical F80 membership, public-availability certification, research-observation eligibility and signal eligibility all remain false. A bounded feed observation is only a metadata event, not a research signal.

## 5. Workflow controls

- Pull requests run offline compilation and unit tests only.
- Scheduled capture is hourly on weekdays, and will begin only after the PR is merged to the default branch.
- A manual \`workflow_dispatch\` requires \`run_live_capture=true\`; manual mode is diagnostic and never persists state.
- Scheduled state is append-only and stores metadata/hashes only.
- A failed feed does not advance its watermark; candidates from an incomplete poll remain suppressed.
- No raw 13F filing content or holdings rows are committed to the public repository.

## 6. Tests and current limitations

Offline tests cover exact form-family filtering, accession extraction, timezone-aware feed timestamps, EST/EDT legal filing floors, watermark and timestamp boundaries, repeated-page detection, missing-boundary suppression, empty-feed baselines, manual non-persistence and the rule that bounded metadata never becomes a research/signal-eligible row.

Initial validation passed 23/23 offline tests in [Run 45554185580](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45554185580). After adding a fail-closed regression for a full 100-entry page followed by an empty page without a prior accession watermark, final validation [Run 45554609362](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45554609362) passed 24/24 offline tests. A subsequent pre-merge code review found and corrected the stale-timestamp pagination issue documented in Section 7; final validation [Run 45560408931](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45560408931) passed 27/27 offline tests; the live-capture job was skipped as designed. Earlier CI attempts caught and corrected an ElementTree/timezone alias collision and an exact-form fixture mismatch. The live-capture job was skipped as designed; no live SEC feed was polled and no current first-seen coverage claim is made. The collector will not produce prospective data until merged and its scheduled workflow runs.

Remaining gates after the first successful capture:

1. Verify actual feed pagination and amendment inclusion from live responses.
2. Reconcile Atom metadata with original filing detail pages for a bounded sample and retrieve exact acceptance timestamps where available.
3. Keep the Phase 613 legal dissemination floor separate from the first-seen receipt upper bound.
4. Resolve manager identity, OTHERMANAGER/OTHERMANAGER2 and filing amendments.
5. Complete historical CUSIP/FIGI-to-F80 identity and effective-dated universe coverage.
6. Only then construct ownership-change features and compare them with frozen LTM/F80 using identical exposure, costs and chronological OOS discipline.

## 7. Pre-merge code-review erratum — timestamp boundary could drop late-indexed filings

A post-implementation review found a data-loss edge case in the initial pagination logic. An Atom entry with an `updated` timestamp at or before the previous poll end was treated as a timestamp boundary even when its accession had never been observed. The poll could then be marked successful, advance the latest-accession watermark, and omit that accession plus older entries behind it. A feed timestamp is not proof that a record was present in the previous poll.

The correction removes feed timestamps as pagination stop conditions. They remain diagnostic: a stale/unknown timestamp can make the event metadata-only and ineligible, but it cannot suppress the accession or advance the scan boundary. The parser also now requires every Atom entry on an exact-form feed page to resolve to an accession; any entry/form parse mismatch fails the page closed and prevents watermark advancement. The scan now stops at the prior accession watermark. If there is no prior watermark, it enumerates through a proven end-of-feed; if a prior watermark exists but disappears before feed end, the poll fails closed and does not advance that feed's state.

Added regressions cover (a) stale-timestamp entries before the actual prior accession, (b) a missing/naive timestamp before the prior accession, (c) full-page plus empty-page end-of-feed with no watermark, and (d) a missing prior accession watermark, and (e) an unparsed Atom entry. The offline suite now contains 27 tests. The workflow's default token permission is also read-only; write permission is scoped to the live-capture job, keeping pull-request validation read-only.

## 8. Research disposition

- SEC 13F prospective metadata capture: implementation prepared; live operation pending merge.
- 13F holdings/ownership signal: not admitted.
- Alpha, OOS, bootstrap and LOO tests: not run.
- FINRA daily short-volume files: remain quarantined; the seven-file duplicate pattern is unresolved.
- CFTC TFF: prospective accumulation only; no new report.
- Form 4 and Form 144: metadata/structured-ledger improvements only; zero signals.
- No data purchases, vendor contact or license requests.
- \`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen; no production, capital, exposure, universe, parameter, cost or holding-period change.
