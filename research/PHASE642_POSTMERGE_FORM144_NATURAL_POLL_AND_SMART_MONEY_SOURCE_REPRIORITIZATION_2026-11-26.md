# Phase 642 — post-merge Form 144 natural-poll validation and Smart Money source reprioritization

**Audit cutoff:** 2026-11-26 14:16 UTC (07:16 America/Hermosillo)  
**Main HEAD before the new capture commit:** `bbff4e81dc6c01c3162d7b43bf1e797deacc372e`  
**Capture commit:** `e594a7a46b0ec43bf8b6c3490b5b0eb1829b6ae7`  
**Disposition:** first natural post-merge Form 144 poll completed successfully and exercised the Phase 638/639 code path. It added no new filing accessions, but advanced structured-detail backfill. No investment signal, return test or alpha evidence.

## 1. Actions preflight and run adjudication

Queried the latest 100 repository-wide Actions runs before any write:

- Total repository run count: **8,348**.
- Latest 100: **71 success / 17 failure / 12 cancelled**.
- Queued, waiting, requested or in-progress among the latest 100: **0**.
- No workflow was dispatched, rerun, cancelled or duplicated.

Latest relevant scheduled runs:

| Source | Latest scheduled run | Result | Post-merge status |
|---|---:|---|---|
| Form 144 / Phase 403 | [45827105431](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45827105431), 2026-11-26 13:13:48 UTC | Success | **Post-merge** of PRs #244/#245 |
| Form 4 / Phase 476 | [45759597509](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45759597509), 05:08 UTC | Success | Pre-merge of PR #240 |
| SEC 13F / Phase 614 | [45751086501](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45751086501), 03:46 UTC | Failed before SEC request | Pre-merge of PR #243 |
| CFTC TFF / Phase 384 | [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471), 04:12 UTC | Success; no new report/revision | Prospective ledger unchanged |
| FINRA Reg SHO / Phase 469 | [45754121648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648), 04:16 UTC | Workflow success; all eight files rejected | Zero accepted observations |

The new Form 144 run had two successful jobs: `offline-regression` and `live-capture`. The live job completed capture, ledger quality audit, 10b5-1 audit, append-only persistence and artifact upload. No active run was found at the audit cutoff.

## 2. Form 144 — first natural post-merge validation

Run [45827105431](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45827105431) ran on `main` after Phase 638 and Phase 639 had been merged.

### Feed and poll integrity

- Both feeds succeeded: Form 144 and Form 144/A.
- **53** feed observations were received and appended: 50 Form 144 entries and 3 Form 144/A entries.
- Pagination completed and prior watermarks were found.
- No feed errors and no possible feed-window gap.
- **0 new accessions** and **0 new XML resolutions** in this poll.
- First-seen remains a successful-poll receipt upper bound, not an exact public-availability timestamp.
- The poll's new-candidate research-observation count and signal-eligible count were both zero.

The run therefore validates the post-merge capture/quality/persistence path, but it does not add a new Form 144 event.

### Structured-detail backfill and ledger quality

The scheduled backfill parsed 10 previously queued accessions and appended **52** structured detail rows. It left 178 accessions in the bounded backfill queue. The append-only structured ledger now contains:

- **825** accessions;
- **5,495** detail rows;
- 817 Form 144 and 8 Form 144/A accessions;
- 447 issuer CIKs;
- zero parse errors;
- zero source-hash mismatches.

The commit diff confirms that this run changed only feed observations, structured sale details and poll state; it did not add event-ledger accessions.

Phase 516 post-capture quality audit:

- **807** filing headers have bounded intervals between successive successful polls.
- **18** are explicitly classified as initial-baseline observations without a lower bound.
- **0** malformed/missing intervals among research-observation-eligible filings.
- **0** public-availability-certified filings.
- **0** signal-eligible filings.

This validates the Phase 638 distinction between legitimate initial-baseline rows and malformed intervals. It does not certify the exact timestamp at which the public could first trade on a filing.

Artifacts:
- [Phase 516 ledger-quality artifact](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45827105431/artifacts/15119964060)
- [Phase 565 post-capture 10b5-1 artifact](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45827105431/artifacts/15120861777)

### Updated 10b5-1 descriptive audit

The refreshed Phase 549 audit reports:

| Measure | Result |
|---|---:|
| Formal plan-adoption dates | 304 / 825 accessions (36.85%) |
| Distinct adoption dates | 130 |
| Plan date before notice date | 303 |
| Plan date equal to notice date | 1 |
| Plan date after notice date | 0 |
| Explicit positive 10b5-1 Remarks | 23 |
| Explicit negative mentions | 4 |
| Ambiguous mentions | 3 |
| No Remarks mention | 795 |
| Sell-to-cover / tax-withholding accessions | 18 |

The four Fermi notices remain a negative control: 2,253,270 proposed units in aggregate, explicitly described as sell-to-cover/tax withholding and not as 10b5-1 sales. These are proposed-sale notices, not confirmed executions. Formal plan dates and Remarks polarity are context, not signal availability.

