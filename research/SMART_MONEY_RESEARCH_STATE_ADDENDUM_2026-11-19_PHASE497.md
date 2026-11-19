# Smart Money Research — state addendum, Phase 497 (2026-11-19)

## Completed
- Phase 497 live run [44487183018](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44487183018) completed successfully. Both offline regression and live audit passed; artifact [14511206505](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44487183018/artifacts/14511206505), ZIP SHA-256 `91582dc70925e0c3d9571a2eec246404eb6941c602301ac8d16afdf6bf50a8c5`.
- Re-fetched and parsed 637/637 immutable Phase 476 Form 4 ownership XML payloads.
- Found 145 non-derivative Table I P/A rows. 81 satisfy a structural-completeness screen (single reporting owner, direct ownership, filing-level 10b5-1=no, positive price/shares, transaction date <= filing date). The workflow calls these `high_specificity_manual_review_rows`, but that label overstates the evidence: this screen does not require open-market footnote language and does not prove discretion or exchange execution. Treat 81 only as a preliminary manual-review queue.
- P/A footnote diagnostics across all 145 rows: 93 rows had resolved references, 52 had none, zero unresolved; keyword counts: open-market 5, trust 28, Rule 10b5-1 9, compensation/vesting 2, employee plan 3. Counts are non-exclusive and not transaction adjudications.
- 122 transaction dates precede filing date; 23 are same-day. All 637 filings are dated 2026-11-18. First-seen is a collector upper bound, not exact public availability.
- No raw payloads, footnote text or transaction-level rows persisted.

## Decision
- Form 4 remains a conditional research source; research-observation eligible 0, signal eligible 0, alpha testing unauthorized.
- Next code/data gate: rename the misleading 81-row field and add aggregate cross-tabs of footnote evidence within the structural screen; then resolve effective-dated security-class/listing identity and historical F80 membership.
- Phase 453 confirms issuer symbol is submission-level and not a complete transaction security master. Phase 455 found only 5 exact issuer-filing-event matches among 224 events in its six-quarter sample against a static 335-symbol snapshot; historical membership remains unverified.
- Existing Phase 97 source ranking remains: Databento PIT Security Master (two-clock identity candidate), CRSP (inactive-security/return benchmark), Norgate (separate index-defined universe). No purchase or license assumed.

## Other sources
- FINRA parser fix from Phase 495 still requires a post-fix live capture to prove the facility-grain parser on real files.
- CFTC TFF and SEC Form 144 remain capture/availability workstreams, not admitted signals.
- Options/Cboe remains subject to history, PIT-vintage, coverage and licensing gates.

## Frozen controls
`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameters, holding period, capital, exposure, costs, holdout or production change. No forward returns, event study, OOS, bootstrap, LOO or holdout use in Phase 497.
