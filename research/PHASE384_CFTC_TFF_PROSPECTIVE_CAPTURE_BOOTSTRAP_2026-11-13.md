# Phase 384 — CFTC TFF prospective first-receipt capture bootstrap

**Date:** 2026-11-13  
**Status:** mainline activation completed through PR #60; weekday schedule is active on `main`; first scheduled observation is pending.  
**Scope:** establish a reproducible, append-only prospective availability clock. No return or alpha test.

## Why this phase follows Phase 383

The CFTC TFF Futures Only archive is broad and internally consistent for the selected index contracts, but its historical static archive Updated date is not formally defined as first publication. Phase 380 found five missing pages, one report-heading mismatch and two stale Updated dates in the 851 post-launch report-date population. Phase 383 isolated Russell E-mini code 239742 and admitted 480/482 pages as a conservative archive proxy, explicitly not certified strict PIT.

Historical data remain backfill / feature warm-up only. This phase does not retroactively certify them.

## Contract panel

- 13874A — CME E-mini S&P 500, post-first-contemporaneous-TFF-report date 2010-07-20.
- 209742 — CME Nasdaq-100 Mini, post-2010-07-20.
- 124603 — CBOT Dow Jones Industrial Average $5, post-2010-07-20.
- 239742 — CME Russell E-mini, only the post-2017-08-15 E-mini contract era. Do not splice the 2006–2008 Russell Mini era or combine ICE code 23977A.

The source is the CFTC TFF Futures Only dataset gpe5-46if. The five CFTC business-purpose categories are aggregate classifications, not trader identities, beneficial owners or verified informed investors.

## Prospective availability policy

1. The branch-push run creates a historical backfill baseline and marks every row signal_eligible=false.
2. Manual dispatch is diagnostic only and never advances the state.
3. Scheduled capture runs **weekdays at 22:15 UTC** (5:15 p.m. ET in standard time; 6:15 p.m. ET in daylight time), after the normal 3:30 p.m. ET CFTC release time. Weekday cadence is required to catch holiday-delayed Monday releases; a Friday-only cron would miss them until the following Friday. If a holiday/backlog delays publication, no new row is invented; the next scheduled run observes it later.
4. A new report-date/code key first observed by a scheduled run after the baseline receives first_seen_utc and may be eligible only from the first regular equity session after that receipt timestamp.
5. A late-arriving older report date is recorded as a late arrival and is never backdated.
6. A changed hash for an existing key is recorded as a revision event, never overwritten as though it had been known earlier.
7. Missing contract-weeks remain missing; no forward-fill and no zero substitution.

The first receipt is the pipeline's conservative knowledge clock, not a claim about the exact CFTC publication second. PR #60 merged the clean activation package to `main`; the scheduled workflow is now active there. The first scheduled observation remains pending.

## Feature warm-up fields

The baseline stores selected public aggregate position fields and derived normalized quantities:
- category net positions divided by open interest;
- spread positions divided by open interest, kept separate from directional net;
- Leveraged Money four-report change, only across continuous 6–8 day report intervals;
- rolling z-scores using only prior observations, requiring at least 26 prior weekly observations;
- Leveraged Money versus Asset Manager net-position divergence.

Open-interest reconciliation adds spread positions to both long and short sides. A row is rejected if category totals do not reconcile exactly to reported open interest. The baseline is not an alpha dataset because historical first-receipt dates are not certified.

## Prior COT diagnostic — do not duplicate

The legacy Phase 23C walk-forward used 12 pseudo-OOS dates, selected among eight features and directions at each date using training 5-session Spearman, and did not include transaction costs or an identical-exposure F80 comparison. Its reported mean strategy returns were:
- NASDAQ: +0.192% at 5 sessions, -0.460% at 20 sessions;
- S&P 500: -0.049% at 5 sessions, -3.058% at 20 sessions.

Hit rates were 66.7%/50.0% at 5 sessions and 50.0%/16.7% at 20 sessions for NASDAQ/S&P 500 respectively. This is a weak, selection-sensitive diagnostic, not evidence of incremental edge. The new work is a prospective timestamp/data-integrity bootstrap, not a repeat of that feature search.

## Acceptance gates

- API row counts reconcile before/retrieved/after by contract.
- Metadata rowsUpdatedAt is unchanged during each snapshot.
- Natural key (report_date, cftc_contract_market_code) is unique.
- Category position fields are complete and finite; open interest is positive.
- Long and short category totals, including spreads on both sides, reconcile exactly to open interest.
- Historical backfill rows are never marked signal-eligible.
- Manual runs, late arrivals and revisions are never signal-eligible.
- Only scheduled first-seen new report rows can be eligible, from the next regular session after receipt.
- No forward returns, alpha, OOS, bootstrap, LOO or holdout is used.

## Controls

No changes to F80_TOP20_PARTIAL50_BASELINE_C20, production, universe, capital, parameters or exposure. The legacy holdout remains consumed and unavailable. No vendor purchase/contact. No Smart Money signal is admitted by this phase.


## Hosted result — completed 2026-11-13

Run [43510629316](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43510629316) succeeded; artifact [14078601093](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43510629316/artifacts/14078601093).

- The first run failed only in three synthetic unit-test fixtures because the fixture incorrectly allocated 50% of open interest to each of five categories. The fixture was corrected to reconcile category totals; no source-data request ran in that failed attempt.
- Corrected run: 10/10 tests passed; API snapshot completed.
- 3,035 rows: 851 each for 13874A, 209742 and 124603; 482 for post-2017 Russell E-mini 239742.
- Before/retrieved/after counts matched for all four contracts; CFTC metadata remained stable; natural key was unique.
- Open-interest accounting reconciled exactly for all 3,035 rows, including spreads on both long and short sides.
- No contract had a report-date gap greater than eight days. All four series end at 2026-11-03.
- The historical baseline CSV (1,420,079 bytes), state hash map (3,035 keys) and manifest were committed append-only to the branch. Every historical row remains signal_eligible=false.
- No forward returns, alpha, OOS, bootstrap, LOO or holdout test was run.

