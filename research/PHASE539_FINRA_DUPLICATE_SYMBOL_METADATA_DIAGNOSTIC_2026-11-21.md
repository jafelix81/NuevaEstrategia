# Phase 539 — FINRA Reg SHO duplicate-symbol metadata diagnostic

**Audit cutoff:** 2026-11-21 04:50 UTC  
**Main HEAD before this phase:** `1df3e9fdd5d6171c17741cef4eb350e0bb73fc51`  
**Disposition:** diagnostic instrumentation added on an isolated branch; live duplicate structure still unobserved. Files remain fail-closed. No aggregation rule, signal, or strategy change.

## 1. Preflight

- Reviewed the latest 100 Actions runs, jobs, logs, artifacts, branches, open PRs, issues and current research files.
- At the cutoff, all 100 returned runs were completed; no in-progress, queued or waiting run was present. No workflow was dispatched, rerun, cancelled or duplicated.
- Latest scheduled runs:
  - FINRA Reg SHO Phase 469 [44860690600](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600).
  - CFTC TFF Phase 384 [44860341977](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977).
  - SEC Form 144 [44847230610](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44847230610).
  - SEC Form 4 [44846461134](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134).
- Phase 537 PR [#196](https://github.com/jafelix81/NuevaEstrategia/pull/196) remains Draft. Existing option-vendor and older feasibility PRs were left untouched.
- New branch: `phase539-finra-duplicate-symbol-metadata-diagnostic`. No production workflow was dispatched.

## 2. Reproduced FINRA failure

Scheduled run [44860690600](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600) completed operationally and its 59 offline regression tests passed. The live poll requested eight trade dates (2026-11-20, 19, 18, 17, 16, 13, 12 and 11):

| Result | Count |
|---|---:|
| HTTP 200 | 8 |
| Valid files | 0 |
| Invalid files | 8 |
| HTTP errors | 0 |
| First-seen / research-eligible observations | 0 |
| Signal-eligible observations | 0 |

All eight files failed with `duplicate_symbol_in_consolidated_file`. The metadata ledger contains response hashes and byte counts (542,484–566,746 bytes); no raw file is stored. `state.json` remains empty, so no file has been admitted as first-seen.

This follows the prior failure mode `market_code_invalid` from run [44669121290](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44669121290). The current parser recognizes comma-separated facility lists, but assumes that any file containing such a list is security-grain and therefore requires unique symbols.

## 3. Diagnostic implementation

The parser still rejects every consolidated-file duplicate. The new exception carries metadata-only diagnostics:

- number of duplicate symbols and extra rows;
- per-symbol row count and source line numbers;
- distinct facility-token sets, union and intersection;
- pairwise facility-token overlaps and number of overlapping row pairs;
- exact-row duplicate indicator/count, based on a SHA-256 fingerprint of the normalized row text.

The scheduled collector writes an append-only `duplicate_diagnostics.csv` ledger and a compact `duplicate_diagnostics.json` artifact. It records the file hash, response size, poll interval and diagnostic counts. It does **not** persist raw rows, volume values or row fingerprints. Existing `polls.csv` and `events.csv` schemas remain unchanged.

**Fail-closed invariant:** diagnostic output does not make a file valid. An invalid file remains ineligible, does not advance the first-seen state, does not produce symbol observations, and cannot enter Phase 468 labeling.

## 4. Why no aggregation change is authorized

A repeated symbol with different facility-token sets could represent disjoint facility-grain records, overlapping consolidated coverage, a mixed-grain export, or a duplicate publication artifact. A repeated symbol with identical facility sets could still contain different volume measures. Summing or deduplicating before identifying the source row grain can double-count or discard real activity.

The next natural scheduled capture should reveal which structure is present. Even then, any revised parser must be justified against FINRA's actual file semantics and independently tested. No automatic sum, max, first-row-wins or last-row-wins behavior is introduced here.

FINRA Reg SHO daily short volume is executed short-sale flow, not outstanding short interest or beneficial-owner positioning. A recovered file would still require first-receipt PIT, effective-dated identity, delisted-security returns and an incremental test against frozen LTM/F80 before any economic interpretation.

## 5. Other source status at the cutoff

- **CFTC TFF:** run [44860341977](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977) captured four new prospective reports, report date 2026-11-17, first received 2026-11-21 03:17:36 UTC. The panel now has 3,043 rows; only prospectively received events are research-observation eligible. Two observations per contract are insufficient for a positioning signal.
- **SEC Form 4/Form 144:** both scheduled captures completed. The strict crosswalk still has three descriptive matches and zero signal-eligible matches. Atea's two proposed sales are linked to option exercise/tax planning, not classified as discretionary bearish sales.
- **Phase 20C:** the latest full-universe census remains 328/335 valid price histories. Seven inactive/renamed/acquired names still need terminal-return and corporate-action reconstruction.
- **Options, ATS, Short Interest and SEC 13D/G:** remain gated by source access, PIT/vintage, universe identity or licensing/credential requirements. No vendor data was purchased or terms bypassed.

## 6. Validation and decision

Two new offline tests cover (1) duplicate-symbol diagnostics and exact-row detection without volume leakage, and (2) persistence of metadata while preserving invalid status and an empty first-seen state. Existing parser and capture tests remain in place. PR [#197](https://github.com/jafelix81/NuevaEstrategia/pull/197) offline regression run [44868210834](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44868210834) passed **61 tests**. The live-capture job was skipped as designed for a pull-request event; natural scheduled validation remains pending.

No live poll, backtest, event study, OOS, bootstrap, LOO, price download or alpha test was started in this phase. The next live diagnostic must be obtained from the existing scheduled workflow, not a manual dispatch.

## Frozen controls

- `F80_TOP20_PARTIAL50_BASELINE_C20` unchanged.
- Universe, parameters, exposure, costs and holding-period policy unchanged.
- New signals admitted: **0**.
- Production changes: **0**.


## Post-audit disposition

After the 04:50 UTC audit cutoff, PR [#197](https://github.com/jafelix81/NuevaEstrategia/pull/197) was reviewed, marked ready and merged to `main` at 2026-11-21 05:22:40 UTC. Merge commit: [c7666f03](https://github.com/jafelix81/NuevaEstrategia/commit/c7666f03a6e01c569fce7b98e1651490bf2376dc). This enables the existing scheduled collector to write the new metadata-only diagnostics. The next natural scheduled capture remains pending; no manual dispatch or rerun was used.
