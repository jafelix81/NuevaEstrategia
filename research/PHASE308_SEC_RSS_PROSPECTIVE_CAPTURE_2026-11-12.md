# Phase 308 — SEC RSS prospective first-observation capture

**Date:** 2026-11-12  
**Status:** capture infrastructure committed; initial run pending.  
**Branch:** phase308-sec-rss-prospective-capture

## Purpose

Phase 307 demonstrated that owner=only isolates Form 4 ownership filings from unrelated 4-prefixed forms while preserving the page-zero Form 4 accession set. Phase 308 converts that finding into a repeatable prospective capture system.

## Capture design

- Query SEC Latest Filings Atom with owner=only, separately for type=4 and type=4/A.
- Scan count=100 pages with 20-row overlap, exact form-token filtering, accession/entity reassembly, stable page-zero recheck and a 50-page cap.
- Preserve raw Atom pages, response headers, poll-start/completion UTC times and SHA-256 in each run artifact.
- Maintain a cumulative accession ledger in research/data/sec_rss_prospective_ledger.json.
- For a newly observed accession, record first_observed_at_utc and the interval from the previous complete capture end to the current first page poll start. If there is no previous complete capture, mark the observation left-censored.
- Keep Atom updated as a separate acceptance-time field; never relabel it as first-public time.
- Record gaps greater than 90 minutes, incomplete scans, missing accessions between complete snapshots, entity-row changes and raw-page hashes.
- The capture workflow is triggered by an hourly automation updating research/SEC_RSS_CAPTURE_TRIGGER.json. It must not launch a second run while a Phase 308 capture is in progress.
- Raw artifacts are retained for 90 days; the cumulative ledger and run summaries are committed to the research branch.

## Interpretation limits

This creates prospective first-observation intervals, not exact first-public timestamps. The interval is only bounded when a prior complete capture exists and no coverage gap invalidates that boundary. No predictive value or alpha is implied by the capture itself.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No production, universe, capital, parameter or holdout changes. No return, bootstrap/LOO or chronological OOS tests are performed in this phase.
