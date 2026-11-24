# Smart Money Research state addendum — Phase 604 (2026-11-24 23:00 UTC)

## Completed: SEC registered-fund ticker/CIK crosswalk

- Phase 604 Actions run [45505786670](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45505786670) succeeded; all 11 offline regression tests passed; artifact [14972004133](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45505786670/artifacts/14972004133) contains row-level mappings, source hashes, manifest and summary.
- All nine SEC files (current company ticker JSON, current mutual-fund ticker JSON, and Series/Class snapshots for 2010, 2016, 2020, 2024, 2025 and 2026) returned HTTP 200 and parsed.
- Current discovery coverage increased from 300/335 to 328/335. The current SEC mutual-fund ticker file and 2026 Series/Class snapshot agree on 28 additional F80 tickers and their 11 registrant CIKs; zero conflicts.
- Across available historical snapshots, 27 tickers retain the same CIK wherever they appear; QQQ appears in one Series/Class snapshot only (2026) and agrees with the current MF ticker file. Seven names remain unresolved by this registered-fund source gate: AVB, EA, EQR, LPRO, ROKU, WBD, WBS.
- This is a current discovery/registrant crosswalk only. Annual snapshots are not effective-dated, do not prove historical F80 membership or exact public availability, and do not make a registrant CIK interchangeable with a 13D/G SUBJECT COMPANY or beneficial-owner CIK.
- Workflow's SEC_USER_AGENT secret environment variable was empty; the existing Phase 401 contact fallback was used and all nine SEC downloads succeeded. No human intervention or secret change was required for Phase 604; repository-secret configuration itself remains unverified.
- Full report: [Phase 604](PHASE604_SEC_SERIES_CLASS_TICKER_CIK_CROSSWALK_AUDIT_2026-11-24.md).

## Other source gates — current disposition

- **SEC Form 4 / Form 144:** prospective first-seen capture and structured parsing continue. Retrieval-clock bounds are conservative but not exact SEC public-dissemination timestamps. Owner-to-transaction attribution, historical security identity and F80 overlap remain incomplete; zero signal-eligible rows.
- **SEC 13D/G:** Phase 603 established the importance of separating SUBJECT COMPANY from FILED BY. Phase 604 improves current fund/ETF registrant discovery, but historical effective-dated identity and exact filing-role joins remain mandatory. Phase 350 historical parent retrieval is still a separate access/coverage task.
- **SEC 13F:** official structured quarterly datasets have a long historical span (Phase 45), and Phase 47's accession-level SUBMISSION-to-INFOTABLE join is the next useful institutional-ownership feasibility gate. Use filing/acceptance availability, never report-quarter-end, as the information clock; amendments and CUSIP-to-F80 identity must be handled before signal research. The current Phase 47 prototype still contains a placeholder User-Agent and should be corrected to the accepted project contact fallback before a live run.
- **Options:** Phase 547 ranks OPRA-wide Cboe Option Trades plus Option Quotes as a conditional broad-market feature source, with Open-Close EOD as a venue-capacity/open/close complement. Exact 335-name coverage, first-receipt vintages, historical convention changes and rights remain unverified. Phase 530's Massive history is conditional but paid; no sample, license or purchase is authorized. Options budget remains USD 0.
- **FINRA Reg SHO / short interest:** Reg SHO files with repeated BCPC/TPC facility rows remain rejected pending correct raw-row/facility-grain reconciliation and a new accepted live capture. Consolidated Short Interest is a conditional twice-monthly positioning source with all-exchange coverage documented from June 2022, but the retrieved panel is not yet strict-PIT or complete for the 335-name universe.
- **CFTC TFF:** 3,043 historical rows remain; no new observations/revisions in the latest prior audit. Report-date and actual first-receipt clocks remain distinct.
- **Market microstructure:** SEC MIDAS is exchange-level context, not participant identity. Cboe TBT/PITCH remain conditional and sample/rights/PIT gated; no public sample is treated as representative market coverage.

## Research decision

- No Smart Money interpretation is assumed to be informed trading.
- No new predictive signal, event-return study, backtest, OOS, bootstrap or LOO result was produced in Phase 604.
- No source was promoted to production. No universe, exposure, cost, parameter, holdout or capital change.
- **F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.**
- Next highest-value data task: resolve the seven remaining issuer tickers with authoritative filing-based CIK evidence and date-aware security identity, then finish the SEC 13D/G subject-role join. In parallel, repair Phase 47's placeholder User-Agent and execute its bounded 13F accession join only after the SEC request identity is valid.
