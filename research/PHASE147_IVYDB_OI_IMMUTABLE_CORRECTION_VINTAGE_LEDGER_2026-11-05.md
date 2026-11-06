# Phase 147 — IvyDB OI immutable correction-vintage ledger

**Date:** 2026-11-05  
**Status:** Completed — offline implementation and regression only.  
**Input:** Phase 145–146 helper review and the documented IvyDB daily correction-patch requirement.  
**No licensed data, vendor contact, purchase, return test, or production change.**

## Decision

Implement an append-only vintage ledger so a corrected historical open-interest value cannot silently overwrite the value known at an earlier decision time. The Phase 145–146 single-version helper remains unchanged; Phase 147 adds an as-of path for normalized full-state versions.

## Why this correction matters

The Phase 145 helper records the current row's receipt, but a ΔOI feature depends on both current and prior-session observations. If the prior-session value is corrected after the current-session file arrives, the revised delta is not fully known until that later correction arrives.

Using only the current-session receipt would make the revised delta appear earlier than it was knowable. Phase 147 sets feature knowledge time to the later of the selected current and prior vintage receipts.

## Ledger contract

Each row is an immutable normalized version of one (security_id, option_id, session_date) state and contains:

- actual timezone-aware first_received_at;
- source_file_hash, source_version, unique version_id;
- version_kind = initial or correction;
- supersedes_version_id for each correction;
- operation = upsert or delete;
- full contract identity, terms, expiration, OI, volume and previous exchange session.

A patch-file adapter must expand each patch into a complete replacement row before writing this ledger. Raw files remain immutable. The helper requires one initial version followed by a strictly ordered, linear correction chain; ambiguous same-timestamp vintages, duplicate hashes within a chain, orphan corrections, stale supersedes pointers and invalid tombstones fail closed.

## As-of semantics

- Only versions with first_received_at strictly earlier than decision_time are visible.
- A correction is never backdated to the session or initial file receipt.
- At the exact correction timestamp, the prior version remains selected because no intra-timestamp sequence is recorded.
- A delete is represented as a tombstone from its own receipt time.
- Current and prior session values are selected independently as of the same decision instant.
- Feature knowledge time is max(current_selected_receipt, prior_selected_receipt).
- Missing/not-yet-known prior state, non-adjacent sessions, expiry, changed expiration, changed contract terms or source-version breaks suppress ΔOI.
- Signed negative ΔOI is retained; it is not a buyer/seller signal.

## Validation

Added:
- research/phase147_ivydb_oi_vintage_ledger.py
- research/test_phase147_ivydb_oi_vintage_ledger.py
- .github/workflows/phase147_ivydb_oi_vintage_ledger.yml

The offline suite covers initial/correction selection, strict timestamp boundaries, no retroactive mutation, late prior-session corrections delaying feature knowledge, chain integrity, duplicate IDs/hashes, tombstones, missing prior vintages, adjacency, expiry, contract continuity, schema-version changes, negative deltas and zero denominators.

## Limitations

- No actual IvyDB raw file or patch sample was available. The ledger is an adapter contract, not a claim that OptionMetrics publishes row-level supersedes IDs. The upstream ingestion process must derive and preserve the chain from immutable file/patch hashes and actual receipt logs.
- Exact vendor patch semantics, patch completeness and first-receipt history remain unverified. If a patch is partial rather than a full-state replacement, the adapter must reconstruct a full state from prior vintages without overwriting raw source files.
- A correct exchange calendar is supplied externally. The helper detects intervening contract observations but does not independently validate the calendar.
- No optionable-universe coverage, historical PIT proof, forward-return, bootstrap/LOO or incremental F80 test was performed.

## Disposition

**PASS — implementation integrity only. DATA/PIT GATE STILL CLOSED.** No alpha claim. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
