# Smart Money Research state addendum — Phase 629 (2026-11-26)

- Actions preflight: 8,304 total runs; latest 100 = 70 success / 19 failure / 11 cancelled; zero in progress. Latest 69 scheduled runs show no SEC 13F / Phase 614 run after integration on main at commit 4211242 (2026-11-25 21:13:55 UTC). The connected read surface does not expose workflow enabled state; verify in GitHub Actions rather than assuming disabled.
- Phase 614 transport defect identified: the collector reuses the Phase 401 fetch helper's hard-coded module-level User-Agent and the workflow does not inject `SEC_USER_AGENT`. Phase 629 proposes secret injection, fail-closed validation before any SEC request, and offline tests for missing/placeholder/valid values. No secret value was read or printed and no live SEC request was made.
- Form 4 natural run 45714679017 succeeded with 415 new metadata events, 912 entity observations, 27 structured transaction rows and 33 footnote references appended by bounded backfills; zero research/signal eligibility. PR #240's exact-entity sidecar remains Draft/unmerged; live post-merge validation remains required.
- Form 144 natural run 45693004404 succeeded with 44 new events, 44 acceptance reconciliations, 723 cumulative accessions and 4,874 detail rows; public availability and signal eligibility remain uncertified.
- Phase 616 PR #241 offline regression passed 30/30; live 44-header sample remains unrun and requires explicit dispatch after review.
- No new alpha/OOS/bootstrap/LOO result. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. Options-data budget USD 0.
