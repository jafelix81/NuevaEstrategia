# Smart Money Research — Phase 684 state addendum (2026-11-28)

Full audit: [Phase 684 — source reconciliation and FINRA rights-hold enforcement](PHASE684_SMART_MONEY_SOURCE_RECONCILIATION_AND_FINRA_RIGHTS_HOLD_ENFORCEMENT_2026-11-28.md)

- **Actions preflight:** 8,409 total runs; latest 100 = 80 success / 16 failure / 4 cancelled; 0 active / 0 queued. 86 open PRs. No duplicate dispatch or rerun.
- **Main:** Phase 469 direct-FINRA-CDN schedule removed in commit `066380e1e3c018aab9fcf02113f4d8076402add2`. Manual live capture now requires `rights_clearance_confirmed=true`; offline regression remains. This enforces Phase 683's conservative rights hold; it is not a legal finding of breach and not an API migration.
- **Form 144:** run 46155351208 succeeded. 52 feed observations are poll rows, not new accessions. Canonical event ledger remains 1,104 accessions. Ten old accessions gained 49 detail rows; structured ledger 986 accessions / 6,409 rows; 118 pending. Formal plan dates 391; public availability certified 0; signal eligible 0.
- **Form 4:** run 46099559273 captured 156 new bounded metadata accessions. Entity reconciliation: 149 single-owner filings, seven multi-owner filings; these are not 156 verified trades. Research/signal eligible 0. Crosswalk: 17 proposed-sale matches / 16 Form 4 accessions / 12 issuers / 16 owners; two acceptance clocks unresolved; signal matches 0.
- **13F:** latest natural capture 46084129349 found four new metadata accessions; no holdings downloaded; signal eligible 0. PR #262 remains draft stacked on #230.
- **FINRA Reg SHO:** run 46105917821 retained 327 unique-symbol observations for one date after duplicate-symbol quarantine; zero signal-eligible rows. Direct CDN schedule is paused.
- **CFTC:** run 46105422375; 3,043 rows, no new signal-eligible history.
- **13D/G:** Phase 603's 147/147 header-identity pilot is a discovery result only. Phase 616's 44-accession/five-quarter live sample remains skipped; PR #219 is draft and manual dispatch with `run_live_sample=true` plus `SEC_USER_AGENT` is still required.
- **Other source gates:** SEC MIDAS has a 2012 Q1–2026 Q3 catalog but no certified per-quarter release clocks or permanent IDs; OCC Volume Query has 96.27% coverage at two recent dates but only 24 months and no buy/sell/open/close semantics; SEC FTD lacks a historical active-universe/zero-vs-inactive bridge; paid OPRA sources remain outside the USD 0 budget; N-PORT short rows remain sparse and poorly mapped.
- **Phase 20C:** still no-go because signal-date-close entry is not executable after the post-close FINRA release. Branch is 12 ahead / 828 behind main; not merged or rerun.

**Disposition:** zero signals promoted; no incremental alpha, new OOS, bootstrap or LOO demonstrated. Holdout untouched. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No paid data spend.
