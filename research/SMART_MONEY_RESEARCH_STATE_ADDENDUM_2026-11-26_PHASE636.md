# Smart Money Research state addendum — Phase 636 (2026-11-26)

- **Main baseline:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- **Phase 635:** PR #243 merged; Phase 614 now prefers a valid `SEC_USER_AGENT` secret and falls back to the established Phase 401 project contact. Offline tests passed 37/37. The first natural post-merge 13F poll is still pending; no manual duplicate poll was sent.
- **SEC 13D/G:** Phase 350 retrieved and validated 43/44 explicit parent references. One parent is unresolved after two evidence-based archive-path attempts (both HTTP 404). Phase 351 is now manual-only to prevent retries.
- **Phase 352:** offline identity/security crosswalk passed 9/9 tests. Structured parent reporting-person names overlap child names in 21/21 documents where those tags are available. Parent `FILED BY` CIK overlaps child reporting-person CIKs in 25/25 cases where child CIKs exist, but this is a submitter proxy. CUSIP continuity: 31/42 valid matches, 5 mismatches, 6 missing parent CUSIPs, 1 invalid sentinel, 1 unresolved parent.
- **Implementation:** Phase 350–352 scripts and workflows remain in Draft stacked PR #37 against `phase347-13dg-cusip-integrity-audit`; do not merge directly to main before reviewing the parent chain.
- **PIT:** no first-publication timestamps; acceptance times do not certify first public availability. No 13D/G signal is eligible.
- **Other sources:** FINRA Reg SHO remains quarantined for BCPC/TPC facility-grain conflicts. CFTC TFF remains a possible broad-market regime covariate, not stock-level flow. Options budget remains USD 0.
- **Model validation:** no new alpha, OOS, bootstrap or LOO evidence. No changes to exposure, universe, costs, parameters, holdout or holding-period policy.

Full report: [Phase 636](PHASE636_SMART_MONEY_13DG_PARENT_LINEAGE_RESULTS_2026-11-26.md).
