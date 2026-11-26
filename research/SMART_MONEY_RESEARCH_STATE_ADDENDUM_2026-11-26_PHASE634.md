# Smart Money Research state addendum — Phase 634 (2026-11-26 07:51 UTC)

**Main HEAD before checkpoint:** `367533fff72fb6068667ed50d9754e40a61a49a3`  
**Phase 634 report commit:** `a4cae0f02a2aaac5a0c575f4917c59e17c14fcbf`

- Actions preflight: 8,316 total runs; latest 100 inspected; 0 queued/in-progress; no dispatch or rerun.
- Form 4 natural run 45759597509 predates Phase 626 merge. Artifact: 90 canonical issuer events, 192 entity observations, 37 detail rows, 66 transaction-linked footnote references plus 26 additional footnote-reference rows, 10 filing-level owner rows, 0 signal-eligible matches. Latest PR check 45769730992 passed 80/80 offline; live capture skipped. Natural post-merge validation of `entity_duplicate_audit.csv` remains pending.
- Form 144 run 45747356670: 82 new first-seen events / 105 feed observations; 815 accessions / 5,443 detail rows; 188 bounded detail backfills remain. Phase 549 negative-control refresh: 295 formal plan-date accessions, 23 positive explicit plan mentions, four negative explicit mentions, three ambiguous; sell-to-cover/tax-withholding control remains non-signal. Signal-eligible count 0.
- FINRA Reg SHO run 45754121648: 8/8 HTTP-200 files rejected; 16 duplicate extra-row occurrences across BCPC/TPC; raw volume not persisted; zero eligible.
- CFTC TFF run 45753716471: 3,043 rows across four index futures through 2026-11-17; no new report/revision; weekly features suppressed by semiweekly/irregular cadence; no signal.
- SEC 13F: main-branch prospective metadata collector only. Historical structural/acceptance/session/legal-clock PR chain #221–#230 remains Draft/unmerged. Full-quarter structure and 48/48 acceptance-page sample are promising feasibility evidence, but effective-dated security mapping and amendment-state integration remain open.
- SEC 13F scheduled run 45751086501 failed closed because `SEC_USER_AGENT` was empty; no SEC request/state write. Workflow references repository `secrets.SEC_USER_AGENT` and declares no Environment. Check repository-secret scope if the value is stored elsewhere.
- SEC 13D/G: Phase 603 147-document role-aware sample passed but is stratified/non-representative; Phase 616's 44-header sample remains unrun and requires manual `workflow_dispatch` with `run_live_sample=true`.
- Options/MIDAS remain conditional feasibility only; no sample, quote, license acceptance, vendor contact or purchase. Options budget USD 0.
- N-PORT aggregate share-balance-growth standalone signal remains killed (Phase 526). Phase 20C same-day-close remains NO-GO; next-session retest is blocked by label/price coverage. MOM120 standalone incremental promotion remains rejected (Phase 499); Phase 574 is historical sensitivity only.
- No new alpha, valid incremental OOS, bootstrap or LOO result. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- Full audit: [Phase 634](PHASE634_SMART_MONEY_SOURCE_GATE_AND_POSTMERGE_CAPTURE_AUDIT_2026-11-26.md).
