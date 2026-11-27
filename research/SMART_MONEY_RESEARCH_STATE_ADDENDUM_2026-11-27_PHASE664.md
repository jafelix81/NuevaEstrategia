# Smart Money Research state addendum — Phase 664

**2026-11-27 UTC**

- Audited the latest Form 144 scheduled capture, run [46015828465](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46015828465). Both jobs succeeded; no new accessions/events, 53 feed-observation rows appended, no feed-window gap. Ledger: 855 accessions / 5,651 detail rows; 10 old accessions enriched by 56 detail rows; 148 remain in the backfill queue.
- Reconciled the poll with Phase 516: 807 research-observation-eligible filing headers, 48 initial-baseline headers without a lower bound, zero public-availability-certified and zero signal-eligible headers.
- Found a Phase 549 output-label defect: 322 formal plan-date accessions / 855 total accessions = 37.66%, but the field was named `formal_plan_date_pct_of_bounded_accessions`. It was not calculated over the 807 PIT-eligible accessions. The actual plan-date/PIT overlap is unknown; do not calculate 322/807.
- Phase 664 renames the metric to `formal_plan_date_pct_of_all_accessions`, adds an explicit denominator-scope label, and carries Phase 516 aggregate PIT counts into the Phase 549 output without inventing an accession-level intersection.
- The descriptive cohort remains 322 formal plan dates, 134 distinct dates, 24 positive explicit remarks, 4 negative explicit, 3 ambiguous and 824 no mention. Four negative sell-to-cover/tax-withholding notices cluster on Fermi (CIK 0002071778), 2026-11-19, 2,253,270 proposed units. Form 144 remains a proposed-sale notice, not execution confirmation.
- Phase 664 is an offline code/measurement correction only. No return or alpha test, chronological OOS, bootstrap, LOO or holdout was run. No signal promoted. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; no vendor contact or paid data, USD 0.

See `research/PHASE664_FORM144_PLAN_DENOMINATOR_PIT_SCOPE_CORRECTION_2026-11-27.md` and its JSON summary.