**Decision:** Form 144 remains a descriptive proposed-supply/order-event source and a useful negative-control dataset. Do not interpret notice counts, plan dates or proposed units as executed selling or informed bearish flow.

## 3. Reprioritization: FINRA T1 ATS versus FINRA Reg SHO

The broader FINRA work contains a more promising *market-structure* dataset than the currently blocked Reg SHO daily files.

### T1 ATS weekly panel

The existing Phase 375/385 research reports:

- 209/209 weekly partitions retrieved, 2021-11-15 through 2025-11-10;
- 10,917,933 rows across 2,292 pages, with Record-Total reconciliation;
- 209/209 symbol bridges from aggregate to reporting ATS/firm rows;
- 438,798 aggregate symbol-week groups;
- 432,804 revision-stable/concentration-ready groups;
- stable groups represent 96.943175% of mapped aggregate share volume;
- Phase 385 verified one actual `initialPublishedDate` for all 209 partitions and mapped each to the first XNYS regular session strictly after publication.

This is materially better historical retrieval and date-level publication coverage than the Reg SHO line currently provides. But it is **not investor flow**: MPID/CRD-derived keys identify reporting ATS/firm venues, not customers, beneficial owners, traders or verified institutions. HHI/top-share variables measure ATS venue concentration, not “smart money” concentration.

Remaining gates before any return study:
1. Effective-dated CUSIP/FIGI/ticker and corporate-action identity.
2. Historical F80 membership rather than a current 335-name snapshot.
3. Inactive/delisted security prices and terminal-return treatment.
4. Reproducible date-level publication clock joined to the symbol-week rows.
5. Coverage sensitivity by week, symbol and mapped volume.

PRs [#50 Phase 375](https://github.com/jafelix81/NuevaEstrategia/pull/50) and [#61 Phase 385](https://github.com/jafelix81/NuevaEstrategia/pull/61) remain Draft and based on older branches. Compared with current `main`, their branches are respectively 177/560 and 189/560 commits ahead/behind. Do not merge either chain wholesale. Port only narrowly scoped, reviewed code if a fresh-mainline identity/price feasibility audit justifies it.

### Reg SHO

The latest daily Reg SHO run received eight HTTP-200 files but rejected all eight under the fail-closed BCPC/TPC duplicate-symbol gate. No volumes were admitted. Keep issue [#214](https://github.com/jafelix81/NuevaEstrategia/issues/214) open; do not sum, drop or reinterpret ambiguous rows.

**Priority change:** treat FINRA T1 ATS as a conditional off-exchange venue-concentration/liquidity hypothesis. Keep Reg SHO quarantined. Neither is currently an institutional-identity or alpha signal.

## 4. Other source gates

- **Form 4:** latest scheduled capture predates PR #240. The next natural capture must validate `entity_duplicate_audit.csv`; no manual run was launched.
- **13F:** PR #243's User-Agent fallback is integrated, but the latest scheduled run predates it. First natural post-merge poll remains pending. The 13F branch chain (#221–230) is stale/diverged; no wholesale merge.
- **13D/G:** 43/44 parent documents recovered; 31/42 comparable CUSIPs match, with five mismatches and six missing parent CUSIPs still quarantined. PR #37 is heavily diverged and remains Draft.
- **CFTC TFF:** 3,035 historical archive rows remain unverified PIT proxies; only eight prospective observations across two report-date clusters exist. The static archive Updated field is not a safe global availability timestamp. Continue prospective capture only.
- **Options:** IvyDB TradeFlow remains a conditional all-venue signed-flow candidate; Cboe Option Trades is the independent OPRA-wide raw trade/NBBO validation candidate; Open-Close is a four-Cboe-venue capacity/open-close complement; PITCH is a separate book-depth candidate. Historical version/revision/first-receipt, 335-name coverage, business-use rights and cost remain unresolved. No vendor contact, sample, quote, license or purchase; authorized options budget remains **USD 0**.
- **SEC MIDAS:** keep as market-structure/risk context, not institutional identity or dark-pool beneficial-owner flow; quarterly release timestamps and effective-dated universe coverage remain unverified.

## 5. Quantitative disposition

- New signals admitted: **0**.
- Incremental alpha versus frozen LTM/F80: **none demonstrated**.
- New valid OOS, bootstrap or LOO evidence: **0**.
- No return/event study, final-holdout access or production change.
- No changes to universe, parameters, exposure, costs, capital or holding-period policy.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## 6. Next gates

1. Wait for the next natural post-merge Form 4 and 13F scheduled polls; do not dispatch duplicates.
2. Continue bounded Form 144 detail backfill, preserving accession grain and negative controls.
3. If pursuing FINRA T1 ATS, start a narrow fresh-mainline identity/universe/price feasibility audit; do not merge stale Phase 375/385 branches.
4. Keep Reg SHO, historical CFTC archive and options signals quarantined until their respective data/PIT/rights gates pass.
5. Only then consider a preregistered incremental test against frozen LTM/F80 with identical exposure, costs, chronological validation, bootstrap and LOO.

No baseline or production change is authorized by this phase.
