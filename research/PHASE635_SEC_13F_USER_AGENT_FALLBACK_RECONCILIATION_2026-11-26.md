# Phase 635 — SEC 13F User-Agent fallback reconciliation

**Audit cutoff:** 2026-11-26 08:44 UTC  
**Base main HEAD:** `38c558ab1b5beba1b483922945854531d091f6ac`  
**Branch:** `phase635-sec-user-agent-shared-fallback-20261126`  
**Disposition:** merged the fallback correction while retaining fail-closed SEC identification. Offline regression passed 37/37; no live SEC request or model test was run in this phase.

## 1. Actions preflight and artifact review

Reviewed the most recent run evidence available in the repository state and fetched current job/step details and logs for the relevant runs:

- SEC 13F scheduled run [45751086501](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45751086501): offline regression succeeded; live-capture failed at `configure_sec_user_agent()`. The job log explicitly shows `SEC_USER_AGENT` empty and `RuntimeError: SEC_USER_AGENT is missing or invalid; no SEC request was made.` The metadata commit step was skipped and no artifact was produced.
- Form 4 natural capture [45759597509](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45759597509): both jobs succeeded; artifact [15089685727](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45759597509/artifacts/15089685727) exists. This run predates the Phase 626 merge, so it does not validate the new post-merge duplicate sidecar.
- FINRA Reg SHO [45754121648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648): both jobs completed successfully, but the artifact [15086513251](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648/artifacts/15086513251) records eight files rejected by the BCPC/TPC duplicate/facility-grain gate.
- CFTC TFF [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471): prospective capture succeeded; artifact [15086462804](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471/artifacts/15086462804) preserves 3,043 historical rows with no new report/revision.
- Latest Form 4 PR check [45769730992](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45769730992): offline regression passed 80/80; live capture was skipped as designed.

The Phase 634 repository-wide Actions snapshot reported zero queued/in-progress runs at its 07:51 UTC cutoff. No workflow was dispatched, rerun, cancelled or duplicated in this phase.

## 2. Root cause and reconciliation

Phase 614 currently requires `secrets.SEC_USER_AGENT` and fails closed if it is absent. The scheduled log confirms that the secret was injected as an empty environment variable.

A separate SEC 13F acceptance-time audit (PR #228 / Phase 611) already uses a shared resolver that prefers the repository secret and falls back to the established Form 144 project contact. That fallback is not a credential; it is the same project contact already used by the repository's SEC transport helper, `phase401_form144a_full_parent_identity_census.SEC_UA`.

The earlier Phase 611 fallback does **not** automatically apply to the Phase 614 prospective collector. They are separate workflows and code paths. This explains why a successful Phase 611 live sample can coexist with a failed Phase 614 scheduled capture.

## 3. Correction proposed

- Prefer a valid `SEC_USER_AGENT` repository secret when present.
- If the secret is absent or placeholder-like, reuse the existing, already-declared `phase401.SEC_UA` project contact.
- Validate either value for a descriptive User-Agent and contact email before any SEC request.
- Fail closed if neither source is valid.
- Never print or persist the User-Agent.
- Preserve the existing hourly weekday schedule, metadata-only capture, append-only state and manual non-persistence behavior.

Regression coverage now checks missing-secret fallback, placeholder-secret fallback, valid-secret override and failure when both sources are invalid.

## 4. Research and model controls

This is an operational transport correction only. It does not certify 13F filing availability, manager identity, security identity, historical F80 membership or amendment state. The 13F metadata collector still emits no research-eligible or signal-eligible rows.

- No 13F holdings were downloaded.
- No historical return, event study, alpha, OOS, bootstrap or LOO test was run.
- SEC 13F historical PIT/identity PR chain #221–#230 remains Draft/unmerged.
- SEC 13D/G 44-header parent retrieval remains a separate gate.
- FINRA Reg SHO remains quarantined; CFTC remains a possible broad-market regime covariate only.
- Options/data-purchase budget remains USD 0.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, exposure, costs, parameters, holdout or production changes.

## 5. Merge and next validation

- [PR #243](https://github.com/jafelix81/NuevaEstrategia/pull/243) was merged into main as commit [`11c2f1a`](https://github.com/jafelix81/NuevaEstrategia/commit/11c2f1acb578784456bc30f82f131ed8fb858c32).
- Hosted PR run [45786202161](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45786202161) passed **37/37 offline tests**. Its live-capture job was skipped as designed; no SEC request was made by that PR run.
- The next naturally scheduled Phase 614 poll must confirm that the established project-contact fallback is applied without exposing it in logs and that all four SEC Atom feeds complete. Do not manually dispatch a duplicate poll.
