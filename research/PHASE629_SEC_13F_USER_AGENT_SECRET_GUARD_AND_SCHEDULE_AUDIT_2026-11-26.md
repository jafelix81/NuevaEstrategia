# Phase 629 — SEC 13F User-Agent secret guard and schedule audit

**Audit cutoff:** 2026-11-26 02:39 UTC  
**Base:** main at the start of this audit; this change is proposed on `phase629-sec13f-user-agent-secret-guard-20261126`.  
**Decision:** correct the 13F transport contract before relying on prospective capture. No live SEC request, workflow dispatch, holdings download, return test or model change was performed.

## 1. Actions preflight

- Repository Actions API reports 8,304 total runs; latest 100 contain 70 success, 19 failure and 11 cancelled; zero runs are currently in progress.
- The latest scheduled run list contains 69 runs. The newest natural SEC capture runs are Form 4 [45714679017](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45714679017) and Form 144 [45693004404](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45693004404). No Phase 614 / SEC 13F run appears in the returned scheduled-run history or the latest 100 repository runs.
- Phase 614 was integrated into main by [commit 4211242](https://github.com/jafelix81/NuevaEstrategia/commit/4211242af5a1967cea6b73c1658576fe4708e362) at 2026-11-25 21:13:55 UTC. Its workflow declares `41 * * * 1-5`, but no scheduled execution is visible after integration.
- The connected read surface does not expose the workflow enabled/disabled administration field. Therefore the absence of runs is verified; the cause (disabled workflow, schedule delivery delay, or another GitHub-side state) is not asserted. A maintainer should verify that Phase 614 is enabled in Actions.

## 2. Material transport-contract defect

Phase 614 calls `phase401_form144a_full_parent_identity_census.fetch_bytes`. The shared helper currently uses a module-level hard-coded `SEC_UA` string. The Phase 614 workflow did not inject the repository's `SEC_USER_AGENT` secret into the live-capture environment, and the Phase 614 CLI did not validate it before network access.

This bypassed the repository's intended secret-backed SEC access contract even though the project contact was non-placeholder. It also meant the configured secret could not govern this collector.

## 3. Proposed correction

- Inject `secrets.SEC_USER_AGENT` only into the Phase 614 live-capture step.
- Validate that the value is non-empty, descriptive and contains a contact email before calling the collector.
- Set the shared Phase 401 transport helper's User-Agent only after validation; never print or persist the secret.
- Fail closed before any SEC request if the secret is absent or placeholder-like.
- Add offline regressions for missing, placeholder and valid values.
- Keep the scheduled metadata-only capture and manual diagnostic behavior unchanged. Manual mode remains non-persistent; no filing bodies or holdings are downloaded.

## 4. Latest natural capture evidence

### Form 4 — run 45714679017

Both offline and live jobs succeeded; artifact [15069775951](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45714679017/artifacts/15069775951) was downloaded and inspected.

- 415 new canonical accession metadata events.
- 912 entity observations; both Form 4 and Form 4/A watermarks passed.
- 491 repeated accession occurrences are accession-grain observations, not exact duplicate entity rows.
- 27 structured transaction-detail rows and 33 transaction-linked footnote references were appended in bounded backfills; filing XML was not persisted.
- Zero research-observation-eligible and zero signal-eligible rows.

PR [#240](https://github.com/jafelix81/NuevaEstrategia/pull/240) proposes a separate exact-entity duplicate sidecar and passed 78/78 offline tests, but remains Draft/unmerged. Its live capture was skipped. The natural run above therefore does not validate the proposed sidecar in production.

### Form 144 — run 45693004404

Both offline and live jobs succeeded; artifacts [15058663926](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45693004404/artifacts/15058663926) and [15060285064](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45693004404/artifacts/15060285064) were downloaded and inspected.

- 44 new metadata events and 44 acceptance-index reconciliations.
- Cumulative structured ledger: 723 accessions / 4,874 detail rows.
- No unresolved acceptance reconciliations or source-hash mismatches in this run.
- Public availability is not certified; zero signal-eligible rows.

### SEC 13D/G — Phase 616

PR [#241](https://github.com/jafelix81/NuevaEstrategia/pull/241) remains Draft. Latest offline run [45733913256](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45733913256) passed 30/30; live sample was skipped. The preregistered 44-header sample has not run.

## 5. Research disposition

No new alpha, OOS, bootstrap or LOO result. No signal is admitted. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No changes to universe, exposure, costs, holding-period policy, capital or production. Options-data budget remains USD 0.
