# Smart Money Research — state addendum (Phase 678)

**Updated:** 2026-11-28 UTC  
**Main HEAD after latest FINRA capture:** `bc4d02d9fd9d60cf726c2bdefd822fbaece35d2d`.

## Phase 678 — FINRA Reg SHO prospective symbol panel

- Latest-20 Actions preflight: 0 active/queued runs; no duplicate workflow dispatched.
- Scheduled run [46105917821](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46105917821) passed both jobs. Offline regression: 65/65 tests. Live capture succeeded.
- **Schedule drift:** Phase 469 declares weekday polls at 22:30 and 23:30 UTC, while this run started at 04:05:39 UTC on 2026-11-28. The run payload does not identify which nominal slot triggered it; the observed start is about 4h35–5h35 later. No manual dispatch/rerun occurred. This is a capture-cadence risk, not a source-publication timestamp.
- The run appended 327 unique symbol rows for trade date 2026-11-27 against the frozen 335-ticker snapshot (97.61% observed-row coverage). Eight names had no row in the source file; this is not classified as delisting or zero volume.
- One date-level first-seen event is research-observation eligible; all 327 rows remain signal-ineligible. The stored first-seen timestamp is a conservative poll-interval upper bound, not exact release time.
- Duplicate diagnostics: 14 symbols / 28 quarantined row occurrences across seven files. Ambiguous duplicate symbols remain fully excluded.
- Raw FINRA source bytes are not persisted; only hashes, metadata and derived per-symbol aggregates are stored. This limits independent raw-value reproduction.
- One-day short-ratio distribution is descriptive only (median 49.21%; IQR 39.02%–58.28%). It is not evidence of investor identity, directional conviction or alpha.
- Since the 2026-11-27 file was first observed after close, the earliest daily-bar-based test session is 2026-11-30. No approved price panel/security master or return labels are joined yet.

Full audit: [Phase 678 report](PHASE678_FINRA_REGSHO_FIRST_PROSPECTIVE_SYMBOL_PANEL_AUDIT_2026-11-28.md).

## Cross-source checks

- **CFTC TFF:** scheduled run [46105422375](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46105422375) succeeded; 17/17 tests passed, but no new report/revision was found. The stored history remains 3,043 rows, with zero signal-eligible historical rows.
- **SEC Form 4:** scheduled run [46099559273](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46099559273) passed offline and live jobs. It added 156 unique accession observations, but no Form 144/Form 4 match became signal-eligible.
- **SEC 13F:** Phase 677's AMS Capital filing remains a retrospective `LEGACY_THOUSANDS_CANDIDATE`, not a normalized holding or feature. Only seven of 15 rows were price-checked; raw XML and SHA-256 are still absent. No production parser change.
- **13F report-period selector:** PR #262 remains a draft stacked on the Phase 613/PR #230 dependency chain; do not merge it until that chain is reconciled.
- **Options/OPRA and 13D/G:** historical-vintage, point-in-time, rights or live-sample gates remain unresolved. No paid source or vendor contact.

## Strategy controls

- New signals promoted: **0**.
- Incremental alpha demonstrated: **none**.
- New valid OOS / bootstrap / LOO result: **0**.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No capital, exposure, universe, parameter or production changes.
- Data budget remains USD 0.

The operational FINRA capture milestone is complete, but the evidence does not justify increasing the project's edge-validation progress estimate.