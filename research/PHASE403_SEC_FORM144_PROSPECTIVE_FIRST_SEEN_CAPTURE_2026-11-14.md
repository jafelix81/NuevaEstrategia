# Phase 403 — Prospective SEC Form 144 / 144-A first-seen capture

**Date:** 2026-11-14 UTC  
**Status at implementation:** capture instrumentation prepared; first live bootstrap is triggered by the branch workflow. This is a data-availability audit only.

## Purpose

Phase 402 established that ACCEPTANCE-DATETIME orders filing versions but is not a certified first-public-receipt timestamp. The SEC Webmaster FAQ says there is no timestamp that identifies when a filing first becomes available on sec.gov; availability is often 1–3 minutes after acceptance, may take longer, and is not guaranteed. A prospective first-seen ledger is therefore required before any same-day or intraday use can even be considered.

The SEC explicitly supports RSS subscriptions from Latest Filings searches and permits filtering by company, CIK or Form Type. The SEC developer page also documents the daily/quarterly index and Oldloads/Feed archives. This phase uses the official Latest Filings Atom endpoints for Form 144 and 144/A, with a one-hour scheduled poll. Sources:

- https://www.sec.gov/about/rss-feeds
- https://www.sec.gov/about/developer-resources
- https://www.sec.gov/about/webmaster-frequently-asked-questions
- https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/file-form-144-electronically

## Capture design

- Poll two official Latest Filings Atom queries: type=144 and type=144/A.
- Request up to 100 entries per feed; deduplicate by accession across feeds.
- Store one immutable first-seen row per accession. A Form 144/A is a separate filing version, not a second proposed sale.
- Record feed updated exactly as supplied, but do not assume it is the acceptance time.
- Record the feed's archive-path CIK separately from XML issuer CIK and filer CIK. Candidate membership is determined only from the parsed XML issuer CIK.
- Fetch the complete submission text for new accessions to capture ACCEPTANCE-DATETIME and the embedded Form 144 XML. Fall back to primary_doc.xml if the complete submission does not yield an XML block.
- The 290-CIK Phase 401 manifest is used only as a frozen current-candidate diagnostic. It is not an effective-dated F80 security master and does not prove historical F80 membership.
- Record the prior successful poll as an interval lower bound only when neither the previous nor current feed poll indicates a possible 100-entry window gap. The current response-receipt time is an upper bound, not exact public availability.
- Preserve a poll summary artifact for each run and append event/state data to research/data/sec_form144_first_seen/.
- The scheduled workflow runs hourly. A missed or delayed GitHub Actions run is not treated as an exact availability clock; full-feed conditions trigger a gap flag and suppress the interval lower bound.

## Timing fields and interpretation

Each new accession stores:

- submission_acceptance_utc — converted from the SEC complete-submission header in America/New_York time.
- feed_updated_utc — Atom feed timestamp, preserved as a separate field.
- first_seen_interval_lower_bound_utc — previous successful poll completion, only if the interval is not gap-contaminated.
- first_seen_interval_upper_bound_utc — response-receipt timestamp for the feed containing the accession.
- first_seen_at_utc — the upper-bound receipt timestamp; not a certified exact public-availability timestamp.
- feed_path_cik, issuer_cik, and filer_cik — distinct identity fields.

No corrected issuer, seller, security class, tranche or quantity is backdated. Each 144/A retains its own accession and first-seen interval.

## Safety and research controls

- signal_eligible=false for every captured event.
- same_day_intraday_use_authorized=false.
- public_availability_certified=false.
- No forward returns, alpha, OOS, bootstrap, LOO or holdout tests.
- No feature is admitted to F80/LTM.
- The historical noOfUnitsOutstanding denominator remains killed.
- No vendor data or paid source is acquired.
- SEC requests reuse the repository's declared SEC User-Agent and existing 0.20-second inter-request throttle, below the SEC's 10 requests/second ceiling.

## Known limitations

1. Hourly GitHub Actions polling creates a coarse upper-bound interval; it cannot validate a 1–3 minute latency distribution or certify exact first-public availability.
2. GitHub scheduled workflows can be delayed. A full 100-entry feed with the prior latest accession missing is flagged as a possible coverage gap; the interval is not used as a lower bound.
3. The RSS feed is a current feed, not a historical archive. The first bootstrap has no lower bound and is not a prospective interval observation.
4. The 290-CIK candidate set is not a historical security master. Issuer matches are diagnostic only.
5. XML retrieval failures remain in the event ledger as unresolved; no event is silently dropped.
6. No inference is made from a Form 144 that the proposed sale was executed.

## Promotion gate

This phase only establishes whether a reproducible prospective receipt ledger can be maintained. Before any economic test, the project still needs historical F80 membership, effective-dated issuer/security identity (including inactive/predecessor/delisted securities), complete amendment lineage, price/corporate-action coverage, and a separately preregistered hypothesis. The conservative next-regular-session rule remains in force until first-seen capture has enough reliable coverage to justify a change.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
