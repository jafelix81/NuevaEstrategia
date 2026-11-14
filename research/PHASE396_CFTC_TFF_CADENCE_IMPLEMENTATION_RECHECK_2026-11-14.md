# Phase 396 — CFTC TFF cadence implementation recheck and first scheduled-capture readiness

**Audit time:** 2026-11-14 10:21 UTC  
**Disposition:** TFF remains demonstrably weekly as of this check; the semiweekly COT announcement is a future plan, not yet an observed TFF dataset transition. The prospective capture is initialized but has not yet completed a scheduled run.

## 1. Official CFTC status

- CFTC Release 9316-26 (2026-10-27) announces a plan to move COT publication from once to twice weekly by year-end: Monday positions on Wednesday and Wednesday positions on Friday, both at 3:30 p.m. ET. It does not give a firm implementation date or identify the exact transition behavior of the TFF Futures Only Socrata resource.  
  Source: https://www.cftc.gov/PressRoom/PressReleases/9316-26
- The current official COT landing page still describes Tuesday position data and a generally Friday 3:30 p.m. ET release; its FAQ still says the report is currently released once a week. The same page displays current reports dated 2026-11-03, including TFF Futures Only.  
  Source: https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
- The official 2026 release calendar still lists the next publication on Monday 2026-11-16 (holiday-delayed), followed by November 20 and November 30. It states that federal holidays can delay publication.  
  Source: https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm
- The TFF Futures Only data-hub page reports Last Updated 2026-11-06. The current report date shown on the CFTC COT landing page is 2026-11-03. No second report date or semiweekly TFF cadence has been observed.  
  Source: https://publicreportinghub.cftc.gov/Commitments-of-Traders/TFF-Futures-Only/gpe5-46if

**Interpretation:** keep the CFTC press release as a transition watch item. Do not relabel TFF as semiweekly until the specific `gpe5-46if` dataset produces prospective Monday/Wednesday position-date evidence and the official schedule confirms the implementation.

## 2. GitHub workflow and capture-state audit

- Main contains the Phase 384 weekday schedule: `15 22 * * 1-5` UTC. It polls after the announced 3:30 p.m. ET release time in both daylight and standard time.
- The recent run `43525140200` was an **event=push** on `phase384-cftc-tff-mainline-activation`, not a scheduled poll. It created the non-eligible historical baseline.
- The committed `research/data/cftc_tff_prospective/state.json` currently records `last_capture_mode=branch_push_baseline`, `last_capture_utc=2026-11-13T23:03:38Z`, and latest report date `2026-11-03` for all four tracked contract codes.
- The data directory currently contains only `baseline_manifest.json`, `historical_backfill.csv`, and `state.json`; no prospective `events/` ledger exists yet. Historical rows remain explicitly ineligible.
- The first weekday scheduled poll after this audit is Monday 2026-11-16 at 22:15 UTC (5:15 p.m. ET), after the official 3:30 p.m. ET release. Because the poll is after the regular session, a report first seen then is usable no earlier than the next regular NYSE session. If the API is not updated at that poll, the later actual first-seen timestamp governs.
- The workflow is not considered to have produced a prospective observation until a run with `event=schedule` writes an immutable event file and updates the state. A successful push-baseline run is not a prospective capture.

## 3. Phase 395 workflow validation

- PR #72 is merged to main at commit `bf5be80246341b8384baa5aa8963ed508bab1643`.
- Run `43582784605` failed only because the test command was launched from the repository root, so the research module import path was missing.
- The workflow was corrected to run from `research/`; run `43582818511` passed all 16 tests. It was an offline-only regression and produced no artifact.
- As of 2026-11-14 10:21 UTC, the Actions API reports zero queued and zero in-progress runs. No capture or research workflow is currently running.

## 4. Frozen research policy

- Phase 387 remains weekly-only and unchanged. Do not stitch weekly and semiweekly observations, reinterpret 52 reports as a year after a cadence change, or use static archive rows to fill the prospective warm-up.
- The Phase 395 atomic-batch guard remains active: only the newest new report per contract in one capture response may be research-observation eligible; older same-batch catch-up rows, revisions and late arrivals remain ineligible.
- No feature history, forward outcome, alpha/OOS/bootstrap/LOO/holdout test or signal admission was produced in this audit.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, capital, exposure, parameters and production remain unchanged. No vendor contact or purchase.

## 5. Next gate

Inspect the first actual scheduled Phase 384 run after the 2026-11-16 release. Confirm (a) the TFF report date actually added, (b) its first-seen UTC timestamp, (c) the resulting eligible/ineligible event classification, and (d) the first usable NYSE session. Continue to treat the source as weekly unless TFF itself demonstrates the new cadence.
