# Smart Money Research state addendum — Phase 537 (2026-11-21)

- **SEC Form 4/4-A:** natural scheduled run 44846461134 succeeded; 474 new accessions were captured with bounded metadata. Ten structured accessions produced 24 detail rows; ten owner accessions produced 15 owner rows. The two queued Atea single-owner filings are now in the sidecar.
- **SEC Form 144/144-A:** natural scheduled run 44847230610 succeeded; 91 events and 103 feed observations were captured, with 91/91 acceptance reconciliations and zero unresolved. Ten backfill accessions produced 62 detail rows. First-seen remains a receipt upper bound, not exact public availability.
- **Automated crosswalk:** the Form 4 run artifact now contains three strict matches: two Atea proposed-sale rows (Bruce Polsky, 8,750 shares; Bruno Lucidi, 22,619 shares) and one Bruno Lucidi prior-sale-history row. Both proposed sales are explicitly linked in filing remarks to option exercise costs and tax planning. Treat as a negative control against naive bearish insider-sale counts. Zero signal-eligible matches.
- **SEC delivery:** both collectors have now produced a further natural scheduled success after the Phase 536 gap snapshot. Keep Issue #194 open until recurring cadence is stable; no manual dispatch or rerun.
- **FINRA Reg SHO:** 56 offline tests passed in run 44669121290, but its live poll remains 8/8 HTTP-200 invalid and predates the Phase 515 repair. No post-Phase-515 scheduled live validation was visible in the latest 100 runs at 2026-11-21 01:22 UTC. No manual dispatch or rerun.
- **Phase 20C:** historical price panel remains 328/329; provider fallback did not recover missing symbols. FINRA Short Interest still requires authorized credentials and one complete async settlement snapshot.
- **Controls:** no event study, backtest, OOS, bootstrap, LOO or holdout test; no signal admitted; `F80_TOP20_PARTIAL50_BASELINE_C20` and production remain frozen.

See `PHASE537_SEC_FORM4_OWNER_ENRICHMENT_AND_CROSSWALK_LIVE_VALIDATION_2026-11-21.md` and its JSON summary for the complete audit.
