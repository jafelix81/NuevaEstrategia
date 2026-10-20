# Smart Money Research State

## Phase 25C — FINRA Short Interest Corrected Incremental

Status: **KILLED_FOR_NOW / NO_PRODUCTION_CHANGE**

Phase 25B had an invalid walk-forward because all OOS dates used the same pre-first-OOS training snapshot set. Phase 25C corrected this by using all snapshots with `KnowledgeDate < SignalDate` independently for each OOS date.

Corrected OOS summary:

| Horizon | Mean LS | Median LS | Positive OOS dates |
|---|---:|---:|---:|
| H5 | +0.0765% | -0.6131% | 2/5 |
| H10 | -0.1191% | -0.2244% | 2/5 |
| H20 | -0.7187% | -1.1510% | 2/5 |

There was one OOS date without a valid forward return. The selected feature changed from `SI_LEVEL_Z12` at the first OOS date to `SI_PERSIST_HIGH6` thereafter. The residual correlations against LTM were unstable and did not establish robust incremental information.

Conclusion: do not tune or promote FINRA Short Interest into F80. Archive this hypothesis unless a future, independently motivated formulation materially changes the information set rather than merely changing parameters.

## Current frozen baseline

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No production change has been authorized.

## Next line: Phase 26A — FINRA OTC/ATS feasibility

Hypothesis: off-exchange/ATS participation, concentration, persistence and changes in participant share may contain incremental information about informed/institutional behavior beyond LTM/F80.

First perform a data-feasibility audit only. FINRA documentation states that `weeklySummaryHistoric` provides a rolling four years of weekly OTC (ATS and non-ATS) aggregate data and that historical data older than one year is static. Production access requires an API credential; mock data must never be treated as production evidence.

Promotion criteria: reproducible historical access, adequate universe coverage, identifiable publication/knowledge timing, and a stable identifier mapping. Only after those pass should predictive tests be designed.
