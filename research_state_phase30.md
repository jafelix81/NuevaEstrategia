# Phase 30 — MOM120 economic validation

Status: RUNNING after workflow push.

## Why this phase exists
Phase 29 found MOM120 as the strongest independent candidate. Before any promotion, this phase tests the signal in the same basic economic implementation as the frozen long-term-momentum baseline.

## Fixed protocol
- Same frozen Phase 11 universe.
- Daily close signal, next-session-open execution.
- F80: rebalance every 80 sessions.
- Top 20, equal-weight target, max 20%/name, gross cap 100%.
- PARTIAL50: move halfway toward target weights.
- Primary cost: 20 bps per side; 10 and 50 bps robustness checks.
- LTM baseline: average percentile ranks of R100/R120/R140/R160.
- Candidate: R120 cross-sectional momentum.
- Continuous chronological simulation; final OOS begins 2024-01-01.
- Paired block bootstrap and leave-one-out checks on the OOS daily return difference.

## Integrity notes
This is a comparative economic test, not a point-in-time universe audit. Both legs use the same frozen research universe, so relative attribution is meaningful, but historical tradability/survivorship remains a separate audit requirement.

Phase 29's raw research code declared a 10 bps cost parameter but did not subtract costs from the factor-ranking statistics. Therefore Phase 30 explicitly applies transaction costs during portfolio simulation rather than treating Phase 29 returns as implementation-ready.

## Decision gate
No production change is authorized by this phase alone. MOM120 can only be promoted if it shows robust OOS economics, cost survival, and incremental value versus the frozen baseline without relying on post-2023 tuning.
