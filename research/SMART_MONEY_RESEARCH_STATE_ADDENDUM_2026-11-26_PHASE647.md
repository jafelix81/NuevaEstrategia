# Smart Money Research State Addendum — Phase 647

**Audit cutoff:** 2026-11-26 18:18 UTC  
**Phase 647 files:** report `8cfaa79` (subsequently clarified in `1e51932` and `d37bee0`); JSON `67a1a05` (subsequently extended in `24efc83`); state addendum initially committed as `e8a66188e8395a0a6bb9cbe642f9209562b6715f`; subsequent audit-trail corrections brought main to `3ba685bbf34cfb1e0f2a6089779c064b01910d48`.  
**Disposition:** Phase 646 preregistered Russell design now has a validated fixed-reference feature construction. Both currently observed Russell events are below the fixed high-crowding threshold. No outcome data or alpha test.

## Completed

- [Phase 646](PHASE646_CFTC_RUSSELL_FROZEN_ARCHIVE_REFERENCE_PREREGISTRATION_2026-11-26.md): separate Russell-only preregistration, distinct from frozen ES/NQ Phase 387.
- [Phase 647 report](PHASE647_CFTC_RUSSELL_FIXED_REFERENCE_FEATURE_VALIDATION_2026-11-26.md) and [machine-readable summary](PHASE647_CFTC_RUSSELL_FIXED_REFERENCE_FEATURE_VALIDATION_2026-11-26.json).
- Historical source: 3,035 total CFTC TFF rows; Russell E-mini code 239742 has 482 rows, with 2018-09-25 and 2019-12-24 excluded, leaving 480 unique finite reference values from 2017-08-15 to 2026-11-03.
- Snapshot manifest created 2026-11-13 23:03:38Z; baseline persisted to main 2026-11-14 00:44:59Z. Use the latter as the conservative project-knowledge bound.
- Fixed-reference empirical mid-rank feature validated against the two prospective events:
  - 2026-11-10: LM net/OI -10.0843%, percentile 40.625%, not high.
  - 2026-11-17: LM net/OI -9.2126%, percentile 45.4167%, not high.
- High-crowding threshold remains P >= 0.80. No low-percentile alternative or other category was searched.

## Current source / operational state

- Actions: 8,350 total; latest 20 inspected; zero active/queued.
- Latest natural SEC runs remain Form 4 [45848689364], 13F [45839454376], Form 144 [45827105431]. Their artifacts were downloaded and inspected; all live jobs succeeded, but each source still has zero signal-eligible observations.
- No later natural SEC capture is visible as of the audit cutoff. Issue #194 remains the schedule-delivery record; no manual dispatch or rerun.
- CFTC [45753716471] had no new report/revision. Official release calendar lists 2026-11-30 3:30 p.m. ET as the next release. The general semiweekly COT announcement does not establish a TFF transition.
- FINRA Reg SHO [45754121648] rejected all eight files, with BCPC/TPC facility-overlap diagnostics; zero accepted rows.
- Phase 20C remains NO-GO under Phase 593; its stale branch is not merged.

## Hard gates still open

1. Phase 646 training gate: 52 matured prospective observations, at least 20 high and 40 non-high.
2. Phase 646 evaluation gate: 150 prospective observations, at least 30 high and 100 non-high.
3. Freeze a permitted, reproducible Russell-proxy adjusted-OHLC and VIX source before accessing any outcome.
4. Continue first-seen CFTC capture; do not backdate historical archive rows or change Phase 387.
5. Continue natural SEC capture; no manual polls.

## Strategy controls

- Signals admitted: **0**.
- Incremental alpha vs LTM/F80: **none demonstrated**.
- New OOS / bootstrap / LOO: **0**.
- Price outcomes inspected: **no**.
- Holdout remains sealed.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No universe, parameters, exposure, costs, capital, holding-period or production changes.
- Options-data budget remains **USD 0**.
