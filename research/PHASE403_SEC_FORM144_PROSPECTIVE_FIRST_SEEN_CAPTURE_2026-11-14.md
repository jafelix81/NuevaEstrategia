# Phase 403 — Prospective SEC Form 144 / 144-A first-seen capture

**Date:** 2026-11-14 UTC  
**Status:** first live bootstrap completed successfully; append-only capture and acceptance-time enrichment are active on the research branch. No return tests or signals.

## Purpose

Phase 402 established that ACCEPTANCE-DATETIME orders filing versions but is not a certified first-public-receipt timestamp. The SEC Webmaster FAQ says there is no timestamp that identifies when a filing first becomes available on sec.gov; availability is often 1–3 minutes after acceptance, may take longer, and is not guaranteed. A prospective first-seen ledger is therefore required before any same-day or intraday use can even be considered.

The SEC explicitly supports RSS subscriptions from Latest Filings searches and permits filtering by company, CIK or Form Type. The SEC developer page also documents daily/quarterly index files and Oldloads/Feed archives. This phase uses the official Latest Filings Atom endpoints for Form 144 and 144/A. Sources:

- https://www.sec.gov/about/rss-feeds
- https://www.sec.gov/about/developer-resources
- https://www.sec.gov/about/webmaster-frequently-asked-questions
- https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/file-form-144-electronically

## First live bootstrap — run 43639113589

The initial workflow invocation exposed a package-import issue because the script was executed as a file. The workflow was corrected to invoke the module with python -m; the corrected run passed both offline regression and live capture. The failed invocation did not write data.

| Measure | Result |
|---|---:|
| Form 144 feed entries returned | 50 |
| Form 144/A feed entries returned | 5 |
| Overlap between the two feeds | 3 |
| Unique accessions captured | 52 |
| XML records parsed | 52/52 |
| Issuer CIK / issuer name / filer CIK / seller fields present | 52/52 each |
| Current Phase 401 candidate-issuer matches | 5 |
| Signal-eligible events | 0 |

The type=144 feed contained 47 Form 144 and three Form 144/A records. The dedicated type=144/A feed returned five records, of which two were additional accessions. This overlap is why both feeds are retained and deduplicated by accession.

The type=144 request asked for 100 records but returned 50. The implementation therefore uses 50 as the conservative observed feed-window threshold: if a future response contains 50 entries and the previous latest accession is absent, it flags a possible feed-window gap and suppresses the interval lower bound. This is an observed response size, not a guarantee that the SEC's feed limit is permanently 50.

The bootstrap was received from 2026-11-14 20:45:08Z to 20:45:21Z. The returned feed timestamps span 2026-11-12 23:34:06Z through 2026-11-14 01:43:19Z. The feed was therefore a historical current-feed snapshot at bootstrap, not a real-time prospective interval. All 52 records have INITIAL_BASELINE_NO_LOWER_BOUND and remain research-ineligible.

The five current-candidate issuer matches are diagnostic only. The 290-CIK Phase 401 set is not an effective-dated F80 security master and does not prove historical F80 membership.

## Acceptance-time enrichment

The complete submission text was retrieved for all 52 accessions and supplied the XML block for 42; ten required the primary_doc.xml fallback. The complete-submission header did not yield a parseable ACCEPTANCE-DATETIME in this sample. A separate filing-detail-page reconciliation writes successful matches to an append-only acceptance_reconciliation.csv keyed by accession, avoiding any rewrite of the immutable first-seen rows. The 52/52 exact equality of Atom updated and SEC Accepted should be treated as a sample-specific validation of the feed timestamp's acceptance-time semantics, not as proof of first-public availability.

For each accession, the reconciliation records:
- SEC filing-detail Accepted time converted from America/New_York to UTC;
- filing date;
- the difference between Atom updated and SEC Accepted;
- the difference between first-seen upper bound and SEC Accepted;
- source URL and reconciliation run;
- timing anomalies, if any.

The corrected reconciliation run 43639405055 retrieved the filing-detail pages for all 52 bootstrap accessions: 52/52 acceptance timestamps were recovered, with zero unresolved rows and zero negative timing anomalies. Atom updated equaled SEC Accepted to the exact second for all 52/52 records. This is strong evidence that the Atom updated field mirrors acceptance time in this sample, but it does not prove first-public availability at acceptance. The bootstrap first-seen upper bound occurred 68,509–162,662 seconds after acceptance (median 83,007 seconds), because the first capture was a weekend baseline of older filings; these lags are not a publication-latency estimate and none of the 52 events is a prospective interval observation.

## Capture design

- Poll two official Latest Filings Atom queries: type=144 and type=144/A.
- Request 100 entries per feed; the first live response returned 50 in the 144 feed and five in the 144/A feed. The conservative observed full-window threshold is set to 50 until further samples confirm the endpoint's maximum; deduplicate by accession across feeds.
- Store one immutable first-seen row per accession. A Form 144/A is a separate filing version, not a second proposed sale.
- Record Atom updated exactly as supplied, but do not assume it is the acceptance time.
- Record the feed archive-path CIK separately from XML issuer CIK and filer CIK. Candidate membership is determined only from the parsed XML issuer CIK.
- Fetch the complete submission text for new accessions to retrieve the XML block; fall back to primary_doc.xml if needed.
- Use the Phase 401 290-CIK manifest only as a current-candidate diagnostic.
- Record the prior successful poll as an interval lower bound only when neither the previous nor current feed poll indicates a possible feed-window gap. The current response-receipt time is an upper bound, not exact public availability.
- Preserve a poll summary artifact for each run and append event/state data to research/data/sec_form144_first_seen/.
- Schedule hourly polling. A missed or delayed GitHub Actions run is not treated as an exact availability clock.

## Timing fields and interpretation

Each first-seen row stores:

- submission_acceptance_utc — when recoverable from the complete submission header;
- feed_updated_utc — Atom timestamp, preserved separately;
- first_seen_interval_lower_bound_utc — previous successful poll completion, only if the interval is not gap-contaminated;
- first_seen_interval_upper_bound_utc — response-receipt timestamp for the feed containing the accession;
- first_seen_at_utc — the upper-bound receipt timestamp, not certified exact public availability;
- feed_path_cik, issuer_cik and filer_cik as distinct identity fields.

Acceptance-time enrichment is stored separately in acceptance_reconciliation.csv. No corrected issuer, seller, security class, tranche or quantity is backdated. Each 144/A retains its own accession and first-seen interval.

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
2. GitHub scheduled workflows can be delayed. A full 50-entry response with the prior latest accession missing is flagged as a possible coverage gap. The second bootstrap poll found the prior latest accession in both feeds and reported no gap.
3. The RSS feed is a current feed, not a historical archive. The bootstrap has no lower bound and is not a prospective interval observation.
4. The 290-CIK candidate set is not a historical security master. Issuer matches are diagnostic only.
5. XML or filing-detail retrieval failures remain unresolved and are not silently converted into valid observations.
6. No inference is made from a Form 144 that the proposed sale was executed.

## Promotion gate

This phase only establishes whether a reproducible prospective receipt ledger can be maintained. Before any economic test, the project still needs historical F80 membership, effective-dated issuer/security identity (including inactive/predecessor/delisted securities), complete amendment lineage, price/corporate-action coverage, and a separately preregistered hypothesis. The conservative next-regular-session rule remains in force until first-seen capture has enough reliable coverage to justify a change.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
