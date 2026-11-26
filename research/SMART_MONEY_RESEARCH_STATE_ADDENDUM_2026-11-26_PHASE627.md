# Smart Money Research state addendum — 2026-11-26 — Phase 627

**Audit cutoff:** 2026-11-26 00:50 UTC  
**Main HEAD:** `54c6e324b20e44307c9ed0244c70c9da3c8797fe`

## Actions and repository preflight

- Repository Actions census: 8,302 total runs; latest 100 inspected. No in-progress or queued runs.
- Latest run: Phase 626 PR #240, [45724525643](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45724525643), completed successfully. Offline regression passed **78/78**; live-capture was skipped. PR #240 remains Draft/open and unmerged.
- Latest natural Form 4 capture on main: [45714679017](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45714679017), both jobs successful; artifact [15069775951](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45714679017/artifacts/15069775951). The run appended 415 canonical metadata events and 912 entity observations; both 4/4-A feed watermarks passed. No issuer identity mismatches, unknown roles or quarantined accessions. The 415 new accessions did not have filing XML downloaded. Research-observation-eligible rows: 0; signal-eligible rows: 0.
- Latest natural Form 144 capture: [45693004404](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45693004404); offline and live jobs succeeded, with three unexpired artifacts. No new Form 144 economic or signal result was established in this audit.
- No workflow was dispatched, rerun, cancelled or duplicated.

## Phase 626 — Form 4 accession repetition versus entity duplication

Independent parsing of the production `entity_observations.csv` sidecar found:

- 912 entity-observation rows across 421 feed/accession groups and 417 unique accession values.
- 910 distinct strict entity keys; only **two exact repeated entity rows**, affecting two keys.
- 489 rows beyond the first entity row per accession are legitimate multi-entity expansion, not duplicates.
- Four repeated accession occurrences across feeds remain a separate accession-grain concept.
- The two exact repeats concern issuer and reporting-owner rows for accession `0001193125-26-477834`, observed at offsets 1200 and 1300 with different response hashes. Raw Atom page bodies were not retained, so the cause is unresolved; this is not proof of a pagination defect.

PR #240 adds an append-only `entity_duplicate_audit.csv` with strict parsed-entity keys and separate counts. The existing accession/entity ledgers, event selection, watermarks and signal eligibility are unchanged. The latest PR regression passed 78/78. Keep the PR unmerged until reviewed; the first natural post-merge capture must validate the new sidecar against live feed observations.

## SEC 13F prospective capture — schedule delivery gap

- The Phase 614/615 collector and full-snapshot safety correction are present on main (integration commit [4211242](https://github.com/jafelix81/NuevaEstrategia/commit/4211242af5a1967cea6b73c1658576fe4708e362)).
- Its workflow declares an hourly weekday schedule at minute 41. The latest 100 repository runs contain no Phase 614 scheduled run after integration, despite multiple eligible schedule slots; no active/queued run is visible.
- This is an observed delivery gap, **not proof that the workflow is disabled**. Workflow administrative enabled-state is not exposed by the available GitHub read interface. The workflow's manual mode is diagnostic-only and does not persist the append-only baseline.
- Human action: verify that **Phase 614 — SEC 13F first-seen prospective metadata capture** is enabled under GitHub Actions. If disabled, enable it; then allow its scheduled run to establish the baseline. Do not treat a manual diagnostic as a persistent capture.

## SEC 13D/G global-index sample — manual gate

- Phase 616 global-index discovery and the bounded 44-accession subject/filer identity sample are integrated on main (commit [b43d703](https://github.com/jafelix81/NuevaEstrategia/commit/b43d703cdc2d84a06965fe1ae7ffb65010f802b2)).
- Latest offline validation passed 30/30 combined tests plus 11/11 standalone Phase 485 parser tests. No live SEC sample was run.
- The workflow is intentionally manual-only and requires `run_live_sample=true`; it uses the existing `SEC_USER_AGENT` Actions secret and fails closed if absent. No secret value should be pasted into chat.
- The GitHub connection available in this run supports reading runs/jobs but not dispatching a workflow. Human action to advance this line: dispatch **Phase 616 — SEC 13D/G global-index bounded identity sample** once with `run_live_sample=true`. The resulting 44-header sample is only an identity/coverage gate, not authorization for a historical crawl, holdings download or return test.

## Research disposition

- No predictive signal, incremental alpha, event-return test, chronological OOS, bootstrap or LOO result was established.
- FINRA, CFTC, Form 4, Form 144, 13F, 13D/G, MIDAS and options hypotheses remain subject to their existing source-specific PIT, identity, coverage and licensing gates.
- No paid data, vendor quote, options request or purchase was made; options-data budget remains USD 0.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, exposure, costs, parameters, holdout or production strategy changes.
