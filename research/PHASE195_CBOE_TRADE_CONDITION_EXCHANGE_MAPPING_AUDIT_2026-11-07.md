# Phase 195 — Cboe Option Trades condition and exchange reference mapping audit

**Audit date:** 2026-11-07  
**Disposition at commit:** hosted mapping retrieval pending  
**Scope:** official current reference mappings reconciled to the one-day 2026-01-07 public sample.

## Why this gate is necessary

Phase 194 established that the public sample can be parsed into daily NBBO-side measurements, but trade-condition IDs were counted without interpretation. A trade print at bid/ask is not automatically eligible for a signed-flow feature: late, out-of-sequence, auction, complex, correction and other special-condition trades can have different economic meaning.

Cboe DataShop exposes public reference files for LiveVol trade-condition IDs and exchange IDs. LiveVol's API documentation describes a message-condition reference mapping numeric IDs to a condition name, message type and applicable security types; the API endpoint itself requires OAuth authorization, so this phase uses only the public DataShop reference files and does not create an account or request credentials.

## Method

- Download the official trade-condition XLSX, exchange-ID CSV and the same public sample archive.
- Hash each downloaded file and retain response metadata.
- Parse XLSX shared strings, workbook relationships and all readable sheets using Python standard library only.
- Identify the mapping header by explicit ID/name columns; do not assume a worksheet or column order.
- Count observed trade-condition and exchange IDs in both 19-column and 25-column sample members; require the ID distributions to match.
- Reconcile every observed ID to the official current mapping.
- Classify descriptions conservatively: regular/normal, complex/spread, auction/cross, late/out-of-sequence, cancel/correction, extended hours, or unclassified.
- Mark a condition as a candidate side-eligible trade only if the mapping explicitly says Regular/Normal, message_type=trade and security_types includes option. A name-only match is insufficient.
- Detect effective-date fields in the mapping. Their absence means the current mapping cannot be assumed valid for historical samples.
- Persist hashes, IDs, descriptions and aggregate counts only. No raw sample rows, symbols, contracts or mapping workbook bytes are stored.

## Known source caveats

The published Option Trades file specification describes market_date as YYYY-MM-DD and quote_datetime as a full YYYY-MM-DD HH:MM:SS.000 timestamp. The public sample instead uses M/D/YYYY and a seven-character time-only field. Phase 194 quarantines that field; this mismatch remains unresolved and must not be silently normalized into an intraday timestamp.

The product page/FAQ advertise historical coverage, but the public sample is one day and one underlying. It does not prove daily completeness, inactive/delisted coverage, first file receipt or historical condition-map versions.

## Admission decision

A complete current mapping is a measurement-quality improvement, not PIT admission. Before signed flow can be backtested, require historical condition-code effective dates, cancellation/correction semantics, adjusted-deliverable treatment, first file receipt and historical sample coverage. Only explicitly normal/regular option trades may enter the primary candidate; all other codes remain separate or excluded by preregistered rule.

No signed-flow feature, stock/option return test, holdout use or production change is authorized. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