The official CFTC schedule lists the report for positions as of 2026-11-10 for release on **2026-11-16 at 3:30 p.m. ET**, delayed by Veterans Day. The Phase 384 baseline ends on 2026-11-03 and predates that release. PR #60 merged the clean activation package to `main` in commit `e88e553afc235916e37e9236e1890b714163c229`; the first scheduled capture is pending and will record the actual pipeline first-receipt time. See the [CFTC release schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm).


## Schedule robustness correction — 2026-11-13

The official CFTC 2026 release schedule lists the report for positions as of 2026-11-10 on **Monday 2026-11-16 at 3:30 p.m. ET**, delayed by Veterans Day. The initial Friday-only cron (`15 22 * * 5`) would delay first observation until 2026-11-20, when the report for 2026-11-17 may also be available. Because the fetch is ordered by report date and the baseline ends at 2026-11-03, both rows would still be classified as first-seen new reports in that run; they would not automatically become late arrivals. However, both would receive the same 2026-11-20 first-seen timestamp, forfeiting the earlier conservative availability that a Monday capture could establish. The weekday cadence reduces this avoidable latency and preserves separate first-receipt dates.

Corrected the workflow cron to `15 22 * * 1-5`, running at 22:15 UTC each weekday. This is after the CFTC's 3:30 p.m. ET release in both U.S. standard and daylight time and captures a Monday holiday-delayed report on the same business day. No report is inferred if the source is not yet updated; the next weekday poll observes it. The existing first-seen, late-arrival and revision rules are unchanged.

Official schedule: [CFTC 2026 Release Schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm). PR #60 subsequently merged the clean activation package to `main`; the weekday cron is active and awaits its first scheduled run. The branch-push bootstrap is protected against overwrite; the cron correction does not reset it.


## Mainline activation correction — 2026-11-13

A repository topology check found that original PR #59 targets `phase383-cftc-russell-eminifutures-pit-panel-audit`, not the default branch `main`. Merging PR #59 alone would therefore **not** activate the scheduled workflow: GitHub scheduled workflows are evaluated from the default branch. To avoid pulling the entire unfinished Phase 377–383 dependency chain into main, a clean activation branch based directly on `main` was prepared with only this Phase 384 workflow, its capture script, tests and report. The push bootstrap is branch-filtered to that activation branch and the initial push is filtered to the workflow file so the workflow starts only after all required files exist. Its successful bootstrap will append the baseline/state files to the branch; merging the clean activation PR to `main` is then the human-controlled activation step. Original PR #59 remains a research-chain draft and is not by itself sufficient to activate the cron. No source rows are made signal-eligible by this packaging correction; no return/alpha test or production change is authorized.


## Eligibility semantics and announced CFTC cadence change — 2026-11-13

The event ledger distinguishes **research-observation eligibility** from a trading signal. A scheduled first-seen new report may be marked `research_observation_eligible=true` only after the observed receipt timestamp; every captured event keeps `signal_eligible=false` and `trade_signal_generated=false`. The first regular equity session after receipt is only the earliest session at which the observation may enter a future research feature set. This workflow does not generate trades or authorize a signal.

The CFTC announced on 2026-10-27 that it plans to increase COT publication frequency from once to twice weekly by the end of 2026: Monday-position data would be released Wednesday and Wednesday-position data Friday, both at 3:30 p.m. ET ([CFTC press release 9316-26](https://www.cftc.gov/PressRoom/PressReleases/9316-26)). No effective date was specified in the announcement, and the 2026-11-13 public schedule still shows the weekly regime. The weekday capture schedule can observe either cadence. Static-backfill cadence labels remain diagnostic only; they are not attached to prospective event payloads and cannot supply Phase 387 feature history. The prospective study must calculate cadence from prospectively first-seen report dates only. Four reports must never be relabeled as four weeks. Any semiweekly features require a separately pre-registered horizon and validation design before use.

This cadence guard is a data-integrity control, not an alpha feature. No trade signal is generated and F80 remains frozen.

## Mainline activation completed — 2026-11-14

PR #60 merged the clean Phase 384 activation package directly to `main` in commit `e88e553afc235916e37e9236e1890b714163c229`. The weekday schedule `15 22 * * 1-5` is active on the default branch. The hosted bootstrap run [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200) passed 11/11 tests, reread the 3,035-row baseline and returned `BASELINE_ALREADY_EXISTS_NO_OVERWRITE`; it did not rewrite historical state. No scheduled capture has yet verified a new report's first receipt. The next report of interest is the 2026-11-10 position report scheduled for 2026-11-16 at 3:30 p.m. ET.

## Phase 388 — raw-only prospective event payload guard — 2026-11-14

A post-merge code review found that scheduled events still carried derived features and cadence labels computed from the unverified static CFTC archive. Although these fields were not marked trade-eligible, their presence created a contamination path against Phase 387's prospective-only feature-history rule. PR #64 merged the correction to `main` in commit `9a57acb005f6496f707bfc6faf685925553930d4`. Prospective events now retain only raw canonical source rows, first-receipt metadata, hashes, event classification and eligibility flags. Archive-derived feature values and cadence labels are not attached to events. Hosted regression [43539923574](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43539923574) passed 13/13 tests. Downstream Phase 387 features must be recomputed solely from prospectively first-seen eligible events.

No new CFTC report has been captured, no alpha/return test has run, and no signal or production change is authorized.
