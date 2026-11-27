# Smart Money Research State Addendum — Phase 660 (2026-11-27)

## Form 4 code-P cohort update

- Latest natural Form 4 run 45976055356 succeeded. It appended 48 structured transaction-detail rows, 65 linked footnote references, 60 separate footnote references and 10 owner rows, but found zero new accessions and zero new canonical event rows.
- The current ledger snapshot has 314 transaction rows across 150 accessions; the owner sidecar has 147 rows across 130 accessions.
- Code-P cohort: 89 transaction rows, 59 accessions and 45 symbol values (44 excluding N/A). Ten issuer-symbol clusters have multiple accessions; four filings are multi-owner. Three code-P accessions lack owner sidecars (ECF, BG and HBCP), all outside the static F80 snapshot.
- Exact symbol match to the immutable 335-ticker reference: 3 code-P accessions / 11 rows / 2 symbols only — UPST (2 accessions, one issuer cluster) and TEAM (one 9-row filing, affirmative filing-level 10b5-1 negative control).
- UPST remains the only non-10b5-flagged issuer cluster in the static-F80 intersection. This is not evidence of open-market execution or discretionary intent; SEC code P includes open-market or private purchases.
- No code-P row is research- or signal-eligible. Filing-level owner sidecars do not verify transaction-line attribution, and the static F80 snapshot does not establish historical membership.

## Decision

P_CODE_CONTEXT_ONLY_NO_PROMOTION. Keep UPST descriptive only; do not run an event study until venue/semantics, security-class identity, conservative availability and effective-dated F80 membership gates pass. The sample is not representative and does not establish incremental alpha.

## Controls

- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- No prices/forward returns, event study, OOS, bootstrap, LOO or holdout inspected in Phase 660.
- No strategy/production changes, vendor contact or data purchase; budget USD 0.
