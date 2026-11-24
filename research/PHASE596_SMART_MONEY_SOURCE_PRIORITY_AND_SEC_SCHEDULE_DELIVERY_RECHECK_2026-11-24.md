# Phase 596 — Smart Money source-priority consistency and SEC scheduled-capture delivery recheck

**Audit cutoff:** 2026-11-24 13:45 UTC  
**Main HEAD at preflight:** `e2f8ba6a7c7ec183a5ec55708bf7ff422872134c`  
**Disposition:** renew the SEC Form 4 / Form 144 schedule-delivery escalation; clarify that the Phase 595 13F accession-join pass does not supersede the existing 13F coverage/strategy kill gates. Schedule 13D remains the highest-priority ownership-disclosure rebuild after the SEC User-Agent prerequisite. No signal or return test is admitted.

## 1. Actions and repository preflight

The repository-wide Actions API was queried before any work:

- Total runs: **8,109**.
- Latest 100: **90 success / 10 failure**.
- `in_progress`, `queued`, `waiting`, and `requested`: **0 each**.
- Schedule-triggered runs in the returned inventory: **59**.
- Branches: **380** (100 + 100 + 100 + 80 across four pages).
- Open PRs: **72**.
- Workflow files on main: **96**.
- Research directory entries: **488**.

Relevant branch comparisons against current main:

| Branch | Ahead | Behind | Disposition |
|---|---:|---:|---|
| `phase47-sec-13f-pit-accession-join-audit` | 10 | 532 | Historical audit branch; do not merge |
| `phase289-sec13f-reentry-adjudication` | 916 | 496 | Deeply diverged; do not merge |
| `phase588-13dg-header-parser-line-boundary` | 2 | 20 | Parser fix is already on main; stale branch not needed |

No branch was merged, rebased, force-updated or deleted.

## 2. Latest scheduled runs, jobs, logs and artifacts

| Source | Latest run | Job result | Artifact |
|---|---:|---|---|
| FINRA Reg SHO / Phase 469 | [45339067236](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236) | Offline + live jobs completed successfully; six source files rejected by data gate | [14895571787](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236/artifacts/14895571787) |
| CFTC TFF / Phase 384 | [45338400329](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329) | Capture and regression completed successfully; no new report rows | [14895036288](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329/artifacts/14895036288) |
| SEC Form 4 / Phase 476 | [45332760566](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566) | Offline + live jobs completed successfully; both feed watermarks found | [14892950135](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566/artifacts/14892950135) |
| SEC Form 144 / Phase 403 | [45330252226](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226) | Offline + live jobs completed successfully; post-capture ledger and 10b5 audits passed | [14891955642](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14891955642), [14891416912](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14891416912), [14890729923](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14890729923) |

All listed jobs are completed and all listed artifacts were unexpired at the audit. Logs were inspected, including the capture summaries and post-capture gates. Workflow-level success must not be confused with acceptance of market observations.

### SEC Form 4

- 516 new canonical accession events and 6,022 total accession-observation ledger rows.
- 653 same-feed repeated observations and six cross-feed repeats; these are not 659 independent filings.
- Both Form 4 and Form 4/A watermarks were found.
- The bounded backfill parsed 10 accessions and appended 24 transaction-detail rows; 2,273 accessions remain in the transaction-detail queue.
- Owner enrichment parsed 10 accessions, appended 11 owner rows, and left 20 accessions pending. One of the ten parsed accessions was multi-owner.
- The descriptive Form 144/Form 4 crosswalk now has five rows; four multi-owner accessions remain quarantined.
- Research-observation-eligible and signal-eligible rows remain **zero**.

### SEC Form 144

- 477 accessions and 3,360 structured detail rows.
- 238 bounded detail-backfill accessions remain.
- Five acceptance reconciliations were unresolved in the Phase 595 audit.
- The latest post-capture ledger hash/count reconciliation passed.
- Signal-eligible headers remain **zero**. A proposed-sale notice is not proof of execution.

### FINRA Reg SHO

The live job returned HTTP 200 for six CNMS files (trade dates 2026-11-16, 17, 18, 19, 20 and 23), but rejected all six:

- Repeated symbols: BCPC and TPC in every file.
- 12 repeated-symbol occurrences / 12 extra rows across the six files.
- Facility sets overlap; rows are not exact raw-row duplicates.
- No raw volume values were persisted; no file was accepted.
- The 2026-11-24 request returned HTTP 403.
- Persistent state remains `files: {}`; first-seen and eligible counts are zero.

Keep Phase 469 fail-closed. Do not sum or drop rows based only on ticker/facility overlap.

### CFTC TFF

- 3,043 historical/prospective ledger rows.
- No new report or revision in run 45338400329.
- Latest report date for the four tracked contracts remains 2026-11-17.
- Historical rows remain ineligible as contemporaneous first-seen observations; no signal is admitted.

## 3. Renewed SEC schedule-delivery gap — human check required

The current main-branch workflow definitions still specify:

- Form 4 / Phase 476: `17 * * * 1-5`.
- Form 144 / Phase 403: `47 * * * *`.

The schedule-filtered Actions inventory shows:

