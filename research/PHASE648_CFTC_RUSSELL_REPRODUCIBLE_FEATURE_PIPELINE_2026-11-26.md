# Phase 648 — CFTC Russell reproducible fixed-reference feature pipeline

**Audit cutoff:** 2026-11-26 19:23 UTC  
**Base main HEAD:** `fd3c3e6c190e329a5f2ad69941edbe83bb2ca1a8`  
**Branch:** `phase648-cftc-russell-reproducible-feature-pipeline`  
**Disposition:** completed on PR #246; offline CI passed 10/10 tests and produced the reproducible JSON artifact. This phase does not inspect price outcomes, fit a predictive model, admit a signal, or change F80.

## 1. Required preflight

Before creating this phase, inspected the latest 100 Actions runs, their current statuses, the latest scheduled runs, open PRs, branch heads, the research tree, Phase 646/647 reports, CFTC capture code, tests, frozen input manifest, and both prospective event payloads.

- Repository Actions inventory: 8,350 total runs.
- Latest 100 runs inspected: zero queued, waiting, requested, pending, or in-progress.
- Latest scheduled SEC captures: Form 4 [45848689364](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45848689364), 13F [45839454376](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45839454376), and Form 144 [45827105431](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45827105431). All jobs completed successfully and all listed artifacts are unexpired.
- Latest scheduled CFTC capture: [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471); no new report or revision, no state change. Its job and artifact were inspected.
- Latest scheduled FINRA Reg SHO capture: [45754121648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648); eight files were rejected by the existing BCPC/TPC row-grain/facility-overlap gate. No rows admitted.
- Latest visible natural SEC run times are Form 4 15:23:55Z, 13F 14:29:01Z and Form 144 13:13:48Z on 2026-11-26. These are the latest visible runs at the cutoff, not evidence that any workflow is disabled. No manual dispatch, rerun, or duplicate poll was made.
- Main branch head was `fd3c3e6c190e329a5f2ad69941edbe83bb2ca1a8`. Phase 646 and 647 are present in main. No existing Phase 648 branch or PR was present.

## 2. Why this phase exists

Phase 647 validated the fixed-reference calculation in a one-off audit. Phase 648 turns that calculation into a small reproducible pipeline and regression suite so future prospective events can be processed without reinterpreting the historical archive or changing the preregistered feature.

The design remains Russell-only and separate from Phase 387 ES/NQ. The historical archive is used only as a frozen reference distribution, not as historical PIT signals, training labels, or a return backtest.

## 3. Frozen inputs and integrity checks

The pipeline verifies Git blob identities before reading either frozen input:

| Input | Required Git blob SHA |
|---|---|
| `research/data/cftc_tff_prospective/historical_backfill.csv` | `4711abbaeeb6107d1cb8f50a7c2e3627373b6d29` |
| `research/data/cftc_tff_prospective/baseline_manifest.json` | `9e58849093f2144ce8cfbf1d3e5efc626a1aa250` |

It also enforces:
- 3,035 total historical rows in the frozen archive.
- Exactly 482 Russell E-mini rows (contract `239742`).
- Exactly two preregistered exceptions: 2018-09-25 and 2019-12-24.
- Exactly 480 finite reference values after exclusions.
- No duplicate Russell report dates.
- Historical rows retain `UNVERIFIED_ARCHIVE_PROXY` and `signal_eligible=false`.
- The manifest remains explicitly `NOT_CERTIFIED; feature warm-up only`.

The conservative project-knowledge bound remains 2026-11-14 00:44:59Z, the mainline persistence time of the immutable reference snapshot. The pipeline rejects any prospective event received at or before that bound.

## 4. Prospective event validation

For Russell events only, the pipeline:
- Accepts only scheduled, first-seen `new_report` observations marked research-observation eligible.
- Rejects unexpected signal eligibility, trade-signal generation, or inclusion of archive-derived features.
- Requires a timezone-aware UTC first-receipt timestamp.
- Reconciles event report date and contract code to the raw source row.
- Recomputes the raw CFTC row digest using the Phase 384 canonicalization.
- Re-runs open-interest accounting checks.
- Recomputes Leveraged Money net/OI from raw long and short positions.
- Rejects duplicate report dates and non-monotonic report/first-seen chronology.

No archive-derived feature values are copied into the prospective event path.

## 5. Reproduced feature

For each prospective Russell event:

`LM_NET_OI = (Leveraged Money long - Leveraged Money short) / open_interest_all`

`P_t = (count(reference < current) + 0.5 * count(reference = current)) / 480`

The fixed state remains `HIGH_LM_CROWDING = 1[P_t >= 0.80]`. No threshold, category, contract, or horizon search is added.

The regression suite requires the two Phase 647 observations to reproduce:
- Report 2026-11-10: percentile 40.625%; not high.
- Report 2026-11-17: percentile 45.4167%; not high.

Later first-seen Russell events are included automatically if they pass all gates. No return or price data are accessed.

## 6. Files added on the Phase 648 branch

- `research/phase648_cftc_russell_feature_pipeline.py`: standard-library pipeline plus reuse of Phase 384's canonical CFTC row hash/OI validation.
- `research/test_phase648_cftc_russell_feature_pipeline.py`: regression tests for frozen Git blob identity, archive coverage, mid-rank ties, Phase 647 reproduction, temporal eligibility, timezone strictness, raw-row hash integrity, duplicate events, and no-signal/no-outcome controls.
- `.github/workflows/phase648_cftc_russell_feature_pipeline.yml`: offline PR validation and a JSON feature artifact; it makes no network requests to CFTC and has no write permission.
- This report and the state addendum.

The workflow is intentionally PR-triggered for these paths and can also be dispatched manually. It installs only the existing Phase 384 import dependency, runs offline tests, and emits a compact reproducible JSON artifact. Final validation: [Run 45883790689](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45883790689), job 140129369138, success; 10/10 tests passed. Artifact [15148398103](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45883790689/artifacts/15148398103) contains the reproduced feature summary. An initial run exposed a JSON serialization error for Decimal values after all tests passed; the value is now converted explicitly and the subsequent full run passed.

## 7. Acceptance and limitations

**Acceptance:** PR #246 is open and mergeable; the final Phase 648 offline workflow completed successfully. The first run's serialization defect was fixed before the passing run. Merge is a code/documentation integration only and does not promote a signal.

Even after CI passes, this is only reproducible feature construction. The sample still contains two prospective report-date observations. The Phase 646 training gate (52 matured observations with at least 20 high and 40 non-high) and evaluation gate (150 observations with at least 30 high and 100 non-high) remain unmet.

The adjusted Russell proxy OHLC and VIX source has not been frozen. No forward price outcomes have been accessed. The study remains blocked before outcome analysis until a permitted, reproducible source and adjustment convention are frozen.

## Frozen strategy controls

- Signals admitted: **0**.
- Incremental alpha versus LTM/F80: **none demonstrated**.
- New OOS / bootstrap / LOO: **0**.
- Price outcomes accessed: **no**.
- Holdout: sealed.
- `F80_TOP20_PARTIAL50_BASELINE_C20`: unchanged and frozen.
- No universe, parameter, capital, exposure, cost, holding-period, or production changes.
- Options-data budget: **USD 0**.
