# Smart Money Research — current state (2026-11-13 UTC)

**Frozen baseline:** `F80_TOP20_PARTIAL50_BASELINE_C20`  
**Legacy holdout:** `CONSUMED_NOT_PRISTINE`; do not reuse.  
**Economic status:** no new Smart Money feature has demonstrated incremental, cost-adjusted OOS edge. No CAGR target or holding-period constraint is imposed.

## Latest completed phase — Phase 351: Cboe TBT public sample

The public Cboe TBT 3% sample for 2025-03-28 was downloaded and parsed against the 22-field v1.1 schema. Hosted workflow passed **16/16 regression tests** and the metadata-only sample gate.

- 113,018 rows; 1,250 underlyings; 25,015 complete option-series identities.
- 111,333 `EXEC_ID` groups: 109,648 singleton and 1,685 two-row Buy/Sell groups.
- 46,350 `COMPLEX_EXEC_ID` groups; 2,111 span multiple complete option series.
- `OPEN_CLOSE` blank on 20,180 rows (17.86%); 507 rows (0.45%) lack OSI root and call/put identity; 69 side codes are unmapped.
- All 113,018 rows show `TRADING_SEGMENT=1`, including 111,240 RTH rows. This conflicts with the v1.1 specification's 1=prior-evening/overnight and 2=daytime example. Do not use segment labels pending clarification.
- 306 rows have a calendar date mismatch between `TRANSACT_TIME` and `TRADING_DT`; all timestamps are timezone-naive in the sample. Use `TRADING_DT` for market date; do not invent timezone.
- NBBO/BBO are present on all rows; 12 crossed NBBO, 2 crossed BBO, 1,646 trades outside NBBO. `FLOOR_ACTION_TS` is blank on 99.45% of rows.

This validates the sample parser and execution-linkage diagnostics only. The sample is one date and a 3% subset; it is not assumed random or representative. The 2025 archive sample is retrospective backfill, not PIT. C1 is not all-OPRA. No returns or alpha were tested.

- [Phase 351 report](PHASE351_CBOE_TBT_PUBLIC_SAMPLE_ROW_GRAIN_AUDIT_2026-11-13.md)
- [Hosted run 43357411197](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43357411197)
- [Metadata-only artifact 14006931596](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43357411197/artifacts/14006931596)
- [Draft PR #38](https://github.com/jafelix81/NuevaEstrategia/pull/38)

## Source dispositions

| Source / line | Current disposition |
|---|---|
| Cboe TBT | High-priority conditional C1 measurement candidate; sample parser passes, but row-grain/sampling, 17.86% open-close missingness, side-code mapping, session/segment discrepancy, licensing, first receipt, corrections and inactive-underlying coverage remain open |
| Cboe Open-Close | One C1 EOD sample date and feature parsing only; no multi-date PIT/vintage proof |
| Cboe Option Sentiment | Historical start advertised at 2012; field cross-tabs and net-delta units/sign remain insufficient for a directional participant hypothesis |
| Cboe Option Quotes | Conditional option risk/context source; sample parser corrections do not establish PIT, all-symbol history or inactive names |
| CFTC TFF/COT | Historical strict PIT rejected: CFTC lacks complete historical release-date ledger; 2023 ION outage and 2025 funding lapse invalidate synthetic availability proxies. Legacy Phase 23C walk-forward quarantined; no reuse |
| CFTC BPR | Monthly broad equity-index regime context only; public retention 25 months, no historical first-receipt ledger; prospective capture staged but not active on default branch |
| FINRA short flow / short interest | Weak/incomplete or timing/pagination defects; no promotion |
| FINRA ATS / OTC | Context-only; later revisions and unresolved duplicate-grain conflicts; do not sum/choose arbitrarily |
| SEC Form 4 | Bulk history and daily-index PIT route are feasible candidates, but raw retrieval, owner attribution and effective-dated security identity remain blocked/incomplete |
| SEC 13D/G | CUSIP and explicit predecessor audits improved identity integrity; broad event/security panel still not admitted |
| SEC 13F / N-PORT | Delayed context only; acceptance/amendment timing and security mapping remain open |
| Form 144 | Filing/role and document-linkage work only; no market-execution or return edge established |

## SEC retrieval blocker

Phase 350's latest hosted attempt [43344689909](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43344689909) stopped before SEC requests because the repository secret `SEC_USER_AGENT` was not configured. No request was sent by that guarded run and no document was retrieved. The earlier HTTP 403 attempt remains quarantined. Do not retry until the secret contains a monitored contact address in the User-Agent. Do not expose the address in code, logs or chat.

## Active GitHub work

- PR #38: Phase 351 TBT sample audit, Draft/Open, not merged.
- PR #37: Phase 350 SEC 13D/G parent retrieval, Draft/Open, blocked on `SEC_USER_AGENT`.
- PR #14 and PR #13: broader stacked research work remains open/unmerged. Do not merge any PR without explicit authorization.
- No active workflow was duplicated; each Phase 351 run was checked before a subsequent update.

## Next gates

1. Resolve the TBT sample's 3% selection rule, row grain, missing `OPEN_CLOSE`, 69 unmapped side codes, and `TRADING_SEGMENT` discrepancy before any feature construction.
2. If later authorized, obtain a lawful representative/eligible sample or trial and written licensing terms; do not purchase or contact a vendor autonomously.
3. For any prospective TBT feed, archive every received file/version with first-receipt UTC, raw hash, schema version and corrections; use only after receipt.
4. Continue the SEC 13D/G and Form 4 retrieval path only after the required monitored-contact secret is configured.
5. Any eventual economic test must use a new untouched prospective holdout, strict chronological splits, label-maturity embargoes, identical exposure/costs versus frozen LTM/F80, clustered bootstrap, LOO and multiplicity controls.

## Controls

No signal admitted. No returns, alpha, OOS, bootstrap or LOO test performed in Phase 351. No holdout used. No vendor contacted, no trial requested, no data purchased, no terms accepted, no PR merged, no production/universe/capital/parameter change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
