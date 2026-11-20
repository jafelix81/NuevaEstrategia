# Smart Money Research state addendum — Phase 378

**As of:** 2026-11-19 local / 2026-11-20 UTC  
**Mainline baseline:** unchanged; this work remains on the draft CFTC research branch / PR #52.

## CFTC TFF source status

- Phase 378 corrected the Phase 377 weekly coverage metric to group actual report dates by ISO week, avoiding false missing-Tuesday flags on holiday-shifted report weeks.
- Hosted run [44648241623](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44648241623) passed 19/19 tests and retrieved 47,420 rows / 90 fields with stable metadata and reconciled counts.
- Three primary index contracts (13874A, 209742, 124603) each have 1,066 consecutive ISO-week slots from 2006-06-13 through report date 2026-11-10, including 14 shifted report dates and no missing or duplicate ISO weeks.
- Russell 239742 has 602 report dates over the full span, but a 483-week latest continuous segment from 2017-08-14 through 2026-11-09; do not treat it as a continuous 2006–2026 series.
- Historical release-time PIT is still not certified. Report date is the position date, not the publication timestamp. Phase 384 first recorded the 2026-11-10 report at 2026-11-18 03:44:57 UTC; it is research-observation eligible but signal-ineligible. The following scheduled capture found no new report/revision.
- CFTC semiweekly publication is announced as a plan for end-2026; the existing business-day poll and cadence-suppression tests remain in place until actual rollout is verified.

## Research disposition

CFTC TFF remains a **conditional macro equity-index positioning** source. TFF categories are business-purpose classifications, not verified trader identities. Do not call them smart-money identity. No features, returns, alpha, OOS, bootstrap, LOO or holdout tests were run. Historical backfill remains excluded from signal features. No change to `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, capital, exposure, costs or production.

See [Phase 378 report](PHASE378_CFTC_TFF_HOLIDAY_SHIFTED_WEEKLY_SLOT_RECONCILIATION_2026-11-19.md) and [Phase 378 summary](PHASE378_CFTC_TFF_HOLIDAY_SHIFTED_WEEKLY_SLOT_RECONCILIATION_SUMMARY_2026-11-19.json).
