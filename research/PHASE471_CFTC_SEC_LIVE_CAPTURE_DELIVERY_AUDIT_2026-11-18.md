# Phase 471 — CFTC first prospective receipt and SEC pagination live audit

**Audit time:** 2026-11-18T04:06:34Z  
**Main HEAD at preflight:** `079399dfaada718d5ba38d2bdceb37ba89f52890`  
**Disposition:** CFTC Phase 384 has recorded its first scheduled prospective report batch (four contract rows, including the two preregistered ES/NQ contracts). SEC Form 144 pagination has now passed its first live scheduled validation with the prior accession recovered and no feed-window gap. Neither source has produced an admitted trading signal.

## 1. Preflight and duplicate-run control

- Queried the latest 30 repository Actions runs: 7,767 total runs reported; latest relevant scheduled runs were SEC Phase 403 [44228413864](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228413864) and CFTC Phase 384 [44232546204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204).
- Explicit repository-wide status queries returned **0 in-progress** and **0 queued** runs at the audit cutoff.
- Enumerated three branch pages: **300 branches**. Open pull requests: **56**.
- No workflow was dispatched, rerun, duplicated, or cancelled.
- PR [#130](https://github.com/jafelix81/NuevaEstrategia/pull/130) merged at 2026-11-18 03:13:38 UTC as `62ab4a2ce997e708d3319537d91707be5008f40a`. The SEC scheduled capture commit `baf2ddf41d65fc05ed648ee89bdfe91ae5f3c6ae` is an ancestor of that merge. CFTC capture commit `079399dfaada718d5ba38d2bdceb37ba89f52890` is current main HEAD at this audit.
- Latest-30 run inventory contained no active run; the explicit status queries are the authoritative active/queued check for this audit.

## 2. CFTC Phase 384 — first prospective receipt confirmed

Scheduled run: [44232546204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204)  
Artifact: [14395926632](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204/artifacts/14395926632)  
Artifact ZIP SHA-256: `e4d9a147e920e3333b1d684a477ac77ef68a1364e9b028c2e3381a34ece795e7`

The scheduled job completed successfully. It ran the 17 Phase 384 unit tests, captured the official TFF Futures Only dataset `gpe5-46if`, committed the append-only event/state update, and uploaded the audit summary.

### Captured observations

- Historical warm-up baseline before this run: **3,035 rows**.
- Total rows after capture: **3,039**.
- New report events: **4**, one per contract code.
- All four report rows are dated **2026-11-10** and have the collector's actual `first_seen_utc = 2026-11-18T03:44:57Z`.
- Per-contract history counts remain 852 for codes `124603`, `13874A`, `209742`, and 483 for `239742`; the four new reports are append-only prospective events, not historical backfill.
- Each event is marked `research_observation_eligible=true`, but `signal_eligible=false`. The run reports `ALPHA_TEST=NOT_AUTHORIZED`, `trade_signal_generated=false`, no forward returns, and no derived features attached to historical backfill.
- The event file is [20261118T034457Z_run44232546204.json](https://github.com/jafelix81/NuevaEstrategia/blob/main/research/data/cftc_tff_prospective/events/20261118T034457Z_run44232546204.json).

The official CFTC release schedule lists the November 10 positions report for release on **November 16, 2026 at 3:30 p.m. ET** (20:30 UTC), delayed for the Veterans Day holiday. Our first collector receipt was 31h 14m 57s after that nominal scheduled release time. This is a collector-latency diagnostic, not an assertion that the Socrata endpoint first became public at the scheduled minute. The only admissible local knowledge clock remains the actual first receipt, and the first usable equity session is the regular session after that receipt (November 18). See the [official release schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm) and [TFF Futures Only dataset](https://publicreportinghub.cftc.gov/Commitments-of-Traders/TFF-Futures-Only/gpe5-46if).

### Scope against the frozen preregistration

Phase 387 preregisters **ES (`13874A`) and NQ (`209742`) only**. DJIA (`124603`) and Russell E-mini (`239742`) remain outside its primary test.

For data QA only, the preregistered `LM_NET_OI = (Leveraged Money long - Leveraged Money short) / open_interest` is:

| Contract | Report date | LM net | Open interest | LM_NET_OI |
|---|---|---:|---:|---:|
| E-mini S&P 500 | 2026-11-10 | -303,060 | 2,017,687 | -15.0202% |
| Nasdaq Mini | 2026-11-10 | +13,967 | 288,717 | +4.8376% |

These are single-observation descriptive values, **not** crowding classifications or predictive results. The primary prior-only percentile `P_t` cannot be calculated until 52 prior valid prospectively first-seen weekly observations exist for the same contract. No historical backfill row may fill that reference window.

Phase 387's event-count and maturity gates remain unchanged. Phase 419 estimated that the full high/non-high training and evaluation event-count gates could require approximately 301 weekly reports (about 5.8 years) under an idealized weekly cadence. This is a planning diagnostic, not a promise of power or a reason to relax the preregistration. If the observed TFF cadence becomes semiweekly or irregular, weekly features remain suppressed and a separate preregistration is required.

### Schedule-delivery caveat

The workflow remains configured for `25 22 * * 1-5` UTC. This run was created at 03:44:45 UTC on November 18, approximately 5h 19m 45s after the prior day's nominal 22:25 UTC slot. GitHub schedule delivery can be delayed; the first-receipt timestamp correctly reflects the actual capture and must not be backdated.

## 3. SEC Phase 403 — pagination validated live, first poll remains a baseline

Scheduled run: [44228413864](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228413864)  
Artifact: [14393319006](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228413864/artifacts/14393319006)  
Artifact ZIP SHA-256: `dd3cae9e7e224491fa32ffaee34b56f3ab6211f57a3bf0384165d5cda1e96775`

Both `offline-regression` and `live-capture` completed successfully. The Phase 454 migration reported `already_current` with 106 rows migrated/verified. The live poll ran from 03:09:51 to 03:10:13 UTC on November 18.

### Form 144 pagination

- Two pages, 100 raw Atom entries each; 100 unique accessions across the pages.
- The previous latest accession `0001950047-26-011220` was found.
- Pagination completed with stop reason `previous_latest_found`.
- `possible_feed_window_gap=false`.
- 90 new accessions were resolved to XML and 90 acceptance timestamps were reconciled; zero acceptance reconciliations remained unresolved.
- 18 issuer matches were found against the 290-CIK candidate manifest. That manifest is explicitly **not** the historical F80 security master.
- Form 144/A returned one page with nine unique accessions, the prior watermark was present, and no new accession was added.
- The run appended 109 feed-observation rows and 90 event rows, with no feed errors.

### Conservative first-poll treatment

This was the first poll after the pagination upgrade, so both feeds correctly report `INITIAL_BASELINE_NO_LOWER_BOUND`. The run had no prior successful poll-start timestamp to bound the interval. Therefore:
- `research_observation_eligible_count=0`;
- `signal_eligible_count=0`;
- `public_availability_certified=false`;
- `alpha_test_authorized=false`;
- `same_day_intraday_use_authorized=false`;
- `f80_changed=false`.

This is a successful live validation of pagination and watermark recovery, **not** a batch of eligible events. A subsequent clean scheduled poll is needed to establish bounded intervals for new accessions. No second post-baseline scheduled poll was visible at the audit cutoff; no duplicate poll was started.

## 4. FINRA Phase 469 — first scheduled capture not yet due

The Phase 469 workflow is present on main with weekday cron `30 22,23 * * 1-5` UTC. At the 04:06 UTC audit cutoff on November 18, its first post-merge scheduled slots (22:30 and 23:30 UTC) were still in the future. No live FINRA capture is claimed. The first scheduled poll remains pending; the historical Phase 31 panel remains diagnostic-only because its original labels used prices before the after-close flow file could be known.

## 5. Research disposition and next gates

1. **CFTC:** prospective sample collection has begun for ES and NQ, but the 52-prior-observation percentile and the fully matured training/evaluation gates are nowhere near satisfied. Continue append-only scheduled capture; do not calculate a high-crowding state yet.
2. **SEC Form 144:** pagination and watermark recovery passed live. Wait for the next scheduled poll to establish a valid lower bound; keep first-poll baseline events ineligible.
3. **FINRA Reg SHO:** inspect the first scheduled Phase 469 capture after 22:30 UTC; retain bootstrap/late-first-seen/revision distinctions and no-signal controls.
4. **Other source lines:** keep options NOTO/PHOTO, SEC Form 4/13F/13D-G, FINRA ATS/short interest and other candidates separate; do not infer that any one source represents informed capital.
5. No historical backfill was promoted. No return, alpha, OOS, bootstrap, LOO, or holdout test was run in this phase.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameters, holding period, capital, exposure, costs, holdout, or production changes were made.

## 6. Reproduction references

- [Phase 384 workflow](../.github/workflows/phase384_cftc_tff_prospective_capture.yml)
- [Phase 403 workflow](../.github/workflows/phase403_sec_form144_first_seen_capture.yml)
- [Phase 469 workflow](../.github/workflows/phase469_finra_regsho_daily_first_seen_capture.yml)
- [Phase 387 preregistration](PHASE387_CFTC_TFF_PROSPECTIVE_CROWDING_RISK_PREREGISTRATION_2026-11-14.md)
- [Phase 419 event-count feasibility](PHASE419_CFTC_TFF_PREREGISTERED_EVENT_COUNT_FEASIBILITY_2026-11-15.md)
- [Phase 471 summary](PHASE471_CFTC_SEC_LIVE_CAPTURE_DELIVERY_SUMMARY_2026-11-18.json)
