# Phase 639 — SEC Form 144 Atom timestamp timezone guard and integration preflight

**Audit cutoff:** 2026-11-26 10:55 UTC  
**Base:** `main` at `fa0d05d49c656054032d9472d5cb3cf0f7da2ad1`  
**Branch:** `phase639-form144-atom-timestamp-tz-guard-20261126`  
**Disposition:** fail closed on timezone-naive SEC Atom `updated` values; document the separate stacked-branch integration blocker. No live SEC request, signal, return test or strategy change.

## 1. Latest Actions evidence checked

- Latest accessible run in this audit: Phase 638 PR validation [45805390010](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45805390010).
- Jobs: `offline-regression` completed successfully; `live-capture` was skipped as designed for a pull-request event.
- The run uploaded only the descriptive Phase 560 artifact [15108454734](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45805390010/artifacts/15108454734), created 2026-11-26 10:52:49 UTC. No SEC capture occurred.
- Phase 638 PR [#244](https://github.com/jafelix81/NuevaEstrategia/pull/244) is merged at `1c9f6bb0bcfadf6429c433c271f322e3cebd1309`; its 82/82 offline tests passed.
- The connected GitHub read surface used for this run exposes commit/PR/run-specific jobs and artifacts, but not a repository-wide Actions-run listing or workflow enabled-state. The most recent full schedule inventory remains the Phase 638 cutoff at 10:53 UTC: 0 queued / 0 in progress and no post-cutoff natural SEC capture. This is a delivery gap, not proof that workflows are disabled.
- No workflow was dispatched, rerun, cancelled or duplicated.

## 2. Phase 639 finding — timezone-naive Atom timestamps

The main-branch Form 144 collector's `parse_utc` previously assigned UTC to a timezone-naive Atom `updated` value. The Form 4 collector already rejects naive timestamps and its regression suite explicitly checks that behavior.

A naive timestamp has no defensible UTC offset. Treating it as UTC silently manufactures chronology and can corrupt feed ordering and timing diagnostics. This is not the first-seen interval clock itself—the Form 144 first-seen upper bound remains the actual response-received time—but it is an avoidable timestamp-integrity inconsistency.

### Change proposed

- Return `None` for a parsed datetime without an explicit timezone/UTC offset.
- Preserve the raw Atom value for audit.
- Leave normalized `feed_updated_utc` blank when the offset is absent.
- Add a regression proving that a naive `updated` value is not silently converted to UTC.
- Keep all existing acceptance, first-seen interval, eligibility and no-signal rules unchanged.

The PR workflow is expected to run offline regression only; the Form 144 live-capture job is skipped for pull-request events.

## 3. Form 144 data interpretation retained

The latest audited natural ledger remains the Phase 638 source:
- 815 filing headers / 5,443 detail rows.
- 807 bounded research-observation-eligible headers.
- 8 expected `INITIAL_BASELINE_NO_LOWER_BOUND` headers quarantined.
- 0 malformed intervals.
- 0 research-eligible headers with invalid intervals.
- 0 exact public-availability certifications.
- 0 signal-eligible headers.

The eight bootstrap rows remain quarantined. A Form 144 remains a proposed-sale notice, not proof of execution. The timestamp hardening does not promote any filing.

## 4. SEC 13F integration readiness — material repository blocker

The 13F feasibility work is substantial, but its PR chain is not merge-ready against current `main`:

| PR / branch layer | Current evidence |
|---|---|
| PR #6, Phase 45 root | Draft; `mergeable=false`; base SHA `fd9bdca` |
| PR #8, Phase 47 root | Draft; `mergeable=false`; 21 commits ahead and 587 behind current main |
| PR #221–230 | Draft stacked chain; each branch is mergeable against its immediate predecessor, not independently based on current main |
| Final Phase 613 branch | 137 commits ahead / 587 behind current main; compare status `diverged` |

All ten stacked PR head checks were observed as completed successfully. Recorded run IDs:
- #221: 45520284969
- #222: 45529146664
- #223: 45531824788
- #224: 45532614924
- #225: 45533082921
- #226: 45533511354
- #227: 45533810347
- #228: 45538436225
- #229: 45538905972
- #230: 45546003346

The 13F branch chain must be rebased/rebuilt against current `main` and revalidated before integration. Do not merge PR #230 directly or infer that its `mergeable=true` against Phase 612 means it is mergeable into current main. The current comparison shows the full stack adds 51 files relative to its old merge base; the large behind count makes a direct merge or force update unsafe.

Research value remains conditional: 13F has strong historical structural joins and acceptance-time feasibility, but no complete effective-dated F80 security mapping, no merged as-of holdings panel, no prospective first-seen series, and no event/OOS evidence. It is not yet a holdings signal.

## 5. SEC 13D/G integration readiness

PR #37 remains Draft and is based on `phase347-13dg-cusip-integrity-audit`. The current Phase 350 branch compares as 292 commits ahead / 565 behind `main`; the Phase 347 base branch compares as 262 ahead / 565 behind. This is another stacked historical branch chain requiring a deliberate rebase/port, not a direct merge.

The 43/44 parent-retrieval and identity results remain descriptive only. Five CUSIP mismatches and six missing parent CUSIPs remain quarantined; first-publication clocks and effective-dated security mapping are not complete.

## 6. Strategy and spending controls

- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No signal, return/event study, alpha, OOS, bootstrap or LOO result was produced.
- No universe, exposure, cost, capital, parameter, holdout or holding-period change.
- Options-data budget remains USD 0; no quote, vendor contact, trial or purchase.
