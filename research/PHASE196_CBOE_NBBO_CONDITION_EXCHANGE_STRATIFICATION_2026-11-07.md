# Phase 196 — Cboe Option Trades NBBO-side decomposition by condition and exchange

**Audit date:** 2026-11-07  
**Disposition:** STRATIFIED_SAMPLE_DIAGNOSTIC_PASS  
**Scope:** one public sample date (2026-01-07), one underlying, 74,999 prints. No return or alpha test.

## Hosted execution

Workflow [42419754569](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42419754569) completed successfully. All 8 offline regression tests passed, the public sample and both current reference files downloaded, all 11 cross-tab reconciliation checks passed, and a 13,713-byte metadata-only artifact was uploaded (artifact 13592858186; SHA-256 8fc18375f52cb8d440e6850de7df5b7a32be028e70786eef0f05e97979d14912).

The sample archive SHA-256 is a02504e156db28b3f007d9d25a534e4c88ffd8d24ac43f3bf84885583a3d10b8; the canonical core-row digest matches Phase 194 (4dd0e041ca3b1921a2f5a6a3825a9505be234947736232fb47f18e93c74d1b06). All 74,999 prints and 531,227 contracts reconcile to the Phase 194 audit. The 15 observed condition IDs, 18 exchange IDs and 99 observed condition×exchange cells all map to the current public reference files.

## Main result: the aggregate imbalance is composition-sensitive

The exact-at-ask minus exact-at-bid contract-volume proxy remains **-36,763 contracts** (172,313 at ask versus 209,076 at bid), or -6.92% of total contract volume. Another 149,838 contracts are in other NBBO classes and are not assigned a side.

| Current condition bucket | Prints | Contract volume | At ask | At bid | Candidate net |
|---|---:|---:|---:|---:|---:|
| Single-leg auction/cross | 20,091 | 143,607 | 34,636 | 55,114 | **-20,478** |
| AutoExecution | 40,334 | 269,551 | 112,489 | 128,884 | **-16,395** |
| IntermarketSweep | 2,165 | 14,142 | 5,854 | 7,699 | -1,845 |
| Multi-leg | 12,331 | 92,020 | 15,921 | 17,355 | -1,434 |
| Single-leg floor | 14 | 10,347 | 3,408 | 15 | +3,393 |
| Stock-option | 64 | 1,560 | 5 | 9 | -4 |

Single-leg auction/cross and AutoExecution account for 55.70% and 44.60% of the net negative proxy, respectively. The 14 single-leg floor prints offset 9.23% of the net deficit. These are execution-condition labels, not beneficial-owner or institutional classifications. The 14 floor prints have a relatively large aggregate size, but this does not identify who traded or why.

The exchange cross-tab contains 18 venues. The largest negative candidate nets are PHLX (-7,156), CBOE (-5,973), ARCA (-4,635), MIAX (-4,412) and MEMX (-3,319). Positive nets appear at AMEX (+2,078), SPHR (+1,066) and BZX (+22). This is one underlying on one date; it is not evidence of persistent venue behavior.

## Critical sensitivity: contract count and premium-weighted arithmetic have opposite signs

The at-ask price-times-contracts sum is 316,324.76; the at-bid sum is 302,387.38. Their difference is **+13,937.38**, even though the raw contract-volume difference is -36,763. The corresponding average premiums are approximately 1.8358 at ask and 1.4463 at bid.

This is not dollar notional: no contract multiplier or adjusted deliverable is applied. It is nevertheless a useful warning. The sign of the apparent imbalance changes when trades are weighted by premium, so raw contract counts alone are not a stable economic measure of directional flow. Contract mix (call/put, strike, expiry, deliverable and delta) must be normalized before any interpretation; the sample's time field remains opaque, and no time-sensitive Greek is admitted.

## Data and PIT limitations

- The condition workbook has 80 rows but only id/name/security_type; no message_type or effective-date fields.
- The exchange file has 40 rows and no effective dates.
- Both current mapping files were last modified after the 2026-01-07 sample date. They support current descriptive labels only, not historical PIT semantics.
- Strict Regular/Normal + trade + options side-eligibility rows: **0**.
- First file receipt, historical daily completeness, inactive/delisted coverage, cancel/correction vintages, adjusted deliverables and broad multi-underlying coverage remain unverified.
- quote_datetime was not used or persisted. The sample is not a multi-day history.

## Admission decision

Phase 196 passes a descriptive cross-tab measurement gate only. It does **not** admit a signed-flow feature, an institutional/informed-flow claim, a stock/option return test or alpha. No holdout was used, no data were purchased, no provider was contacted, production was not changed, and F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

Next gate: obtain effective-dated condition semantics and immutable file-receipt/correction history, verify adjusted contract multipliers/deliverables, and demonstrate multi-day/multi-underlying coverage before deciding whether this source deserves a historical study. If those gates cannot be met, archive this raw-trade signed-flow route rather than optimizing the one-day imbalance.
