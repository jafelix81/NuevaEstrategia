# Smart Money Research State Addendum — Phase 646

**Audit cutoff:** 2026-11-26 18:18 UTC  
**Main commit:** `05ad6c11006713cd2d75d7cc6ea0f3310a1b0ab1`  
**Disposition:** new Russell-only CFTC small-cap downside-risk hypothesis preregistered. No feature values or outcomes inspected; no signal or strategy change.

## New research protocol

- [Phase 646 preregistration](PHASE646_CFTC_RUSSELL_FROZEN_ARCHIVE_REFERENCE_PREREGISTRATION_2026-11-26.md) defines a fixed reference distribution from the 480 valid Russell E-mini archive observations in the baseline snapshot created 2026-11-13 23:03:38Z.
- That snapshot timestamp is the project's knowledge time for the fixed reference dataset. It is earlier than both prospective first-receipt events (2026-11-18 03:44:57Z and 2026-11-21 03:17:36Z).
- Historical rows are permitted only as a frozen reference distribution for prospective Russell observations received after the snapshot. They are not historical signals, labels, training observations or return data.
- This is explicitly separate from Phase 387 ES/NQ. Phase 387's prohibition on historical archive rows in its prospective feature reference is unchanged.
- Fixed primary feature: Leveraged Money net/OI empirical mid-rank against 480 valid reference rows; high crowding threshold fixed at 0.80.
- Fixed primary outcome: 20-session Russell-proxy downside drawdown severity, subject to a separately frozen, permitted and reproducible adjusted-OHLC source.
- Walk-forward training/evaluation, event-count gates, block bootstrap, HAC and leave-one-year-out requirements are specified before outcomes are accessed.
- No price outcomes or feature percentile values were accessed in Phase 646.

## Operational preflight

- Actions inventory: 8,350 total runs; latest 30 inspected; zero queued/in-progress.
- Latest natural SEC captures remain Form 4 [45848689364](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45848689364), 13F [45839454376](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45839454376), and Form 144 [45827105431](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45827105431). All jobs succeeded, but each source still has zero signal-eligible observations.
- Current committed poll state has not advanced after those runs. No later natural SEC run is visible as of 18:18 UTC. This remains a delivery gap, not proof of disabled workflows; issue #194 tracks it.
- CFTC latest scheduled run [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471) recorded no new report or revision. The official CFTC calendar still lists the next 2026 report release on 2026-11-30 at 3:30 p.m. ET; the CFTC's 2026-10-27 announcement of a planned semiweekly COT schedule is not proof that TFF Futures Only has transitioned. Continue actual weekday polling and use first receipt only.
- FINRA Reg SHO latest run [45754121648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648) rejected all eight files; zero rows admitted.
- Phase 20C branch is 12 commits ahead / 680 behind main. Phase 593 NO-GO remains authoritative. No branch merge, manual workflow dispatch, rerun or duplicate poll.

## Current source disposition

- CFTC Russell: conditional prospective small-cap risk-context hypothesis under Phase 646.
- CFTC ES/NQ: Phase 387 unchanged; weekly prospective-only design remains frozen.
- SEC Form 4 / 13F / Form 144: operational capture and descriptive backfill; no eligible signal rows.
- SEC 13D/G: 43/44 parent retrieval; identity/CUSIP exceptions remain quarantined.
- FINRA T1 ATS: venue/firm concentration only; identity/universe/inactive-security gates remain open.
- FINRA Reg SHO: quarantine.
- Options / OPRA / Open-Close / OCC / MIDAS: feasibility only; no paid data or license authorized; options budget USD 0.

## Quantitative controls

- Signals admitted: **0**.
- Incremental alpha vs LTM/F80: **none demonstrated**.
- New OOS / bootstrap / LOO: **0**.
- Holdout remains sealed.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No universe, parameter, capital, exposure, cost, holding-period or production changes.

## Next gates

1. Implement Phase 646's fixed-baseline percentile calculation as a separate Russell-only path with unit tests for the snapshot timestamp, the two excluded archive dates, report-date ordering, no backdating and first-seen session mapping.
2. Freeze and validate a permitted reproducible Russell-proxy adjusted-OHLC source before opening any forward outcomes.
3. Continue actual CFTC first-receipt capture; do not assume the semiweekly transition until new TFF report dates prove it.
4. Continue natural SEC captures; do not dispatch manually while schedule delivery is being observed.
5. Keep Phase 387, FINRA Phase 20C and F80 controls unchanged.
