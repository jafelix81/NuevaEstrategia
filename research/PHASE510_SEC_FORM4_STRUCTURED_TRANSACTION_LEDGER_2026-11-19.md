# Phase 510 — SEC Form 4 structured transaction-detail ledger

**Date:** 2026-11-19  
**Preflight main:** 44b2560cd931b52c474cd05f939fe440ae484f0d  
**Disposition:** add a bounded, append-only structured detail ledger to the existing Phase 476 prospective Form 4/4-A collector. No signal, return test or production change is authorized.

## 1. Why this phase

The existing Form 4 collector is deliberately metadata-only. Phase 497 separately re-fetched and parsed 637 real ownership XML payloads and found 145 non-derivative P/A rows, but it did not persist transaction-level rows. Its 81-row structural-completeness queue was not a high-specificity discretionary/open-market cohort. A later repeat retrieved 636/637 and found only two of 81 rows with an explicit open-market footnote keyword; that cross-tab is provisional and keyword absence is not evidence of a private purchase.

Phase 498 found that the observed 655 bounded metadata events had receipt intervals 6.47–8.54 hours wide. Nominal hourly polling has not been demonstrated. The upper receipt bound still supports conservative next-session timing, but it does not identify the exact first-public time.

## 2. Implementation

The new phase510_form4_structured_transaction_ledger.py processes only existing Form 4/4-A event-ledger rows marked BOUNDED_METADATA_ONLY.

- Reuses the existing Phase 476 schedule; no second poller or new cron is created.
- Backfills newest-first, at most 10 accession documents per scheduled run.
- Retrieves the complete submission TXT and extracts the ownership XML; falls back to primary_doc.xml.
- Stores one filing-header row plus separate non-derivative and derivative transaction rows.
- Preserves accession, form, feed provenance, first-seen lower/upper bounds, first-seen run, acceptance clock, XML retrieval time, hashes and parser version.
- Independently rejects non-scheduled events, naive timestamps, reversed intervals and inconsistent upper-bound/receipt clocks.
- Stores transaction code, acquired/disposed code, raw and normalized numeric fields, security title, dates, direct/indirect flag, post-transaction holdings, derivative terms, footnote references, keyword flags and footnote hashes.
- Does not persist raw XML or full footnote text.
- Does not attach reporting-owner CIK to transaction rows. Single-owner records remain filing-grain only; multi-owner rows are explicitly quarantined because the applicable schema does not provide a transaction-to-owner key.
- Preserves Form 4/A as an amendment information arrival. It is not automatically counted as a new economic trade.
- Code P remains open-market-or-private purchase; the parser never labels it confirmed exchange execution. S/D and other codes are also preserved without inferring motive.
- Every row remains non-research-eligible, non-signal, non-intraday and without certified public-availability time.

A fetch failure remains pending for a later bounded retry. A successfully retrieved but malformed XML is recorded as a parse-error header row and quarantined rather than silently discarded. The detail ledger is append-only and idempotent by row key.

## 3. Validation

The 11 Phase 510 synthetic regression tests cover non-derivative/derivative separation, multi-owner quarantine, P-code semantics, amendment treatment, Decimal/date parsing, missing-value behavior, independent first-seen and retrieval clocks, strict rejection of naive/reversed intervals, parser-version-aware reprocessing, idempotent append, bounded-only selection, backfill limit and manual-mode no-write behavior. Combined with Phase 476, CI run 44642337001 passed 50 tests.

PR CI is offline-only. The first scheduled Phase 476 run after merge is the live integration gate. It must demonstrate actual XML retrieval, parse success, append-only behavior and artifact summary before the ledger can be described as live-validated.

## 4. Source and economic limitations

- No historical first-public timestamp is reconstructed.
- SEC acceptance is not exact public availability.
- Feed-path CIK remains unverified routing metadata, not issuer identity.
- Issuer CIK/symbol fields are extracted but not joined to the effective-dated 335-name F80 security master.
- Transaction date is not a tradable event timestamp.
- P/A does not prove an exchange execution; footnote keywords are diagnostics, not intent classification.
- Reporting-owner count is not transaction-owner attribution.
- No forward returns, event study, backtest, OOS, bootstrap, LOO or holdout test was run.

## 5. Decision

This phase advances Form 4 from prospective metadata collection to prospective transaction-detail collection. It does not create an insider signal. The next gates are live parser validation, historical issuer/security-class identity, effective-dated F80 membership and conservative first-executable-session mapping. Only after those gates pass may a preregistered discretionary-purchase or sale-pressure hypothesis be compared with frozen LTM/F80 using identical exposure and costs.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
