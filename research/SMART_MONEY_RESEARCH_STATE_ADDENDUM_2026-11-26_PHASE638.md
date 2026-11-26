# Smart Money Research State Addendum — Phase 638 (2026-11-26)

## Completed

- Phase 638 merged to `main`: [PR #244](https://github.com/jafelix81/NuevaEstrategia/pull/244), commit `1c9f6bb0bcfadf6429c433c271f322e3cebd1309`.
- [Validation run 45805390010](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45805390010): Phase 403 offline suite **82/82 passed**; live capture skipped for PR.
- Phase 516 now separates expected `INITIAL_BASELINE_NO_LOWER_BOUND` rows from malformed intervals and fails closed if a research-eligible filing has an invalid interval.
- Live Form 144 ledger at run 45747356670: 815 filing headers / 5,443 detail rows; 807 bounded research-observation-eligible headers; 8 expected baseline headers quarantined; 0 malformed intervals; 0 eligible rows with invalid intervals; 0 exact public-availability certifications; 0 signal-eligible headers.
- The eight baseline rows all have first-seen upper bound 2026-11-18T03:09:53Z, no prior-poll lower bound, and are explicitly research-ineligible.

## Source state

- SEC Form 4: latest natural run 45759597509 (05:08 UTC), successful. It predates Phase 626 merge PR #240 (06:40 UTC); a post-merge natural capture is still required.
- SEC Form 144: latest natural run 45747356670 (03:11 UTC), successful; no later scheduled run visible by the 10:53 UTC audit.
- SEC 13F: run 45751086501 failed before SEC requests because the secret was empty. PR #243 / Phase 635 merged at 08:49 UTC and the collector now falls back to the existing project contact. No post-merge natural poll is visible yet.
- SEC 13D/G: PR #37 remains Draft. Latest Phase 352 check 45788991215 passed 9/9; 43/44 parent documents retrieved; CUSIP continuity remains 31 matches, 5 mismatches, 6 parent CUSIPs missing, and 1 unresolved parent. No strict PIT or signal admission.
- FINRA Reg SHO: latest run 45754121648 received eight files but admitted zero because BCPC/TPC facility-grain duplicate conflicts remain unresolved.
- CFTC TFF: latest run 45753716471 had no new reports or revisions; 3,043 total rows, zero historically signal-eligible rows. Only eight prospective contract observations across two report dates were eligible for observation, not signals.
- Options: feasibility only; no quote request, vendor contact or purchase. Authorized budget USD 0.

## Operational schedule gap

At the 2026-11-26 10:53 UTC audit, the scheduled-run API returned 74 historical scheduled runs and no scheduled run after the latest Form 4 run at 05:08 UTC. The latest 40 overall runs were dominated by PR checks. No runs were queued or in progress.

Current schedules in the default-branch workflow files:
- Phase 614 SEC 13F: minute 41, weekdays.
- Phase 476 SEC Form 4: minute 17, weekdays.
- Phase 403 SEC Form 144: minute 47, hourly.

The available read API does not expose each workflow's administrative enabled/disabled state. Missing scheduled runs are confirmed; a disabled state is not inferred. Verify these three workflows in GitHub Actions and enable them if disabled. Do not manually dispatch a duplicate poll.

## Model protection

- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No new incremental alpha, OOS, bootstrap or LOO result.
- No universe, parameters, holding-period policy, exposure, costs, capital, production or holdout change.
- No options-data spend; budget USD 0.
