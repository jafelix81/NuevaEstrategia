# Smart Money Research — state addendum, Phase 497 (2026-11-19)

## Completed
- Phase 497 live run [44487183018](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44487183018) completed successfully. Both offline regression and live audit passed; artifact [14511206505](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44487183018/artifacts/14511206505), ZIP SHA-256 `91582dc70925e0c3d9571a2eec246404eb6941c602301ac8d16afdf6bf50a8c5`.
- Initial run 44487183018 re-fetched and parsed 637/637 immutable Phase 476 Form 4 ownership XML payloads. Repeat run 44492496082 retrieved/parsed 636/637 (one submission unavailable); its artifact does not expose the failed accession. The second run reproduced 145 P/A rows and 81 structural-queue rows but is not a complete independent replication.
- Found 145 non-derivative Table I P/A rows. 81 satisfy a structural-completeness screen (single reporting owner, direct ownership, filing-level 10b5-1=no, positive price/shares, transaction date <= filing date). The current output uses `structural_completeness_queue_rows`; an earlier overclaiming `high_specificity_manual_review_rows` label is retired. This screen does not prove discretion or exchange execution.
- P/A footnote diagnostics across all 145 rows: 93 rows had resolved references, 52 had none, zero unresolved; keyword counts: open-market 5, trust 28, Rule 10b5-1 9, compensation/vesting 2, employee plan 3. Counts are non-exclusive and not transaction adjudications.
- 122 transaction dates precede filing date; 23 are same-day. All 637 filings are dated 2026-11-18. First-seen is a collector upper bound, not exact public availability.
- No raw payloads, footnote text or transaction-level rows persisted.

## Decision
- Form 4 remains a conditional research source; research-observation eligible 0, signal eligible 0, alpha testing unauthorized.
- Repeat-run cross-tab (636/637 parsed): 34 structural-queue rows had footnote references, 47 had none; 2 had an open-market keyword only and 79 had neither open-market nor private-purchase keywords. This is provisional because one filing was unavailable; the artifact does not identify it. Next gate is full-cohort repeatability/failure traceability, then effective-dated security-class/listing identity and historical F80 membership.
- Phase 453 confirms issuer symbol is submission-level and not a complete transaction security master. Phase 455 found only 5 exact issuer-filing-event matches among 224 events in its six-quarter sample against a static 335-symbol snapshot; historical membership remains unverified.
- Existing Phase 97 source ranking remains: Databento PIT Security Master (two-clock identity candidate), CRSP (inactive-security/return benchmark), Norgate (separate index-defined universe). No purchase or license assumed.

## Other sources
- FINRA parser fix from Phase 495 still requires a post-fix live capture to prove the facility-grain parser on real files. The next scheduled FINRA window is later on 2026-11-19; no post-fix live result is yet established at this review.
- CFTC TFF and SEC Form 144 remain capture/availability workstreams, not admitted signals.
- Options/Cboe remains subject to history, PIT-vintage, coverage and licensing gates.

## Frozen controls
`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameters, holding period, capital, exposure, costs, holdout or production change. No forward returns, event study, OOS, bootstrap, LOO or holdout use in Phase 497.


## Subsequent SEC Form 4 metadata poll
- Main's scheduled Phase 476 run [44505739718](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44505739718), artifact [14519048458](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44505739718/artifacts/14519048458), completed at 2026-11-19 10:27:06 UTC.
- Added 18 new canonical Form 4 events from 37 new accession occurrences; 19 within-feed repeats and zero cross-feed repeats. All 18 new events have bounded metadata intervals. No filing XML was downloaded; no observations or signals were admitted.
- These 18 events are a new, unaudited cohort, not part of the immutable 637-accession Phase 497 cohort.

## Operational review
- Main at review: `00af77cfc37446a4854caafdfeb2feb640a07256` (the scheduled Phase 476 metadata-ledger commit).
- Latest Actions page reports 7,884 runs; no active or queued run was present in the first 100 latest-run records.
- The Phase 497 branch is 10 commits ahead and 1 behind main; its changes are additive research/workflow files and do not modify the append-only main ledger.
- The Phase 497 workflow now runs live SEC retrieval only on explicit `workflow_dispatch` or a push commit message containing `[run-live]`; documentation/PR updates will not automatically refetch the 637 documents.
