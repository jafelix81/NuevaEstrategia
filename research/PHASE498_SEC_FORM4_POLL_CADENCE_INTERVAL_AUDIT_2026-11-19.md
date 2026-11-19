# Phase 498 — SEC Form 4 poll cadence and first-seen interval audit

**Audit cutoff:** 2026-11-19 11:15 UTC  
**Main baseline:** `95c304d5b07653cbe817912f8b713b30ad8fdbbf`  
**Disposition:** **HOURLY CADENCE NOT DEMONSTRATED; ALL 655 BOUNDED EVENTS HAVE 6.47–8.54 HOUR RECEIPT INTERVALS. DAILY NEXT-SESSION TIMING REMAINS CONSERVATIVELY BOUNDABLE; NO SIGNAL PROMOTION.**

## 1. Preflight

- Main HEAD: `95c304d5b07653cbe817912f8b713b30ad8fdbbf`.
- Actions inventory: 7,886 total runs; latest 100 inspected; no queued, in-progress, waiting or requested runs in that page at cutoff.
- Latest Phase 497 PR CI [44509660064](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44509660064): offline regression passed; live audit skipped as designed.
- Latest scheduled Form 4/4-A poll [44505739718](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44505739718) completed successfully. No duplicate capture was started.
- Open PRs: 56. Existing Phase 13D/G PR #37 remains draft and blocked on the SEC contact User-Agent secret; older FINRA branches/PRs were not modified.
- The current collector declares `17 * * * 1-5` (hourly weekdays at minute 17). This audit uses only persisted receipts and does not dispatch, rerun, or alter a workflow.

## 2. Observed poll cadence

The mainline feed-observation ledger contains three successful scheduled poll windows:

| Run | First feed receipt UTC | Last feed receipt UTC | Feed observations |
|---|---|---|---:|
| 44380395679 | 2026-11-18 19:26:00 | 2026-11-18 19:26:08 | 2 |
| 44440313382 | 2026-11-19 01:54:11 | 2026-11-19 01:54:40 | 20 |
| 44505739718 | 2026-11-19 10:27:04 | 2026-11-19 10:27:06 | 2 |

The time from the previous poll's final receipt to the next poll's first receipt was:

- 6 h 28 min 03 s (6.4675 h)
- 8 h 32 min 24 s (8.5400 h)

These are materially longer than the declared one-hour cadence. Only three schedule-triggered runs are visible in the latest run inventory for this ledger. The evidence is consistent with delayed or missed scheduled executions, but does not establish that the workflow is disabled. No cron change or manual catch-up was made.

## 3. Event-ledger interval census

The append-only Form 4 event ledger contains 690 rows:

| First-seen classification | Rows |
|---|---:|
| Initial baseline without a lower bound | 35 |
| Bounded metadata-only | 655 |
| **Total** | **690** |

The 655 bounded events are split across:
- Run 44440313382: 637 events, lower bound 2026-11-18 19:26:08 UTC; upper bounds 2026-11-19 01:54:11–01:54:34 UTC.
- Run 44505739718: 18 events, lower bound 2026-11-19 01:54:40 UTC; upper bound 2026-11-19 10:27:04 UTC.

| Interval-width statistic | Hours |
|---|---:|
| Minimum | 6.4675 |
| 25th percentile | 6.4681 |
| Median | 6.4700 |
| 75th percentile | 6.4714 |
| 90th percentile | 6.4728 |
| Maximum | 8.5400 |
| At most 1 hour | 0 |
| At most 2 hours | 0 |
| Over 6 hours | 655 |

All bounded intervals are materially wider than one hour. The word “bounded” means only that a prior successful poll watermark and a later receipt bound the observation interval; it does not imply fine-grained or exact first-publication timing.

## 4. Conservative daily timing implication

The collector receipt is an **upper bound** on when this collector had observed an accession, not the exact public-availability time.

- The 637-event cohort's latest upper bound is 2026-11-19 01:54:34 UTC (2026-11-18 20:54:34 America/New_York), after the prior day's regular session.
- The 18-event cohort's upper bound is 2026-11-19 10:27:04 UTC (05:27:04 America/New_York), before the 2026-11-19 regular-session open.
- Therefore, using the conservative rule “first regular session whose open occurs after the collector receipt upper bound,” both bounded cohorts have 2026-11-19 as their first safe regular-session date.

This is a daily timing bound only. It does **not** certify exact public availability, authorize same-day intraday use, resolve security identity, identify the reporting owner, establish transaction discretion, or prove historical F80 membership. The 35 initial-baseline rows have no lower bound and remain unusable for event timing.

The broad polling gaps reduce freshness and make intraday research unsuitable. They do not, by themselves, prevent a next-session daily feature once all other identity, transaction-semantics and universe gates are satisfied.

## 5. Eligibility and decision

- Total events: 690.
- Research-observation eligible: 0.
- Signal eligible: 0.
- Same-day intraday use: not authorized.
- Historical security identity: not verified.
- Historical F80 membership: not verified.
- Alpha test: not authorized.

**Decision: TIMING_BOUND_ONLY_NO_SIGNAL_PROMOTION.**

Do not infer one-hour polling from the cron declaration. Continue to use actual poll receipts and their conservative upper bounds. Do not backdate any event to the feed `updated` timestamp or acceptance timestamp.

## 6. Next gates

1. Observe the next naturally scheduled Phase 476 poll; do not manually duplicate it.
2. Recompute receipt gaps and interval widths after each successful poll. If long gaps persist, treat the source as next-session/daily metadata only.
3. Keep Form 4 content/owner/security mapping separate from arrival metadata. The 637-document Phase 497 cohort remains a one-filing-date census, not a historical return sample.
4. Keep FINRA post-Phase-495 live parser validation pending until its existing 22:30/23:30 UTC windows; the earlier run 44453548570 used the pre-fix main SHA and rejected all eight files.
5. Keep SEC 13D/G parent retrieval blocked until the repository secret `SEC_USER_AGENT` contains a project identifier and monitored contact email. Do not retry SEC archive requests before that human configuration is confirmed.

## 7. Frozen controls

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameter, holding-period, capital, exposure, cost, holdout or production change. No forward-return, event-study, OOS, bootstrap, LOO or holdout test was run.
