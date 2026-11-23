# Phase 569 — Open research-PR adjudication and post-Phase-565 operations recheck

**Audit cutoff:** 2026-11-23 05:39 UTC  
**Main HEAD at preflight:** `c3b78cb20773cfe130053c8426487ad61220decb`  
**Disposition:** consolidate material findings from current draft research PRs without merging stale branches; identify the still-unvalidated post-Phase-565 capture and recurring SEC schedule gap. No new signal or alpha result.

## 1. Repository and Actions preflight

- Repository Actions API: **8,072 total runs**; latest 100 = **96 success / 4 failure**; explicit queued and in-progress queries both returned zero.
- Branch inventory: **373** across five pages. Open PR search: **72**.
- No workflow was dispatched, rerun, cancelled, or duplicated.
- Latest overall run [45096929863](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45096929863) is PR CI for Phase 565. Jobs: `offline-regression` succeeded and `live-capture` was skipped as designed. The decoded log confirms **80/80 tests passed**. Artifact [14783278471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45096929863/artifacts/14783278471) is the pre-capture Phase 560 descriptive refresh, not the new post-capture Phase 549 artifact.

## 2. Form 144 / Form 4 schedule and artifact status

### Form 144 — Phase 403

- Main workflow cron remains `47 * * * *`.
- Latest natural run remains [45085664016](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45085664016), created 2026-11-22 23:53:30 UTC. Both jobs succeeded.
- The live job's step list/log confirms the Phase 516 post-capture ledger reconciliation passed and the append-only ledger was committed. It predates the Phase 565 merge, so it did **not** run the new post-capture Phase 549 polarity classifier.
- Current ledger at that run: **295 accessions / 2,196 detail rows**, 268 bounded backfill accessions remaining; 53 feed entries observed but zero new entries/accessions/events; 10 existing accessions backfilled with 82 detail rows; zero parse errors/hash mismatches; zero public-availability-certified and zero signal-eligible filings.
- Unexpired artifacts: [14778539572](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45085664016/artifacts/14778539572) (capture/poll audit) and [14779385856](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45085664016/artifacts/14779385856) (pre-capture Phase 560 refresh).
- At the 05:39 UTC cutoff, no later schedule event appears. The 00:47–04:47 UTC hourly slots are absent; 05:47 had not yet occurred. This is an observed delivery gap, not proof of administrative disablement.

### Form 4 — Phase 476

- Main workflow cron remains `17 * * * 1-5`.
- Latest natural run visible is [44846461134](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134), created 2026-11-21 00:50:30 UTC. Both jobs succeeded; artifact [14683520646](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134/artifacts/14683520646) is unexpired.
- Its live log records 15 owner rows appended, 20 owner-sidecar accessions remaining, three descriptive Form 144/Form 4 crosswalk rows, two matched Form 4 accessions, eight Form 4 accessions without single-owner identity, and **zero signal-eligible matches**. The current structured Form 4 census is 70 transaction rows / 40 accessions / 32 issuer symbols; filing-level ownership is not transaction-line attribution.
- No later Form 4 schedule run appears in the latest 100 Actions records. Do not interpret transaction dates or EDGAR acceptance as an exact public-availability clock.

