# Smart Money Research State Addendum — Phase 657 (2026-11-27)

**Mainline documentation:** [Phase 657 report](PHASE657_SEC_13DG_SUBJECT_VS_FILER_FORM_FAMILY_CROSSTAB_2026-11-27.md) · [JSON summary](PHASE657_SEC_13DG_SUBJECT_VS_FILER_FORM_FAMILY_CROSSTAB_2026-11-27.json)

## New research finding — SEC 13D/G role × form split

- Recomputed the form-family cross-tab from the immutable Phase 603 artifact (147 verified header rows; artifact ZIP SHA-256 is recorded in the report).
- Current-F80 **subject** matches: 24; current-F80 **FILED BY** matches: 45; both: 2; subject-only: 22; filer-only: 43.
- Sixteen of the 22 subject-only rows are 13D/13D-A; 32 of the 43 filer-only rows are 13G/13G-A. Both-role overlaps occur only in two 13G-family rows.
- This reinforces issuer-role separation and makes issuer-side 13D content classification the next research priority. The sample is deliberately stratified, not representative; this is not a prevalence estimate or evidence of alpha.
- Initial 13D filings and 13D/A state changes must remain separate. 13G/13G-A remains ownership-state context, not a directional signal by definition.

## Latest operational evidence rechecked

- FINRA run `45939887443`: both jobs successful; seven partial bootstrap files, one 403, 14 duplicate symbol-date groups (BCPC/TPC), 28 row occurrences quarantined, zero first-seen/research/signal-eligible observations. Raw rows and volume values were not persisted.
- Form 144 run `45940802895`: both jobs successful; 53 feed observations, no new accessions, 10 bounded backfills adding 58 detail rows; ledger 845 accessions / 5,595 detail rows; zero signal-eligible rows.
- Form 4 run `45917890802`: both jobs successful; 10 accessions parsed, 13 owner rows appended, 14 crosswalk rows across 12 matched accessions; zero signal-eligible matches.
- 13F run `45910142871`: both jobs successful; 29 existing accession observations, zero new accessions, no holdings downloaded.
- Phase 616 offline CI run `45614747438`: 30/30 tests passed; the live-sample job was skipped. No 44-accession live sample has been run.

## Phase 616 human prerequisite

The merged manual-only workflow is `.github/workflows/phase616_sec_13dg_global_index_discovery.yml`; it requires `workflow_dispatch` with `run_live_sample=true`. The collector fails before any SEC request unless `SEC_USER_AGENT` contains a valid monitored contact email and is not a placeholder. The latest observed 13F run log exposed an empty `SEC_USER_AGENT` environment; the Phase 603 pilot instead used the shared Phase 401 fallback. This does not prove the secret's current state, but if it remains empty the Phase 616 job will stop before making requests.

The connected GitHub action set available in this run does not expose workflow dispatch or secret inspection/set operations. Human step if the live sample is to proceed: confirm/set the repository Actions secret `SEC_USER_AGENT` with a monitored contact, then dispatch the Phase 616 workflow once with `run_live_sample=true`. Do not paste the value into chat. The sample is limited to 44 headers across five preregistered quarters; it does not authorize a full crawl or event study.

## Repository / branch controls

- Latest relevant mainline research snapshot before Phase 657 was Phase 656; no active run was found among the latest relevant run records inspected.
- Branch census: 407 branches over five pages. No new branch or workflow was created in this phase.
- PR #233 (Phase 616) is merged. PR #220 (Phase 604 current fund ticker mapping, 328/335) remains Draft/unmerged; its mapping is a current snapshot, not historical PIT membership.
- No manual workflow dispatch, rerun, schedule change or duplicate capture was made.

## Frozen controls

- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No signal promoted; no incremental alpha demonstrated.
- No prices/forward returns inspected; no event study, OOS, bootstrap, LOO or holdout test run.
- No production, universe, parameters, exposure, costs, capital or holding-period rules changed.
- No paid data, vendor contact, quote request or purchase; budget remains USD 0.
