# Phase 477 — SEC Form 4/4-A feed timestamp consistency gate

**Audit cutoff:** 2026-11-18 11:05 UTC  
**Base main:** 9a80a4a6e2bd411556b4e48fada9dda51dd424c3  
**Disposition:** tighten Phase 476 event-level interval classification before the first live poll.

## 1. Finding

Phase 476 correctly required a previous successful poll and discovery of the prior accession watermark. However, its event-level bounded flag did not compare the SEC Atom entry's own updated timestamp with the local polling interval.

That was too permissive. A newly observed accession can carry an Atom updated timestamp at or before the previous successful poll. That may indicate a stale/reordered feed entry or a delayed index insertion. Local first-seen receipt alone does not establish that the event first became available inside the interval.

## 2. New event-level rule

The collector now separates poll continuity from event timestamp consistency.

A poll can be marked POLL_WATERMARK_BOUNDED only when:
1. it is a scheduled poll;
2. a prior accession watermark exists;
3. the watermark is found during complete pagination; and
4. a previous successful poll end exists.

An individual event is marked BOUNDED_METADATA_ONLY only when, in addition:
- the Atom updated timestamp parses with an explicit timezone;
- Atom updated is strictly later than the previous successful poll end; and
- Atom updated is no later than the local response receipt timestamp.

Otherwise it is quarantined as one of:
- FEED_OR_RECEIPT_TIMESTAMP_UNKNOWN;
- FEED_TIMESTAMP_NOT_AFTER_PREVIOUS_POLL;
- FEED_TIMESTAMP_AFTER_FIRST_SEEN;
- or the relevant baseline/gap/manual status.

This comparison is a consistency filter, not a claim that Atom updated is the exact public-availability timestamp. The local first-seen receipt remains an upper bound. All records remain research-ineligible and signal-ineligible.

## 3. Regression coverage

The canonical Phase 476 test file now includes 35 offline tests. New cases cover stale, missing and future Atom timestamps, plus an end-to-end two-poll example where the source timestamp is strictly inside the observed local interval.

The end-to-end test confirms:
- first poll is baseline and unbounded;
- second poll finds the prior accession watermark;
- only an event whose feed timestamp falls inside the local interval receives BOUNDED_METADATA_ONLY;
- the lower bound is the previous successful poll end;
- research_observation_eligible and signal_eligible remain false.

## 4. Operational status

- Phase 476 is already merged in main at 13155f11acdc3907c66213d17c0143a3c45e917e.
- No live Form 4/4-A poll was run by this phase.
- The first scheduled Phase 476 run remains a baseline; a later successful poll is required.
- No SEC filing XML/text, transaction rows, owner names, prices or raw Atom payloads are downloaded or stored.
- No manual dispatch or duplicate workflow was initiated.

## 5. Research disposition

This is a point-in-time integrity improvement only. It does not create an insider signal or solve issuer/security identity, historical F80 membership, reporting-owner attribution, transaction-code semantics, 10b5-1 interpretation or return-label availability.

No event study, backtest, alpha, OOS, bootstrap, LOO or holdout test was run. F80_TOP20_PARTIAL50_BASELINE_C20 and production remain frozen.
