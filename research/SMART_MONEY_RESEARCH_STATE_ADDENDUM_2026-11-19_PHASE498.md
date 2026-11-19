# Smart Money Research — state addendum, Phase 498 (2026-11-19)

## Completed
- Audited the current mainline SEC Form 4/4-A append-only event and feed-observation ledgers without making new SEC requests.
- Main baseline: `95c304d5b07653cbe817912f8b713b30ad8fdbbf`.
- Three successful scheduled polls are present in the current feed-observation ledger: runs 44380395679, 44440313382 and 44505739718.
- The collector declares `17 * * * 1-5`, but the observed prior-end to next-start receipt gaps were 6.4675 h and 8.5400 h. Hourly delivery is not demonstrated; this is evidence of delayed/missed schedule slots, not proof that the workflow is disabled.
- The event ledger contains 690 rows: 35 initial-baseline rows without a lower bound and 655 bounded metadata-only rows (637 from run 44440313382; 18 from run 44505739718).
- All 655 bounded event intervals are 6.4675–8.5400 h wide; median 6.4700 h; 0 are at most 2 h. “Bounded” is not equivalent to exact or high-frequency publication timing.
- Under the conservative first-regular-session-after-collector-receipt-upper-bound rule, both bounded cohorts first become usable on 2026-11-19 for daily timing. This does not authorize intraday use or override identity/transaction/universe gates.
- Research-observation eligible = 0; signal eligible = 0. No raw payloads or transaction rows were added.

## Decision
- SEC Form 4 remains a conditional daily disclosure-event source, not an intraday signal source on this observed cadence.
- Do not infer hourly capture from the cron declaration. Use actual receipt bounds; do not backdate to feed `updated` or acceptance timestamps.
- Phase 497 remains a one-filing-date transaction-context census, not a historical return sample.
- No event study, forward-return test, OOS, bootstrap, LOO or holdout test was run.

## Other active gates
- FINRA Phase 495 facility-grain parser still needs its first post-fix live capture; the latest live run 44453548570 used the pre-fix main SHA and rejected all eight files.
- CFTC TFF run 44453066854 succeeded but found no new reports or revisions; 3,039 historical rows remain and zero historical rows are signal-eligible.
- SEC 13D/G parent retrieval remains blocked by the required repository Actions secret `SEC_USER_AGENT` containing a project identifier and monitored contact email. PR #37 remains draft; no SEC request should be retried before the secret is configured.
- Options remain conditional on historical PIT/vintage, coverage, independent validation and licensing.

## Frozen controls
`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameters, holding period, capital, exposure, costs, holdout or production changes. No new signal admitted.


## Integration completion
- PR [#154](https://github.com/jafelix81/NuevaEstrategia/pull/154) merged at 2026-11-19 11:22:52 UTC; squash merge / main HEAD: `880f8faeff03f1505ffead155babf74dd94c0bda`.
- Push CI [44514184045](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44514184045) and PR CI [44514246907](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44514246907) both passed 9/9 offline tests and recomputed the aggregate-only cadence audit. Artifact [14523893664](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44514184045/artifacts/14523893664), SHA-256 `1f6eb049aec749caf7e0a2c0267db1ee8c9e180e444dd270f90d5b5cf9371b67`.
- Post-cutoff operational check at 11:22 UTC did not yet show a schedule-triggered Phase 476 run for the 11:17 UTC slot. Treat it as delayed/not yet visible, not proof that the workflow is disabled. No duplicate poll was started.
- Actions total count at this check: 7888; no active or queued run in the latest 30 records.
