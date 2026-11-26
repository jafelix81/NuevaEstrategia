# Phase 638 — SEC Form 144 first-seen interval classification

**Audit cutoff:** 2026-11-26 10:46 UTC  
**Base:** `main` at `aefa343521bca76ae6d201fd608180230cb2c44d`  
**Branch:** `phase638-form144-initial-baseline-interval-classification-20261126`  
**Disposition:** clarify expected bootstrap quarantine versus genuinely malformed point-in-time intervals. No signal, return test or strategy change.

## 1. Evidence reviewed

Natural Form 144 capture [run 45747356670](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45747356670) completed successfully and produced [artifact 15083886905](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45747356670/artifacts/15083886905).

- 82 new canonical accessions from 84 feed entries; two cross-feed overlaps.
- 82/82 new XML submissions resolved; no parser errors or source-hash mismatches.
- Structured ledger: 815 filing headers and 5,443 detail rows.
- 807 headers have bounded first-seen intervals and are research-observation eligible.
- Eight headers are explicitly `INITIAL_BASELINE_NO_LOWER_BOUND`; all eight have a first-seen upper bound, no prior-poll lower bound, and `research_observation_eligible=false`.
- Zero filing headers have certified exact public availability; zero are signal eligible.

The eight baseline rows all belong to poll `44228413864`, first seen at `2026-11-18T03:09:53Z`, and have no EDGAR acceptance timestamp in the structured ledger. They are expected bootstrap observations, not malformed intervals. They remain excluded from research-observation eligibility.

## 2. Audit semantic correction

The previous Phase 516 summary reported `malformed_or_missing_first_seen_intervals=8`. Inspection of all 815 filing-header rows showed that the eight cases were the expected initial baseline above. The old label conflated an intentional no-lower-bound bootstrap state with genuinely malformed data.

This branch changes the Phase 516 audit to:

- Count and list `INITIAL_BASELINE_NO_LOWER_BOUND` rows separately.
- Count as malformed only intervals that fail the declared status/bounds contract.
- Explicitly count and list any research-observation-eligible filing with an invalid interval.
- Keep expected baseline rows quarantined and preserve zero signal eligibility.
- Require a clean interval audit for the descriptive quality-pass disposition.

Two regression tests cover (a) the expected baseline quarantine and (b) rejection of a baseline row incorrectly marked research eligible. Existing tests continue to cover timezone-aware bounds and the no-signal rule.

## 3. Implementation and validation

PR [#244](https://github.com/jafelix81/NuevaEstrategia/pull/244) merged to `main` at commit `1c9f6bb0bcfadf6429c433c271f322e3cebd1309`.

- [PR workflow run 45805390010](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45805390010) succeeded.
- Phase 403 offline regression: **82/82 tests passed**.
- Live-capture job was skipped for the pull-request event.
- Re-running Phase 516 on the committed 815-header / 5,443-row ledger produced: 8 expected initial-baseline rows; 0 malformed intervals; 0 research-eligible rows with invalid intervals; 0 signal-eligible headers.
- The descriptive quality-pass disposition was preserved.

## 4. Current Form 144 interpretation

The Phase 549 artifact remains descriptive:

- 295/815 accessions have a formal plan-adoption date.
- Remarks polarity: 23 positive explicit, 4 negative explicit, 3 ambiguous, 785 no mention.
- Four Fermi sell-to-cover notices total 2,253,270 proposed units; they explicitly describe tax-withholding transactions, not discretionary bearish trades.
- A Form 144 is a proposed-sale notice, not confirmation of execution.

No return series, event study, alpha, chronological OOS, bootstrap, LOO or holdout test was run. No filing is admitted as a trading signal.

## 5. Actions and cross-source preflight

At the cutoff, the Actions API showed zero in-progress and zero queued runs. The latest 40 runs were dominated by PR checks. The latest relevant PR check, [run 45788991215](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45788991215), passed the Phase 352 crosswalk (9/9 tests) and uploaded artifact [15101941929](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45788991215/artifacts/15101941929); it did not repeat live SEC retrieval.

The latest scheduled-run inventory contained 74 runs. No natural scheduled run was visible after:
- Form 4: [45759597509](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45759597509), 2026-11-26 05:08 UTC. This predates the Phase 626 merge (PR #240, merged 06:40 UTC).
- Form 144: [45747356670](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45747356670), 2026-11-26 03:11 UTC.
- SEC 13F: [45751086501](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45751086501), 2026-11-26 03:46 UTC. This predates the Phase 635 fallback merge (PR #243, merged 08:49 UTC); the old run failed before any SEC request because the secret was empty.

The current workflow definitions retain schedules for Phase 476 (minute 17 weekdays), Phase 403 (minute 47 hourly), and Phase 614 (minute 41 weekdays). The available read surface does not expose each workflow's administrative enabled/disabled state. Therefore the absence of runs is confirmed, but a disabled state is not inferred. A post-merge natural capture is still required for Phase 626 and Phase 635.

Other source gates remain unchanged: FINRA Reg SHO is quarantined for BCPC/TPC row-grain conflicts; CFTC TFF has 3,035 unverified archive rows plus only eight prospective contract observations across two report dates; SEC 13D/G has 43/44 parent documents retrieved with CUSIP continuity unresolved in five cases and missing in six.

## 6. Strategy controls

- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No universe, parameters, holding-period policy, exposure, costs, capital, production or holdout changes.
- No options-data purchase, vendor contact or quote request; authorized budget remains USD 0.
