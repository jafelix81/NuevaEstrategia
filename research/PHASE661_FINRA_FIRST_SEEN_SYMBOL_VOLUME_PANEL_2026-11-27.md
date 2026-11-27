# Phase 661 — FINRA first-seen symbol-volume panel persistence

**Audit cutoff:** 2026-11-27 10:02 UTC  
**Base:** `main` at `a27340c1866b5e44f2638eb4dc3e0cbd1617b7ea`  
**Disposition:** implementation and offline validation complete in draft PR #251; production capture remains pending merge and the next natural scheduled poll.

## 1. Why this phase was necessary

The Phase 469 collector parsed FINRA CNMS daily short-sale-volume files, but its `build_symbol_observations` helper emitted only timing/metadata fields and was not called from `run_capture`. The collector therefore preserved file hashes and duplicate diagnostics without preserving any usable short-volume values.

The last natural capture before this change was [run 45939887443](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45939887443). Both jobs succeeded, but the live poll returned seven valid historical files classified as **bootstrap**, one 403 for 2026-11-26, and zero first-seen or late-first-seen research observations. Its compact artifact was only 1,985 bytes and contained summary metadata, not a symbol-volume panel.

## 2. Change implemented

The collector now builds and appends `research/data/finra_regsho_daily_first_seen/symbol_observations.csv` only when a file is conservatively eligible as `first_seen` or `late_first_seen`.

Each row preserves:

- short volume, short-exempt volume, total volume and derived ratios;
- symbol, trade date, market/facility tokens and parsed row grain;
- source-row SHA-256 fingerprints, whole-file SHA-256, byte count and schema version;
- source URL and original row/symbol counts;
- poll start/end and first-seen upper bound, explicitly marked as **not the exact public-release timestamp**;
- the exact static ticker-filter snapshot commit and SHA-256;
- research-observation eligibility true and signal eligibility false.

The static filter is an exact copy of the 335-ticker reference from commit `1aa1b91f383ce9cef375a43e775c736a27356a5`, verified at runtime against SHA-256 `f850655a22a8843dad90e9562b3152b9ca064560586109022b5bfd205a003dda`. This is a reproducible symbol filter only; it is **not** evidence that a ticker was an eligible F80 constituent on any historical date.

## 3. Integrity and no-lookahead controls

1. Only the 335 exact reference symbols are persisted by the scheduled CLI. The parser still diagnoses the complete source file before filtering.
2. Every row for an ambiguous duplicated symbol remains quarantined; unique symbols may be retained in a clearly marked partial panel.
3. Legacy facility-grain rows retain the ordered hashes of every source row contributing to an aggregate.
4. Panel append is idempotent on `(trade_date, symbol, raw_sha256)`. A retry with the same immutable content is skipped; conflicting content for the same key fails closed.
5. The panel is written before the state checkpoint so a retry after an interrupted run cannot silently lose rows or duplicate them.
6. Bootstrap files, manual diagnostics, unchanged polls and revisions do not produce eligible panel rows. Revisions preserve the original first-seen event and are not reclassified as new observations.
7. The first-seen clock remains the collector poll interval. The upper bound is used conservatively for executable-session mapping; it is not treated as the exact instant FINRA published the file.
8. Raw source bytes are not persisted. The panel stores parsed values plus file/row hashes and source metadata; the original public URL remains recorded.

## 4. Validation

[PR validation run 45978706947](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45978706947):

- offline regression: **65 tests passed**;
- live-capture job: correctly skipped for a pull-request event;
- no artifact was expected from the offline-only PR run.

Tests cover volume persistence, partial-symbol quarantine, first-seen and late-first-seen clocks, bootstrap/manual/revision exclusion, exact universe hash/count, retry idempotency, and explicit-universe filtering.

## 5. Next natural capture

After merge, the next scheduled FINRA poll is the first opportunity for production rows. It should check 2026-11-26 for a possible `late_first_seen` only if the prior scheduled 403 is present in the persistent poll ledger, and 2026-11-27 for same-day `first_seen` after 16:00 New York time. Neither event is assumed in advance. No manual dispatch is needed.

## 6. Research status

This phase repairs a missing data-persistence step; it does not demonstrate a predictive edge.

- No price or forward-return data inspected.
- No event study, signal, OOS, bootstrap or LOO test run.
- No short-flow feature admitted to the strategy.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No data vendor contacted; no purchase; data budget remains USD 0.