Issue [#194](https://github.com/jafelix81/NuevaEstrategia/issues/194) remains the single operational tracker. The connector cannot inspect repository Actions administrative settings or confirm whether scheduled workflows are enabled/permitted; a human check in GitHub Actions/Settings is still required. No cron change or manual poll was made.

## 3. Cross-source live-capture reconciliation

| Source | Latest inspected natural run | Actual result | Research disposition |
|---|---|---|---|
| FINRA Reg SHO | [44860690600](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600) | 8 HTTP-200 files, 8 invalid, 0 valid, 0 eligible; artifact [14688803921](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600/artifacts/14688803921) | Predates Phase 539 merge; natural post-merge validation still required |
| CFTC TFF | [44860341977](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977) | Four prospective contract events; 3,043 archive rows; artifact [14689726870](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977/artifacts/14689726870) | Only two prospective report vintages; historical archive rows remain feature-ineligible |
| FINRA Weekly Summary | Phase 518 panel | 259 consecutive weeks, 2021-11-15 to 2026-10-26 | Candidate only; date-only final-value proxy is not strict PIT |
| FINRA Short Interest | Phase 447 workflow | No successful live query | 2026-11-24 publication for 2026-11-13 settlement; one-settlement test requires authorized credentials/terms |

FINRA Weekly Summary's proposed final-value knowledge-date floor remains `max(initialPublishedDate,lastUpdateDate)`, with execution no earlier than the next regular session. Phase 100 found 1,882 sampled symbol rows whose `lastUpdateDate` followed initial publication. Exact public timestamps, revision vintages, effective-dated universe coverage, two LND composite-key groups and permitted API use remain unresolved. Do not use the final value at initial publication time or infer beneficial-owner direction from ATS/OTC reporting-entity rows.

CFTC TFF still has only two prospective vintages (2026-11-10 and 2026-11-17) across four index contracts. Phase 387 is a frozen weekly crowding/downside-risk hypothesis, not a directional stock-selection test; its event-count and maturity design implies a multi-year prospective sample. No historical CFTC archive row is promoted to PIT feature eligibility.

## 4. Material adjudication of current draft research PRs

These findings are recorded here without merging the old branches. All listed branches are materially behind current main and remain draft.

### PR #201 — SEC MIDAS methodology / off-exchange scope

- The public MIDAS per-security series is an **exchange market-structure** dataset, not an off-exchange or participant-identity feed.
- Hidden trades are executions against undisplayed resting orders on exchanges; the public MIDAS hidden-volume metric must **not** be described as dark-pool/off-exchange institutional accumulation. That interpretation is killed for scope mismatch.
- Retain MIDAS only as a conditional exchange liquidity/market-structure-state candidate. The 59-quarter catalog (2012 Q1–2026 Q3) does not establish exact frozen-335 coverage, delisted identity, ZIP integrity or per-quarter first-public timestamps.
- PR [#201](https://github.com/jafelix81/NuevaEstrategia/pull/201) remains Draft; branch is 2 commits ahead / 43 behind main.

### PR #200 — Cboe OPRA options / Open-Close

- OPRA-wide Option Trades + Option Quotes remain the strongest documented broad options data candidate; Cboe Open-Close is a narrower Cboe-venue capacity × buy/sell × open/close complement.
- No sample or licensed data were acquired. Historical file receipt/correction vintages and exact historical F80 optionability remain unverified.
- Cboe DataShop standard terms require a separate written, executed authorization for using data/methodology to create an index, indicator, benchmark or investment strategy; applicable third-party OPRA rights must also be confirmed. **No strategy research or purchase is authorized under standard terms alone.**
- PR [#200](https://github.com/jafelix81/NuevaEstrategia/pull/200) remains Draft; branch is 5 ahead / 43 behind main.

### PR #199 — Form 4 negative control

- The only exact overlap found in the current structured Form 4 ledger versus the static 335-symbol snapshot is SE / Sea Ltd.
- It is **one accession with seven sale lines**, with affirmative `AFF10B5ONE=yes`; treat it as a planned-trading negative control, not seven independent discretionary insider sales.
- Filing-level owner data and first-seen upper-bound timing do not establish transaction-line beneficial-owner attribution or exact public availability. Zero signal-eligible rows.
- PR [#199](https://github.com/jafelix81/NuevaEstrategia/pull/199) remains Draft; branch is 5 ahead / 43 behind main.

### Other stale branches

- PR #198 (Phase 542 FTD User-Agent): 6 ahead / 46 behind; its SEC secret-backed path is superseded by the consolidated PR #204 and should not be merged separately.
- PR #159 (FINRA Short Interest): 7 ahead / 146 behind; one authorized live settlement validation remains the only next gate after credentials and permitted-use terms are confirmed.
- PR #204 (SEC FTD shared credential contract): 11 ahead / 23 behind; still needs `SEC_USER_AGENT` and a deliberate refresh/review before its bounded two-file sample.
- PR #1 (Phase 29 Independent Alpha Lab): 5 ahead / 538 behind. Phase 480 already adjudicated MOM120 as baseline-family reconfirmation, not incremental alpha; do not rerun the same candidate selection or merge the stale branch.

## 5. Phase 20C and baseline integrity

Phase 20C remains at **328/335** valid price histories. AVB, EA, EQR, LPRO, ROKU, WBD and WBS are inactive/acquired/renamed cases. Their terminal/successor total-return and corporate-action reconciliation is still incomplete. Do not silently drop or replace them, mix unvalidated price providers, or run a reduced-universe result as if it were the frozen universe.

## 6. Decision and next gates

1. Human: verify Phase 403 and Phase 476 workflows are enabled and repository scheduled Actions are permitted; do not alter cron or dispatch duplicate polls before that check.
2. On the first natural post-Phase-565 Form 144 run, inspect the distinct `phase565-form144-10b5-post-capture` artifact and verify accession/detail reconciliation plus `signal_admitted=false`.
3. On the next natural FINRA Reg SHO run, verify Phase 539's fail-closed row-grain/duplicate diagnostics before accepting any file.
4. On 2026-11-24, use the existing Phase 447 one-settlement FINRA Short Interest workflow only if an authorized maintainer has configured valid credentials and confirmed the project's permitted use; explicitly pass settlement date `2026-11-13`. Do not batch historical dates.
5. Keep MIDAS as exchange-liquidity context only; keep Cboe options blocked pending written strategy-use rights and sample/PIT/universe validation; keep TFF prospective-only.

**Quantitative result:** new signals admitted 0; incremental alpha demonstrated none; new OOS/backtest/bootstrap/LOO tests 0; exposure, costs, universe, holding-period policy, holdout and production unchanged. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
