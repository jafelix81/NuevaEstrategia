# Phase 578 — FINRA ATS revision-clock semantics and stable-row PIT reclassification

**Audit cutoff:** 2026-11-23 16:06 UTC  
**Main HEAD at preflight:** `917f683f0711875dce2a72579d2b6a367e9dc059`  
**Disposition:** **FINRA weekly ATS remains the strongest conditional public off-exchange stock-level candidate. The official field definitions now resolve that `lastReportedDate` is a firm-submission/update date, not a public revision-release timestamp. Admit only revision-stable rows to the initial-publication clock; quarantine revised rows. No return/alpha test or signal admission.**

## 1. Repository and Actions preflight

- Actions API: **8,076 total runs**; latest 100 = **96 success / 4 failure**; zero queued or in progress.
- Branch census: **374** (100 + 100 + 100 + 74); open PRs: **72**.
- Latest run [45204833774](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45204833774), Phase 577 post-merge main run, completed successfully. Its single `offline-contract` job passed **16/16** synthetic tests. No artifacts were expected for this offline-only run.
- Phase 577 PR [#207](https://github.com/jafelix81/NuevaEstrategia/pull/207) is merged. Main currently points to `917f683f0711875dce2a72579d2b6a367e9dc059`.
- Latest natural SEC runs remain Form 144 [45137579123](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45137579123) at 08:18:38 UTC and Form 4 [45133809578](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45133809578) at 07:48:40 UTC. Form 144's three artifacts and Form 4's one artifact remain unexpired; the Phase 565 post-capture artifact digest remains `7d8d62289b21ce28de22ebf408fd461534d1cea0b95034f00379b0e51e741c58`.
- At 16:06 UTC, absent schedule slots are Form 144 `:47` from 08:47 through 15:47 UTC (8 slots) and weekday Form 4 `:17` from 08:17 through 15:17 UTC (8 slots); 16:17 had not yet arrived. This is a delivery gap, not proof of administrative disablement. Existing Issue [#194](https://github.com/jafelix81/NuevaEstrategia/issues/194) comment 7104521256 was updated in place. No manual dispatch, rerun, cron change, cancellation or duplicate poll was performed.

## 2. New official semantic clarification

FINRA's official **OTC Transparency (ATS and Non-ATS) Reporting API Specifications, version 0.4, dated 2019-01-16**, defines the weekly fields as follows:

- `initialPublishedDate`: the first Monday or next business day after the reporting delay — two weeks for NMS Tier 1 and four weeks for NMS Tier 2 / OTC.
- `lastReportedDate`: the last time a firm sent an update to any underlying data contributing to the aggregate count.
- `lastUpdateDate`: the later of `lastReportedDate` and `initialPublishedDate`.
- Weekly files and updates are available no earlier than 06:00 ET on business days; the specification does not provide a historical, per-revision public-release timestamp or a maximum delay from firm update to public release.

Official source: https://www.finra.org/sites/default/files/OTC-Transparency-Data-File-Download-API-v04.pdf (data dictionary pp. 3–4; file availability p. 10).

**PIT consequence:** `lastReportedDate` is not a FINRA public-publication timestamp. A revised final snapshot cannot be backdated to `lastReportedDate`, nor can `lastUpdateDate` be treated as a verified public-availability time. The original publication clock applies only to observations that were not subsequently revised.

## 3. Reconcile the existing historical evidence without mixing grains

### Phase 385 — date-level publication clock

The hosted Phase 385 census validated all **209/209** consecutive T1 weekly partitions from 2021-11-15 through 2025-11-10:

- 1,045 unique partition pairs.
- 10,917,933 full T1 records paginated.
- 438,822 `ATS_W_SMBL` aggregate rows.
- 2,292 pages; 209/209 Record-Total reconciliations.
- One valid `initialPublishedDate` per partition; all 209 publication dates matched the documented 21/22-calendar-day rule.
- First eligible daily session is the first NYSE regular session **strictly after** the actual `initialPublishedDate`; never use the same-day close/open.
- 5,994 aggregate rows had `lastUpdateDate` later than `initialPublishedDate`.

This validates a date-level clock for initial publication, not intraday receipt and not the public release time of later revisions. Report: [Phase 385](research/PHASE385_FINRA_T1_PUBLICATION_CLOCK_RESULT_2026-11-14.md). An anonymized date-only artifact is [14096455337](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43536354917/artifacts/14096455337).

### Phase 375 — revision stability at symbol-week grain

The separate Phase 375 bridge reports **432,804 of 438,798 symbol-week groups** as revision-stable/concentration-ready: **98.633996%** of symbol-week groups and **96.943175%** of mapped aggregate share volume.

These are symbol-week group statistics, not the 438,822 row count or the 5,994 revised aggregate-row count from Phase 385. Do not conflate the grains or infer identical denominators.

The Phase 375 full audit and implementation are contained in the Draft [PR #61](https://github.com/jafelix81/NuevaEstrategia/pull/61) branch; its source branch is 189 commits ahead / 455 behind main and must not be merged as-is. The mainline Phase 385 publication-clock result is [here](research/PHASE385_FINRA_T1_PUBLICATION_CLOCK_RESULT_2026-11-14.md).

### Phase 535 / broader recent API panel

Phase 535 reconciled Phase 100's 10 sampled partitions / 968,139 rows and found `initialPublishedDate` on 100% of sampled symbol-aggregate rows; 1,882 of 108,444 sampled rows had a later `lastUpdateDate`. Phase 518 extended the combined recent panel to 259 consecutive weeks, 2021-11-15 through 2026-10-26. The five-week overlap showed 94.63%–99.10% overlap with the legacy 335-name list, but that curated list is not a representative broad-market denominator.

The separate ATS archive that might extend history to 2014 returned HTTP 530 from GitHub Actions; no certification or terms control was submitted. The Query API's `blocksSummary` has no ticker dimension and remains killed for stock selection.

Report: [Phase 535](research/PHASE535_FINRA_ATS_ARCHIVE_ACCESS_AND_PIT_RECONCILIATION_2026-11-20.md).

## 4. Revised PIT disposition

For any future reconstruction:

1. **Stable row/group:** require `lastReportedDate <= initialPublishedDate` (equivalently, no later `lastUpdateDate` under the documented field definition). Use the verified `initialPublishedDate`, then the first NYSE regular session strictly after it.
2. **Revised row/group:** if `lastReportedDate > initialPublishedDate`, quarantine it from the historical initial-publication panel. Do not substitute `lastReportedDate` or `lastUpdateDate` as the revision's public timestamp.
3. Keep all missing, conflicting, duplicate-key and invalid-date cases quarantined; never convert missing activity to zero or silently aggregate conflicting LND rows.
4. Preserve ATS and non-ATS, Tier 1 and Tier 2, and firm/MPID concentration as separate measures. ATS volume does not identify aggressor direction, beneficial owner, investor sophistication or whether the activity is informed.
5. Use an effective-dated security master and historical F80 membership, including ticker changes, share classes, mergers, delistings and inactive names. Current ticker overlap alone is not sufficient.

The stable subset is promising in completeness, but **the source is not yet eligible for an economic test** because the effective-dated security identity and historical comparison-universe gates remain open. Phase 385's implementation PR [#61](https://github.com/jafelix81/NuevaEstrategia/pull/61) remains Draft and is severely diverged from current main (189 commits ahead / 455 behind); do not merge it as-is. The audit result is useful, but the old branch needs deliberate reconstruction before its workflow/code can be reused.

## 5. Economic hypotheses — still hypotheses

After identity and stable-row gates pass, preregister separately:

- Abnormal ATS share of consolidated volume.
- Change/acceleration in ATS participation.
- Concentration across ATS MPIDs.
- ATS versus non-ATS divergence.
- Whether any apparent effect vanishes after controlling for prior return, contemporaneous return, volatility, turnover, size and liquidity (return-chasing / mechanical activity control).

Compare each feature incrementally against frozen LTM/F80 with identical universe, exposure and costs; chronological walk-forward/OOS; block bootstrap; leave-one-time-block/event-block-out; and multiplicity control. No feature selection from the final holdout.

## 6. Source priority and next gates

- **FINRA ATS stable-row panel:** strongest public off-exchange stock-level candidate once historical security identity is solved; use only revision-stable rows for the initial publication clock.
- **FINRA Consolidated Short Interest:** next single-date validation is settlement 2026-11-13 after the 2026-11-24 21:40 UTC documented availability gate, with authorized credentials and permitted-use rights. Its manual workflow default must be overridden explicitly.
- **SEC Schedule 13D:** high-information activist/control-intent hypothesis, but the existing panel remains quarantined pending `SEC_USER_AGENT`, subject-issuer identity and public-dissemination controls.
- **Options OI/IV/flow:** high information potential, but Cboe/Massive/ThetaData/OCC remain license, first-receipt, historical-vintage and exact-universe coverage gated.
- **SEC MIDAS:** exchange-market-structure/liquidity context only; not dark-pool or participant identity.
- **CFTC TFF:** market-regime context only; two prospective vintages are insufficient for the preregistered sample.
- **13F:** parked for insufficient historical identity/coverage; N-PORT raw quarter-over-quarter share-growth remains killed as a standalone ranking.

## 7. Decision and controls

- New signal admitted: **0**.
- Incremental alpha demonstrated: **none**.
- Return/event/OOS/bootstrap/LOO test: **not run**.
- No raw FINRA data or licensed data added to the public repository.
- No universe, parameter, holding-period, exposure, cost, holdout or production change.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

**Conclusion:** FINRA ATS is closer to a defensible PIT stock-level research panel than the prior “revision clock unknown” label suggested, but only the revision-stable subset can use the verified initial-publication clock. Revised observations remain quarantined until a true public revision timestamp or prospective first-receipt vintage is available. The remaining decisive blocker is effective-dated security identity and universe continuity, not another alpha experiment.
