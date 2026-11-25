# Smart Money Research state addendum — Phase 48 (2026-11-25 00:41 UTC)

- **PASS:** Phase 48's pure SEC 13F manager-period as-of amendment state machine compiled and passed 12/12 synthetic offline regression tests in [Actions run 45519938849](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45519938849).
- RESTATEMENT replaces the full portfolio state; NEW HOLDINGS / NEW HOLDINGS ENTRIES appends only new line keys; overlapping entries fail closed.
- 13F-NT and 13F-NT/A are retained as notice-only events, never as zero holdings.
- Availability uses the first supplied regular session strictly after date-only FILING_DATE; report period is never treated as availability. The session calendar must be externally verified and have sufficient forward coverage.
- Phase 47 workflow security/operations fix: PR run [45519613878](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45519613878) passed seven offline tests; live SEC retrieval was skipped. Future live retrieval requires explicit workflow_dispatch with run_live_sec_audit=true. No live SEC request occurred in this run.
- Phase 48 tests are synthetic only. No actual holdings state panel, OTHERMANAGER linkage, historical CUSIP/FIGI-to-F80 crosswalk, exact acceptance timestamp, signal, alpha, OOS, bootstrap or LOO result is claimed.
- Historical 13F coverage remains unresolved: Phase 22C reported 212/335 in 2016Q1, 246/335 in 2020Q1 and 280/335 in 2024Q1. Phase 604's 328/335 is current registered-fund ticker/registrant discovery, not an effective-dated security master.
- Next: parse OTHERMANAGER relationships and validate complete amendment chains against original EDGAR filings, then revisit the historical CUSIP/F80 coverage gate.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. Options budget remains USD 0; no sample, purchase or quote request.
