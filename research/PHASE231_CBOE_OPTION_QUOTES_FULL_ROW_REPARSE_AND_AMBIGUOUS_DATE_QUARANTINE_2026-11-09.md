# Phase 231 — Cboe Option Quotes full-row reparse with unique-only date quarantine

**Date:** 2026-11-09  
**Status:** Full raw-sample diagnostic completed; unambiguous subset passes; ambiguous rows quarantined  
**Workflow:** [Run 42568771468](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42568771468)  
**Artifact:** [Metadata-only artifact 13651429847](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42568771468/artifacts/13651429847)

## Result

The Phase 230 date-locale correction was applied to the original Phase 174 full-row parser, then the complete public sample was downloaded again and reprocessed. The raw sample SHA-256 matched the pinned Phase 174/175 source exactly:

\`7645a6cc94f1a984e98264a4b494f748e373c30ecde85de25ceadb83a5c56782\`

Archive size: 2,628,937 bytes.

| Measure | Result |
|---|---:|
| Data members | 5 |
| Populated row instances | 115,617 |
| Ambiguous expiration rows quarantined | 3,304 |
| Ambiguous quote timestamps | 0 |
| Unambiguous valid rows | 112,313 |
| Non-ambiguous invalid contract rows | 0 |
| Invalid timestamps | 0 |
| Numeric error rows | 0 |
| Duplicate contract/interval keys | 0 |
| Bid-above-ask rows | 0 |
| Contract-days with inconsistent start-of-day OI | 0 |

All five data members passed the unambiguous-subset gate. All member-level date counters reconciled with the independent Phase 175 all-row diagnostic. The full-sample schema gate remains **false** because ambiguous expiration values were not guessed or silently coerced.

The 3,304 ambiguous expiration rows occur in the four 2023-09-21 members (826 per member). The fifth member, dated 2022-02-02, has no ambiguous expiration rows. The other 112,313 rows passed the full row-level contract, numeric, duplicate-key, and available OI invariants.

## Schema and coverage limits

The five members contain 17, 25, 26, 18, and 26 columns. Four members have quote date 2023-09-21 and one has quote date 2022-02-02. The 2023 members each contain two underlying symbols; the 2022 member contains one. Member-level unique-series counts are not globally deduplicated across files.

This is a parser and sample-integrity result, not a historical coverage result. Five files, two quote dates, and a very small underlying sample cannot establish active/delisted universe coverage, continuous historical availability, first-receipt timestamps, or a stable correction-vintage policy.

## Important field semantics

- The quote timestamp files preserve their actual precision: the slash-formatted records have minute precision; the ISO records have seconds. No seconds were fabricated.
- Zero trade volume is not a row error: quote intervals can exist without a trade.
- The 2022 member contains 1,392 rows with zero IV but non-zero Greeks. Cboe's FAQ explains this can occur when the mid-price is below intrinsic, no quoted market is available, or the IV solver reaches its limit; Greeks may use the ask as a fallback while IV does not. This is a documented calculation convention, not evidence of malformed rows.
- Open interest is previous-night OCC end-of-day OI, static during the trading day; the sample showed no contract-day inconsistencies where the field was present.

## CI history and correction

The first Phase 231 run (42568562899) completed parsing and uploaded an artifact but failed its final assertion because the wrapper did not expose the already-verified archive hash as \`archive_integrity_match\`. The source hash itself matched. The wrapper was corrected to publish that boolean, and the current-head rerun **42568771468 succeeded**:
- 9/9 offline regression tests passed.
- Full public sample download and reparse succeeded.
- Date-counter reconciliation passed for every member.
- Metadata-only artifact uploaded (2,422 bytes; ZIP SHA-256 \`b65e594b48b1467bf22aefecf7b9afab78f4a18e2caf47e30569a57453f0a924\`).

The initial failed run is retained in the audit trail; it was an output-contract bug, not a data or parser failure.

## Decision

**Accept the unique-date parser correction for this pinned public sample only.** Keep 3,304 ambiguous expirations quarantined. Do not admit Cboe Option Quotes to strict PIT or alpha. No forward-return test, bootstrap/LOO, chronological OOS, or final holdout was used. No data was purchased; F80 and production were not changed.
