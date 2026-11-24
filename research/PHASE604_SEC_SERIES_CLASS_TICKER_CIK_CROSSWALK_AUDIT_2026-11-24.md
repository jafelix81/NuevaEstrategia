# Phase 604 — SEC series/class ticker-to-CIK crosswalk feasibility audit

**Status:** awaiting bounded GitHub Actions execution  
**Scope:** resolve the 35 tickers left unmapped by Phase 603 using SEC official registered-fund series/class records and current mutual-fund ticker metadata.

## Hypothesis

Some of the 35 Phase 603 unmapped symbols are registered fund or ETF share classes whose ticker-to-registrant CIK association is not represented in the SEC's ordinary company ticker files. The SEC publishes a separate company-tickers-MF file and annual Investment Company Series and Class reports; these sources may improve current discovery coverage.

## Sources and design

- Current company_tickers.json and company_tickers_exchange.json are the Phase 603 baseline.
- Current company_tickers_mf.json is parsed separately, retaining registrant CIK, series ID, class ID and ticker where available.
- SEC Investment Company Series and Class CSV snapshots: 2026, 2025, 2024, 2020, 2016 and 2010.
- Every downloaded file is hashed. Exact ticker matching only; no fuzzy name matching or inferred CIKs.
- Multiple class rows are preserved. Multiple CIKs for one ticker are reported as conflicts, not silently collapsed.

## Hard limitations

The SEC describes its ticker files as periodically updated discovery aids and does not guarantee their accuracy or scope. Its Series and Class report is a snapshot, not an effective-dated security master. It may include funds that have not launched or that ceased operations without updating status, and it is not comprehensive for all closed-end funds or unit investment trusts.

The CIK in the Series/Class report identifies the investment-company registrant; series and class IDs are separate identifiers. A match is therefore a candidate ticker-to-registrant link, not proof that a given 13D/G header's SUBJECT COMPANY is that CIK.

No historical F80 membership, exact ticker-change dates, public-availability time, signal, returns, OOS, bootstrap or LOO test is authorized by this phase.

## Decision rule

- PASS only if the current company ticker files, current mutual-fund ticker file and 2026 Series/Class CSV are fetched and parsed successfully.
- Historical snapshot failures are reported individually and do not get silently imputed.
- The final report will record incremental mappings, remaining unmapped symbols, CIK conflicts, and cross-snapshot changes.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; options-data budget remains USD 0.
