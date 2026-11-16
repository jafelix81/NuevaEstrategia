# Smart Money Research state addendum — 2026-11-16, Phase 427

## Operational preflight

- Main HEAD at preflight: e05244394aa4191b30df15c531e1ea5733bf59ee; default branch main.
- Latest 100 Actions runs: 7,665 total runs reported; 61 success, 38 failure, 1 cancelled; all 100 completed, with no queued/in-progress/waiting/requested run visible.
- The latest Phase 426 sequence had five attempts: two failures and three successes. The first failure was a missing frozen-engine module on the branch; the second was a Python true/True serialization typo. Both were corrected. Final run [43789923762](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43789923762) passed its single research job; artifact [14191029663](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43789923762/artifacts/14191029663) contains 47 files (16,522,350-byte ZIP; SHA-256 2ae79509bb090c8e024f97b074fe1351b8a8747541091150cc991493a2d4450b).
- Inspected 262 branches (100 + 100 + 62), 56 open PRs, and 64 workflow files. Phase 426 PR #90 merged at 2026-11-16 02:08:03 UTC. No active Actions run was present; no workflow was dispatched or rerun during this audit.

## Phase 426/427 decision

- Phase 426's exact-engine, matched-gross C20 comparison remains a promising historical diagnostic, not a promotion. It uses 335 current tickers, Yahoo historical prices, 2024-01-02–2026-11-13 (721 paired sessions), and only ten OOS cycle fragments; the universe is not point-in-time/survivorship-free and 2024+ was already examined in Phases 29/30.
- Phase 427 re-audited the artifact's paired returns. Overall MOM120-minus-LTM mean excess was 5.1686 bps/day and relative wealth multiple 1.4416x, but 91.81% of cumulative log-relative gain accrued in 2024–2025. 2026 through Nov 13 was only 1.55 bps/day, HAC(80) t=0.75, 95% CI −2.52 to +5.63 bps. The latest 75-session cycle fragment was negative. Across all ten fragments, 8/10 were positive; one-sided exact sign-test p=0.0547. Do not infer persistence from the eight complete cycles alone.
- Phase 427 report: research/PHASE427_MOM120_TEMPORAL_STABILITY_AUDIT_2026-11-16.md; reproducible script: research/phase427_mom120_temporal_stability_audit.py. The script consumes the Phase 426 artifact CSV only; no new prices, parameters or holdout were used.
- Decision: PROMISING_BUT_TEMPORALLY_CONCENTRATED_NO_PROMOTION. Prospective shadow and a pre-registered R120-residual/conditional test remain future work. MOM120 is a momentum reweighting already inside LTM, not a Smart Money source.

## Other source gates remain unchanged

- SEC Form 144 latest scheduled run visible: [43773157505](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43773157505), successful with 55 feed rows and zero new accessions/events/eligible observations. No later scheduled run appears in the latest 100; hourly first-seen cadence remains unproven. No manual dispatch or cron change.
- CFTC TFF latest run remains bootstrap [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200): 3,035 historical warm-up rows, zero signal-eligible rows. First expected prospective scheduled capture remains Monday 2026-11-16 22:15 UTC after the 20:30 UTC release; it had not yet occurred at this audit.
- SEC 13D/G remains blocked on repository-owner secret SEC_USER_AGENT with a monitored contact. FINRA Phase 20C remains at 328/329 valid price histories. Options and commercial flow sources remain conditional. No Smart Money source/signal admitted.

## Controls

F80_TOP20_PARTIAL50_BASELINE_C20, universe, parameters, holdout, capital, exposure policy and production remain frozen. No data purchased, no provider contacted, no credentials changed, no holdout use, no production workflow dispatched.


## Merge verification

- Phase 427 PR [#91](https://github.com/jafelix81/NuevaEstrategia/pull/91) merged successfully by squash at 2026-11-16 02:18:32 UTC.
- Main commit: `26e500f2c4c006bfde27d0fd3603c37426577260`.
- Post-merge Actions check: latest 100 runs remain 61 success, 38 failure, 1 cancelled; zero active/queued runs. No new workflow was triggered by the documentation-only merge.
- The three Phase 427 files are present on main. No changes to trading code, workflow definitions, production, or frozen baseline.
