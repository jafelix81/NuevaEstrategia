# Phase 529 — SEC scheduled-capture gap and Smart Money operational preflight

**Audit time:** 2026-11-20 15:32 UTC  
**Main HEAD:** `bb437a6956a28457b21a77e88e2820799b202b84` (Phase 527 merged)  
**Disposition:** **SEC post-Phase-525 live validation remains blocked by an observed scheduled-run gap. No source or signal admitted.**

## 1. Preflight

- Inspected the latest 100 of 7,964 Actions runs, jobs, logs, artifact metadata, main commits, branches, open PRs, issue #185, relevant workflow YAML and research files.
- No run was queued, in progress, waiting or requested in the inspected latest-run page. No workflow was dispatched, rerun, cancelled or duplicated.
- Latest overall run: [44728717197](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44728717197), successful PR check on `phase525-report-count-reconciliation`; its `live-capture` job was skipped. It is not a live SEC capture.
- Phase 528 remains open as draft PR [#186](https://github.com/jafelix81/NuevaEstrategia/pull/186), documentation-only, mergeable, with no sample, purchase, vendor contact, credentials, collector, backtest or signal admission. Its head is `4453d5666d5fcd6ab57d87eeae8b7b0f228b32b8`; the changed paths do not match a research-code workflow trigger.

## 2. SEC schedule gap

The schedule-filtered Actions query (`event=schedule`, `branch=main`) returns 38 historical schedule runs. The latest SEC runs are:

| Workflow | Latest scheduled run | Job result | Artifact |
|---|---|---|---|
| Form 4 / Phase 476 | [44716430351](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44716430351), 10:06:51 UTC | offline + live success | [14619333577](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44716430351/artifacts/14619333577), 1,311 bytes |
| Form 144 / Phase 403 | [44720422923](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44720422923), 10:34:45 UTC | offline + live success | [14621821685](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44720422923/artifacts/14621821685), 1,902 bytes |

### Form 4 details

- The live log records 33 new accession observations, 10 structured accessions, 37 detail rows (27 transactions), zero parse errors and 1,213 bounded accessions remaining.
- The run predates Phase 525's merge. Its log contains no owner-enrichment or crosswalk step.
- Main now contains the Phase 525 code and the scheduled steps: `phase525_form4_reporting_owner_identity.py --mode schedule --limit 10` and `phase525_form144_form4_crosswalk.py`.
- Current schedule in main: `17 * * * 1-5`.
- `research/data/sec_form4_first_seen/reporting_owners.csv` remains absent on main.

### Form 144 details

- The live log records no new accessions, parses 10 previously bounded accessions, reports zero parse/hash errors and 358 structured accessions remaining.
- Current schedule in main: `47 * * * *`.

No scheduled SEC run appears after 10:34:45 UTC in the latest 100-run listing. At the audit cutoff, the following configured slots had no corresponding run:

- Form 4: 11:17, 12:17, 13:17, 14:17 and 15:17 UTC.
- Form 144: 11:47, 12:47, 13:47 and 14:47 UTC.

This is an observed delivery gap, not proof that a workflow is disabled. GitHub scheduled events may be delayed or dropped. The read connector does not expose the workflow enable/disable setting or repository Actions settings, so their administrative state cannot be confirmed here.

**Human action:** verify in GitHub → Actions that Phase 476 Form 4 and Phase 403 Form 144 are enabled and that scheduled Actions are permitted. Then allow the next configured schedules to execute naturally. Do not manually dispatch both just to test them.

Issue [#185](https://github.com/jafelix81/NuevaEstrategia/issues/185) was updated with this evidence (comment 7043530451).

## 3. Research-source state

- **SEC Form 4 / Form 144:** parsers and Phase 525 crosswalk are code/test validated, but the owner sidecar and crosswalk are not live-data validated after merge. All observations remain descriptive; no signal eligibility.
- **SEC 13D/G:** [PR #37](https://github.com/jafelix81/NuevaEstrategia/pull/37) remains blocked by the missing monitored-contact `SEC_USER_AGENT` Actions secret. No retry was made. The secret must contain a project identifier and monitored contact email; do not expose it in chat or source control.
- **FINRA Reg SHO:** latest live run [44669121290](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44669121290) predates Phase 515. Post-fix live validation remains pending.
- **FINRA Consolidated Short Interest:** [PR #159](https://github.com/jafelix81/NuevaEstrategia/pull/159) remains draft; the controlled one-settlement validation requires authorized FINRA credentials and confirmation of usage terms. Do not run the 106-settlement backfill first.
- **FINRA T1 ATS:** aggregate weekly HHI remains killed for insufficient chronological sample; symbol-week panel remains deferred until effective-dated identity and survivorship-aware returns are solved.
- **CFTC TFF:** latest prospective capture [44668300202](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44668300202) contains 3,039 rows and no new report/revision; retrospective `Updated` timestamps remain ineligible as PIT.
- **Options:** ThetaData remains a conditional options trade/quote, OI and IV candidate. The 6/10/14-year individual tiers do not establish historical first-receipt vintages, 335-name inactive/delisted coverage, professional bulk rights, non-display/OPRA classification or internal derived-work retention. No data, trial or license was acquired. Cboe DataShop strategy research remains blocked absent a separate executed license carve-out.
- **SEC 13F / N-PORT:** broad-universe 13F remains parked for historical identity/coverage; the specified N-PORT share-growth signal remains killed. Do not reopen by threshold tuning.

## 4. Strategy controls

- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No new feature or signal admitted; no forward-return test, event study, backtest, OOS, bootstrap, LOO or holdout use.
- No universe, parameter, exposure, turnover, cost, capital, production or workflow changes.
- The latest live runs are historical evidence only; no data were backdated to nominal cron slots.

## 5. Next gates

1. Human verification of scheduled SEC workflow enablement; then wait for natural Form 4/Form 144 runs and confirm `reporting_owners.csv` plus crosswalk output.
2. Obtain the monitored-contact `SEC_USER_AGENT` secret before resuming the 44 exact SEC 13D/G parent requests.
3. Validate FINRA Reg SHO after Phase 515 and, separately, one authorized FINRA Short Interest settlement before any batch.
4. Keep ThetaData at feasibility-only until written research/non-display/OPRA/retention rights and a small authorized sample are confirmed.

**Final disposition:** operational capture continuity is the immediate bottleneck. No Smart Money source has demonstrated incremental alpha over frozen LTM/F80.