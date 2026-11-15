# Phase 424 — SEC capture cadence and 13D/G access-gate recheck

**Audit time:** 2026-11-15 22:06 UTC  
**Disposition:** SEC Form 144 remains technically healthy per completed poll, but hourly delivery is not demonstrated; SEC 13D/G parent retrieval remains blocked pending a repository Actions secret. No source or signal admitted.

## 1. Actions/repository preflight

- Main HEAD: `0615d8738bc83ef09e4b3cd5717752821103f36b`.
- Latest 100 Actions runs: 7,659 total reported; 62 success, 37 failure, 1 cancelled; no queued/in-progress/waiting/requested runs in the latest page.
- Inspected all 261 branches across three pages, 56 open PRs, 63 workflow files, latest run jobs/logs/artifacts and relevant research state.
- No workflow was dispatched or rerun; no PR was merged or modified.
- Latest visible SEC Form 144 run remains [43743993846](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43743993846), successful on both jobs. Offline regression 15/15; live receipt 17:58:03Z; 55 feed-observation rows (50 Form 144 + 5 Form 144/A); zero new accessions/events/candidate matches; no feed-window gap; artifact [14173342433](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43743993846/artifacts/14173342433).

## 2. SEC Form 144 — hourly delivery still unproven

Mainline workflow `.github/workflows/phase403_sec_form144_first_seen_capture.yml` contains `cron: "37 * * * *"`.

The workflow-specific schedule query returned 13 schedule runs in total. The latest three were:
- 2026-11-15 03:01:47Z
- 2026-11-15 11:27:32Z
- 2026-11-15 17:57:31Z

The two intervals are 8h25m45s and 6h29m59s, not hourly. As of 22:06Z, no schedule run had appeared for the expected :37 slots at 18:37, 19:37, 20:37 or 21:37Z. The latest live-capture log confirms that the 17:57Z run fetched both feeds, appended the 55 observation rows, pushed the append-only ledger/state commit and uploaded its artifact.

This is an observed delivery gap, not proof that GitHub has permanently disabled the schedule. GitHub scheduled runs can be delayed or dropped; the next :37 slot had not yet arrived at audit time. **Do not manually dispatch, create duplicate polls or change the cron solely from this observation.** Until cadence is stable, first-seen timestamps remain interval-censored by the actual successful poll times, not by nominal cron slots.

## 3. CFTC TFF — mainline schedule is correctly activated

- PR [#60](https://github.com/jafelix81/NuevaEstrategia/pull/60) is merged into `main` (2026-11-14 00:45Z).
- Mainline workflow `.github/workflows/phase384_cftc_tff_prospective_capture.yml` contains weekday schedule `15 22 * * 1-5`.
- The latest run [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200) was a branch-push bootstrap, not a scheduled prospective capture. Its job passed 11/11 tests, read 3,035 historical rows, preserved `BASELINE_ALREADY_EXISTS_NO_OVERWRITE`, and produced zero eligible historical rows. Artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705).
- Sunday 2026-11-15 has no weekday schedule slot. The next expected run is Monday 2026-11-16 22:15 UTC after the CFTC's scheduled 20:30 UTC release. No duplicate or manual run was launched.

## 4. SEC 13D/G — exact human unblock remains outstanding

PR [#37 — Phase 350](https://github.com/jafelix81/NuevaEstrategia/pull/37) remains open and draft, based on `phase347-13dg-cusip-integrity-audit`. It contains an immutable manifest of 44 explicit parent accession references.

The prior run [43327053770](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43327053770) passed 10 offline tests but stopped on the first SEC Archives request with HTTP 403: 1 request attempted, 0 raw parent documents saved, 0/44 retrieved. The run correctly stopped rather than continuing requests. PR #37 still documents that the project-URL-only User-Agent lacks a monitored contact email.

**Required human action:** add/update repository secret `SEC_USER_AGENT` under **Settings → Secrets and variables → Actions**, with a project identifier and a monitored contact email. Do not put the email in chat. Secrets cannot be read back through this audit, so their current value cannot be independently verified. No SEC retry should occur until the secret is confirmed by the repository owner; after it is set, the exact-parent retrieval can resume at the existing 2 requests/second throttle.

## 5. Other research gates

- Form 4: SEC quarterly schema/history and accession-level PIT are feasible, but the historical frozen-universe issuer/security identity coverage previously measured at 54.6% (2016 Q1), 65.4% (2020 Q1), 76.4% (2024 Q1) and 83.3% (2026 Q3) is insufficient for a stable full-universe return test. See [Phase 39 feasibility](https://github.com/jafelix81/NuevaEstrategia/blob/main/research/PHASE39_SEC_FORM4_INSIDER_FEASIBILITY_2026-10-26.md) and [Phase 346 legacy identity bridge PR](https://github.com/jafelix81/NuevaEstrategia/pull/35).
- FINRA Phase 20C remains blocked at 328/329 valid price histories; no provider mixing, universe reduction or paid data acquisition was made.
- Obscura Flow Metrics remains conditional due conflicting public PIT semantics, unknown upstream lineage/history/coverage and lack of row-level sample. No account, trial, contact or purchase.

## 6. Research controls

- No new source or signal admitted.
- No forward-return, alpha, OOS, bootstrap, LOO or holdout test.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, holdout, capital, exposure and production remain unchanged.
- No vendor purchase/contact, secret write, workflow modification, manual dispatch or PR change.
