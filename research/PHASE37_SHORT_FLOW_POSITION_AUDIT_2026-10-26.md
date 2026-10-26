# Phase 37 — FINRA Short-Flow × Short-Interest Audit

Date: 2026-10-26

## Decision

**KILL for the frozen-335 security-selection research line in the current public-data form.**

The repository already contained Phase 31, a dedicated FINRA short-flow × short-interest divergence experiment. I audited its latest successful artifact before commissioning another test. The artifact is useful for feasibility, but it fails the required identical-universe coverage gate and therefore cannot support a valid incremental alpha claim versus `F80_TOP20_PARTIAL50_BASELINE_C20`.

## What the live Phase 31 artifact actually contains

Latest successful Phase 31 run: `40164323397`, head `44c2fda9ea03fcfbce662e4dd26ca876ac03961b`.
Artifact: `phase31-finra-flow-si-divergence` (`12588045711`).

The run covered an OOS diagnostic period of 2024-01-02 through 2026-10-23 at 20-business-day signal cadence. Its PIT rule for flow was through signal-date close, while short interest used `KnowledgeDate = settlement + 7 business days`.

The artifact successfully downloaded/processed:

- FINRA short-sale flow: 362,727 rows, **334 unique tickers**, 2022-06-01 through 2026-10-23.
- FINRA consolidated short interest: 9,420 rows, only **98 unique tickers**, 2022-06-15 through 2026-09-30.
- Per-settlement-date frozen-universe coverage in the short-interest audit was generally **84–96 names**, with several failed settlement requests.

Therefore the joint flow+position panel is not remotely equivalent to the frozen 335-name universe. It is roughly a 29% universe sample at its best and typically lower. The downstream Phase 31 signal results are consequently a **diagnostic subset result**, not an apples-to-apples strategy test.

## Important interpretation of the Phase 31 return statistics

The latest artifact reported some persistent-looking cross-sectional relationships, e.g. `JOINT_RISE` had positive residual-LTM IC at 5 days and negative residual-LTM IC at 10/20 days, while `JOINT_FALL` showed the opposite pattern. Those directions are economically unstable across horizons and the bootstrap intervals on the top-decile-minus-bottom-decile spreads include zero.

More importantly, because the joint sample is restricted to approximately 98 names, these numbers **must not be interpreted as evidence of incremental alpha for the frozen strategy universe**. No portfolio promotion is justified.

The mirror-image relationship between `JOINT_RISE` and `JOINT_FALL` is also partly mechanical because the factors are sign reversals of the same underlying product (`FLOW_Z20 × SI_CHG_Z6`). It is not independent confirmation.

## PIT/data-quality caveat

The Phase 31 code still uses the conservative `settlement + 7 business days` short-interest knowledge-date proxy rather than the actual publication timestamp. That is acceptable for a conservative diagnostic, but it is not sufficient to establish exact historical tradability.

The short-interest audit also showed several JSON/API failures, including 2024-01-15, 2024-03-29 and 2026-10-15; the last requested 2026-10-30 settlement is naturally beyond the current date and must not enter any OOS panel.

## Why this is a kill rather than another rerun

A new Phase 37 run using the same consolidated short-interest source would not solve the fundamental problem. The limiting issue is **security coverage**, not statistical power from the chosen test. Re-running with different transformations would manufacture apparent precision on a non-representative subset.

The candidate may be revisited only if a historical FINRA short-interest source can demonstrate materially broader coverage of the frozen universe, or if the research question is explicitly changed to a smaller, pre-specified eligible universe with its own independent baseline. Neither is permitted for the frozen production strategy at present.

## Research state after audit

1. **Options Open-Close / OI / IV / skew:** strongest information-density candidate; commercial historical access remains required.
2. **FINRA security-level ATS/off-exchange:** strongest public stock-level candidate; historical archive/PIT coverage remains unresolved.
3. **FINRA short-flow + consolidated short-interest:** **killed for frozen-335 stock selection due inadequate joint short-interest coverage.** The prior Phase 31 subset result is retained as diagnostic evidence only.
4. **SEC 13D/13G:** secondary; historical universe mapping remains incomplete.
5. **FINRA `blocksSummary`:** killed for stock selection because it has no security/ticker dimension.

## Frozen baseline

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No short-flow or short-interest feature is admitted to the strategy.

## Re-entry criteria

A future short-position experiment requires, at minimum:

- reproducible historical PIT timestamps;
- a pre-specified coverage threshold materially closer to the frozen universe (not a ~98/335 subset);
- identifier continuity and delisting handling;
- documented correction/revision treatment;
- an independent chronological OOS panel;
- identical exposure and transaction-cost accounting versus F80/LTM;
- bootstrap and leave-one-date-out sensitivity;
- explicit controls for prior returns/return-chasing.
