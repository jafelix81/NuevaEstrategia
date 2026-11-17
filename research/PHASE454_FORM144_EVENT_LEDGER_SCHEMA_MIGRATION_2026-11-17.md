# Phase 454 — SEC Form 144 append-only event-ledger schema migration

**Audit time:** 2026-11-17 12:38 UTC  
**Disposition:** MATERIAL LIVE-CAPTURE BUG CONFIRMED; ROOT CAUSE IS CSV HEADER/WRITER SCHEMA DRIFT, NOT A SEC FEED OUTAGE. Atomic, fail-closed migration added before the capture step. No historical timestamps or signals are fabricated.

## 1. New live evidence

A real scheduled Phase 403 run occurred after the prior audit:

- [Run 44083941814](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44083941814)
- Event: `schedule`; main SHA: `cfe97c971cceb027a50f924ce9984ba6489492d5`
- Offline regression: passed.
- Live capture: failed in acceptance reconciliation.
- No artifact; append-only commit step skipped.

The exact exception was:

```
ValueError: invalid literal for int() with base 10:
'2026-11-16T16:55:39-05:00'
```

## 2. Root cause proved from committed files

Phase 444 inserted two fields into the current `EVENT_FIELDS` order immediately after `feed_names`:

- `cross_feed_provenance_complete`
- `capture_poll_status`

The committed `research/data/sec_form144_first_seen/events.csv` still has the prior header, which omits those two fields. The old append routine wrote new rows using the new field order but did not migrate the existing header.

For a newly appended row, the old header therefore interpreted each subsequent value two columns late. In particular, the current `feed_path_cik` column received the `feed_updated_raw` timestamp. The acceptance reconciler then attempted `int(path_cik)` and raised the observed ValueError.

The code appends new rows before acceptance reconciliation. The failed job's commit step was skipped, so the malformed runner-workspace rows and state were not pushed to main. The committed historical ledger remains intact; the mismatch is still present and must be migrated before the next live capture.

This is a schema migration omission in Phase 444's live integration. Its synthetic partial-feed tests passed because their temporary ledgers were created with the current header; they did not exercise the existing main ledger.

## 3. Fix

Added `phase454_form144_event_ledger_schema_migration.py` and a PR-only regression suite. The existing Phase 403 workflow now:

1. Compiles the migration module and runs both Phase 403 and Phase 454 offline tests.
2. Runs the migration step before the live SEC capture.
3. Rewrites only when the existing header is a strict subset/reordering of the current `EVENT_FIELDS`.
4. Preserves every historical field by column name; newly introduced fields remain blank for old rows (unknown, not inferred).
5. Rejects duplicate headers, unknown columns and malformed rows with extra values; it never silently drops data.
6. Uses a same-directory temporary file, flush/fsync and atomic `os.replace`.
7. Writes a small migration audit JSON into the normal Phase 403 artifact directory.

The migration is idempotent. It does not call SEC, modify first-seen timestamps, change event eligibility, or authorize a signal. The current main ledger's two missing columns will be backfilled as blank values only.

## 4. Validation

Six offline migration tests cover:
- legacy header migration and preservation of `feed_path_cik` / feed timestamps;
- a new append after migration with correct column alignment;
- idempotence;
- fail-closed unknown and duplicate headers;
- malformed extra row values;
- missing/empty file no-op.

The existing Phase 403 offline suite remains in the same CI gate. Live capture is skipped on pull requests.

## 5. Research and operational controls

The run 440839 schedule event proves at least one scheduled trigger was delivered; it does not establish reliable hourly delivery. The failed run did not persist its newly appended runner-workspace rows or poll state. The next successful scheduled run must produce an artifact and a committed ledger/state update before we count any new first-seen observation.

- SEC feed first-seen remains an upper-bound timestamp, not exact SEC-public receipt.
- No manual dispatch or replay was used to manufacture prospective observations.
- No new Form 144 signal or forward-return test was run.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## 6. Reproduction

```bash
python -m research.phase454_form144_event_ledger_schema_migration --path research/data/sec_form144_first_seen/events.csv --output phase403_output/schema_migration.json
python -m unittest -v research.test_phase403_sec_form144_first_seen_capture research.test_phase454_form144_event_ledger_schema_migration
```
