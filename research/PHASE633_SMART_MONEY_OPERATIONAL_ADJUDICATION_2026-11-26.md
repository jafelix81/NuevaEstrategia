# Phase 633 — Smart Money operational adjudication and post-merge gates

**Audit cutoff:** 2026-11-26 06:45 UTC  
**Main HEAD before checkpoint:** `99754d55cc63f972796f81b8dc4b060500e63391`  
**Disposition:** three auditability corrections were merged after offline regression; the next natural Form 4 poll is required to validate the new entity-duplicate sidecar in production. No new signal or alpha result.

## 1. Preflight

Reviewed recent Actions runs, jobs, logs, artifacts, open PRs, branches and research files before proceeding.

- Actions inventory: 8,314 total runs at preflight; latest 10 inspected.
- Explicit status queries: 0 in-progress and 0 queued.
- No workflow was dispatched, rerun, cancelled or duplicated.
- Main before this checkpoint: `99754d55cc63f972796f81b8dc4b060500e63391`.
- The latest Form 4 scheduled capture remains [run 45759597509](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45759597509); it predates the Phase 626 merge.

## 2. Three auditability changes merged

### Phase 626 — SEC Form 4 entity duplicate semantics

[PR #240](https://github.com/jafelix81/NuevaEstrategia/pull/240) merged as [`b43c562`](https://github.com/jafelix81/NuevaEstrategia/commit/b43c56297ec19fbde03cb38b11ae025ad5b21aeb).

- Adds an append-only `entity_duplicate_audit.csv` sidecar without changing existing accession/entity ledger schemas.
- Exact keys now require recognized feed `4`/`4A`, valid SEC accession format, recognized issuer/reporting role, nonzero numeric CIK and normalized non-empty entity name.
- Missing or malformed identity components remain unkeyed; no fuzzy matching.
- Repeated accession occurrences remain distinct from exact entity duplicates and legitimate multi-entity accessions.
- Latest PR regression [45769730992](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45769730992): **80/80 passed**; live capture skipped as intended.

Independent per-poll re-audit of the committed production ledger:

| Natural poll | Entity rows | Strict unique keys | Exact duplicate groups / extra rows |
|---|---:|---:|---:|
| [45714679017](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45714679017) | 912 | 910 | 2 / 2 |
| [45759597509](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45759597509) | 192 | 192 | 0 / 0 |

The earlier 912-row poll contained two exact repeated entity rows across offsets 1200/1300 for accession `0001193125-26-477834`. The later 192-row poll contains no exact repeated entity key within that poll. Do not compare the full append-only ledger across poll runs without scoping by `poll_run_id`: the same entity may legitimately be observed again in a later poll. The merged sidecar has not yet been validated by a natural post-merge capture.

### Phase 628 — SEC 13D/G identity documentation

[PR #241](https://github.com/jafelix81/NuevaEstrategia/pull/241) merged as [`03470ce`](https://github.com/jafelix81/NuevaEstrategia/commit/03470ceb6c379b5e67ba5b8a09232e50ca0641a0).

The module documentation now matches the implemented identity contract:
- master-index CIK/company name: candidate subject-company identity;
- SEC-HEADER SUBJECT COMPANY: verified subject identity;
- SEC-HEADER FILED BY: filing-entity identity;
- accession prefix: EDGAR login/submitter CIK;
- archive-path CIK: retrieval locator only.

The existing PR run [45733913256](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45733913256) passed 30/30 offline tests. The 44-document live sample was not run.

### Phase 618 — Form 144/Form 4 acceptance-clock diagnostics

[PR #235](https://github.com/jafelix81/NuevaEstrategia/pull/235) merged as [`99754d5`](https://github.com/jafelix81/NuevaEstrategia/commit/99754d55cc63f972796f81b8dc4b060500e63391).

The crosswalk summary now separately reports missing Form 144 acceptance timestamps, missing Form 4 acceptance timestamps, accession lists and unresolved acceptance-clock rows. This is diagnostic transparency only: it does not impute timestamps, certify public availability, change matching or admit signals. PR run [45602471386](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45602471386) passed 65/65 offline tests; live capture skipped.

## 3. Current source adjudication

### SEC Form 4 / Form 144

- Latest natural Form 4 run [45759597509](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45759597509): 90 new canonical accession events, 192 entity observations; both feed watermark/continuity gates passed.
- The 90 new metadata events have bounded observation intervals, not certified exact public-availability timestamps. Signal-eligible rows remain zero.
- The structured transaction ledger contains 340 rows. The Phase 632 triage remains controlling: P-coded rows are not automatically discretionary open-market purchases; the nine TEAM rows in the latest 37-row batch are under a Rule 10b5-1 plan and indirect trust ownership, while two XBP rows remain unresolved. All rows remain signal-ineligible.
- Form 144 proposed-sale notices are not executions. The descriptive crosswalk remains non-signal.

### SEC 13F / 13D/G

- Scheduled 13F run [45751086501](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45751086501): offline tests passed, but live capture failed closed because the injected `SEC_USER_AGENT` value was empty. The log confirms no SEC request was made and no ledger state advanced. Phase 629's code fix is already on main; secret availability remains a repository configuration blocker.
- The Phase 616 44-header 13D/G sample has not been executed. It requires a manual dispatch with `run_live_sample=true` after the existing SEC User-Agent secret is available. PR CI is not a substitute for the live sample.

### FINRA / CFTC

- FINRA Reg SHO run [45754121648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648): eight HTTP-200 files were all rejected by the fail-closed BCPC/TPC overlapping-facility duplicate gate. No raw volume was admitted; zero accepted files and zero eligible observations. Do not sum, drop or max-select rows without security/facility-grain reconciliation.
- CFTC TFF run [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471): 3,043 historical observations through 2026-11-17, no new reports or revisions, zero signal-eligible historical rows. Retain only as a possible broad positioning/regime covariate, not security-level institutional flow.

### Options, MIDAS and N-PORT

- Cboe OPRA/Open-Close and SEC MIDAS remain conditional feasibility candidates; exact frozen-universe coverage, historical first-receipt/correction vintages, licensing and reproducibility remain unverified. No sample, quote, license acceptance or purchase was made.
- MIDAS hidden volume is not dark/off-exchange institutional accumulation; retain only as a possible exchange-market-structure/liquidity-state feature after file-level PIT validation.
- The simple N-PORT aggregate share-balance-growth directional signal remains killed under Phase 526 due unstable/mostly negative dose-response evidence. N-PORT may remain descriptive holdings context, not a promoted signal.
- Options-data budget remains USD 0.

## 4. Phase 20C and strategy controls

- Phase 593 remains authoritative: same-day-close FINRA entry is NO-GO because the daily file is published after the regular session.
- The next-session successor remains untested. Phase 594 still identifies the missing Phase 469-to-468 first-seen label bridge and incomplete historical adjusted-price/terminal-return coverage for seven inactive/renamed/acquired names.
- No new incremental alpha, valid OOS, bootstrap or LOO result was produced.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, exposure, cost, parameter, holding-period, holdout or production change.

## 5. Next gates

1. Wait for the next natural scheduled Form 4 capture to validate `entity_duplicate_audit.csv` on live Atom pages; do not dispatch a duplicate poll.
2. Restore the exact repository Actions secret `SEC_USER_AGENT`; do not expose its value. Then run the bounded Phase 616 44-header sample once with `run_live_sample=true`.
3. Keep FINRA Reg SHO quarantined until BCPC/TPC are reconciled at the security/facility grain with authorized data and use rights.
4. Continue source-level PIT and universe coverage audits; do not run event returns until identity, public availability, delisted history and costs are frozen.

**Final result:** infrastructure and auditability improved; no new smart-money hypothesis has earned signal eligibility. F80 remains unchanged.