- Latest Form 4 scheduled run: 45332760566, started 05:21:36 UTC; persisted poll ended 05:22:13 UTC. No Form 4 schedule run is present for **06:17 through 13:17 UTC** (eight expected weekday slots).
- Latest Form 144 scheduled run: 45330252226, started 05:00:27 UTC; persisted poll ended 05:01:16 UTC. No Form 144 schedule run is present for **05:47 through 12:47 UTC** (eight completed hourly slots). The 13:47 slot had not yet occurred at the 13:45 cutoff.
- The latest repository-wide run remains FINRA 45339067236 at 06:15:11 UTC. There are no active or queued runs.

The persisted Form 4 and Form 144 `state.json` files independently confirm those same last successful poll IDs/timestamps. This is a verified absence of scheduled run records at the audit cutoff, not proof that either workflow is disabled or that GitHub deliberately dropped events.

**Issue #194 was reopened** and updated with this exact recheck: [Issue #194](https://github.com/jafelix81/NuevaEstrategia/issues/194).

Human action: verify that Phase 403 and Phase 476 are enabled and that scheduled Actions are permitted for the repository. Do not manually dispatch, rerun, alter cron, or create replacement workflows solely to test delivery. The connected read interface does not expose workflow enabled-state or repository schedule-policy settings.

## 4. Source-priority consistency: Schedule 13D remains ahead of Form 13F

Phase 595 correctly demonstrated a **100% accession join** in two sampled Form 13F datasets:

- 2018 Q1: 6,570 submissions / 1,879,731 holdings / 25,816 CUSIPs.
- 2026 Jun–Aug: 11,852 submissions / 3,830,274 holdings / 34,951 CUSIPs.

That is a source-schema and accession-join result only. It does not establish historical security identity, full-universe coverage, or alpha. It does not overturn the existing 13F disposition:

- Phase 22C V6 coverage against the frozen 335-name denominator was 212/335 (63.28%) in 2016 Q1, 246/335 (73.43%) in 2020 Q1 and 280/335 (83.58%) in 2024 Q1.
- The effective-dated CUSIP/security-class crosswalk, inactive/delisted coverage and historical F80 membership remain unresolved.
- Phase 386 killed the specified N-PORT quarter-over-quarter aggregate share-growth ranking after mostly negative/unstable six-period dose-response results; Form 13F broad-universe ownership-change remained parked.
- The Phase 47 branch is 10 commits ahead but 532 behind main; its old workflow and hard-coded placeholder User-Agent are not safe to merge or replay.

**Clarification to the Phase 595 wording:** the two-snapshot join pass does not make Form 13F the next alpha or broad-universe research priority. Form 13F remains parked until a materially different, preregistered hypothesis and effective-dated identity/coverage gate pass.

The previously established Phase 555 source-priority decision remains controlling: **rebuild Schedule 13D subject-issuer identity first**, with Schedule 13G handled as a separate, slower ownership-state/context family. The rationale is event specificity and the faster 13D reporting regime, not an assumption that all activist filers are informed or profitable.

## 5. Schedule 13D/G rebuild readiness

The legacy Phase 28D/35 panel remains quarantined:

- 20,266 historical accessions.
- Phase 484 confirmed that stored issuer CIK/ticker can represent the reporting filer rather than the subject issuer; two original SEC filings explicitly show different subject issuers.
- Zero rows in the old artifact are certified as subject-issuer-verified from that artifact alone.
- Phase 485 added separate SUBJECT COMPANY / FILED BY parsing and accession-to-filer consistency checks.
- Phase 588 fixed single-line parsing of blank header fields; the natural offline regression [45330853390](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330853390) passed 11/11 tests.

This is a parser-quality pass, not a completed historical rebuild. The repository still requires a maintainer-confirmed `SEC_USER_AGENT` secret containing a descriptive project identifier and monitored contact before the planned bounded SEC retrievals. No secret values were inspected or changed; no SEC request or full-panel rebuild was made.

After the human prerequisite is confirmed, use only the already-planned bounded sample (44 exact-parent retrievals), reconcile headers, subject/filer identities, accession lineage, XML/legacy regimes and hashes, and measure subject-security coverage against the historical universe. Do not launch the 20,266-accession rebuild or open forward returns until the bounded sample passes.

## 6. Research decision and next actions

1. Re-establish reliable natural Form 4 / Form 144 schedule delivery after the maintainer checks Actions settings.
2. After `SEC_USER_AGENT` is confirmed, complete the bounded Schedule 13D subject-issuer rebuild; keep 13G separate.
3. Continue Form 4 transaction/owner backfills, but preserve multi-owner and transaction-semantics quarantines.
4. Resolve BCPC/TPC source row identity and FINRA data-use/retention rights before accepting any Reg SHO rows.
5. Keep Cboe OPRA as a conditional independent options-flow reconstruction source behind sample, PIT/correction-vintage, universe-coverage and license gates. Do not equate option volume or SLAN auction flow with informed institutional buying.
6. Keep CFTC TFF prospective-only until sufficient independent, timestamped events accumulate.

No return/event study, backtest, new OOS, bootstrap, LOO or holdout test was run. No signal admitted; incremental alpha demonstrated: **none**.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameter, exposure, cost, holding-period, holdout or production change. No workflow was dispatched, rerun, cancelled or duplicated.
