# Phase 308 — SEC RSS prospective first-observation capture

**Date:** 2026-11-12  
**Status:** two consecutive complete current-feed snapshots captured; event-level timestamp correction advanced to Phase 309.  
**Branch:** `phase308-sec-rss-prospective-capture`

## Purpose and acquisition design

Phase 307 showed that `owner=only` isolates ownership filings from unrelated 4-prefixed forms while preserving the page-zero Form 4 accession set. Phase 308 implements repeatable prospective capture:

- Query SEC Latest Filings Atom with `owner=only`, separately for exact Form 4 and Form 4/A.
- Scan count=100 pages with 20-row overlap, exact form-token filtering, accession/entity reassembly, stable page-zero recheck and a 50-page cap.
- Preserve raw Atom pages, response headers, poll-start/completion UTC times and SHA-256 in each run artifact.
- Maintain a cumulative accession ledger in `research/data/sec_rss_prospective_ledger.json`.
- Keep Atom `updated` separate from first observation; it is not relabeled as first-public time.
- Record capture gaps, incomplete scans, changed entity-row sets, missing/new accessions between complete snapshots and raw-page hashes.
- The hourly research automation updates `research/SEC_RSS_CAPTURE_TRIGGER.json`; workflow concurrency prevents overlapping Phase 308 captures.
- Raw artifacts are retained for 90 days. A compact ledger snapshot is committed once per UTC day; intervening hourly state is carried by the Actions cache and run artifacts.

## Hosted capture results

### Initial complete snapshot — run 43142830440

- 30/30 SEC requests succeeded; snapshot complete.
- Form 4: **1,022 accessions / 2,111 entity rows**.
- Form 4/A: **18 accessions / 36 entity rows**.
- Total: **1,040 unique accessions**, 2,147 entity rows.
- Zero target structural errors and zero row-fingerprint conflicts.
- First snapshot was left-censored: there was no earlier complete observation boundary. Its 1,040 accessions cannot be assigned a historical first-observation interval.

### Second complete snapshot — run 43143888820

- 30/30 SEC requests succeeded; snapshot complete.
- Same 1,022 Form 4 and 18 Form 4/A accessions; 2,147 entity rows.
- **0 new accessions**, **0 changed entity-row sets**, **0 missing accessions** relative to the prior complete snapshot.
- No gap over 90 minutes; elapsed time from the previous complete capture end to the next capture start was **8.839 minutes**.
- Zero target structural errors and zero row-fingerprint conflicts.
- The cumulative ledger reached two captures and 1,040 unique accessions.

The second snapshot validates repeatability and ledger continuity, but it does not retroactively bound the first observation of the initial 1,040 accessions. No new accession arrived in the second interval, so this pair of runs has not yet demonstrated a newly observed accession with a non-left-censored interval.

## Phase 309 timestamp correction

Code review found that the first ledger implementation used the overall capture start as the interval end for every accession. That timestamp precedes the actual page response and is not a valid upper bound on when the collector first observed the accession.

Phase 309 changes the event timestamp to the **earliest successful Atom page response completion containing any row for that accession**, while preserving the corresponding poll-start time and page offset separately. Entity rows remain unioned across pages. If an event timestamp precedes the previous complete-capture boundary, the interval is marked invalid rather than admitted.

This is a collector-observation interval only. It is not the SEC's exact first-public timestamp and does not establish strict PIT until repeated live captures demonstrate the behavior and gaps remain controlled.

## Interpretation limits and frozen controls

- The RSS current-feed is a rolling snapshot, not a historical archive.
- Exact first-public timestamp: **not verified**.
- The first 1,040 accessions are left-censored at the start of prospective capture.
- PAC/deletion events are not captured by this query.
- Strict PIT admission, return/alpha, bootstrap/LOO and chronological OOS: **not authorized / not run**.
- Holdout used: **false**.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, production, universe, capital and parameters: unchanged.
- No vendor purchase, email sent, PR opened or merged.
