# Phase 333 — SEC TradingSymbol to share-class binding audit

**Date:** 2026-11-12 UTC  
**Status:** completed; direct class bindings found in a narrow, hash-pinned sample.  
**Run:** [43223597921](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43223597921)  
**Artifact:** [13946542878](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43223597921/artifacts/13946542878) — SHA-256 `fe39d1d377082f6a538f281809629a0085b855033f0dab82b5f0cf7f5d4c5e21`  
**Review:** [PR #22](https://github.com/jafelix81/NuevaEstrategia/pull/22), draft, based on Phase 332.

## Question and strict rule

When a pre-event SEC 8-K/8-K/A reports multiple TradingSymbol facts and multiple share classes, does the TradingSymbol fact itself carry an explicit XBRL class dimension?

A symbol-to-class link is accepted only when the **TradingSymbol fact's own context** contains a StatementClassOfStockAxis or ClassesOfShareCapitalAxis member. Document-level co-occurrence of symbols and class members is not a mapping. Same-context security titles are retained as supporting description, but no class is inferred when the symbol fact has no class dimension.

## Results

| Measure | Result |
|---|---:|
| Unique hash-pinned documents | 9 |
| SHA-256 matches | 9/9 |
| Expected symbol sets reproduced | 9/9 |
| TradingSymbol facts | 25 |
| TradingSymbol facts with class axis | 20 |
| Documents with direct class binding on all symbol facts | 4/9 |
| Documents with only issuer-level symbol evidence | 5/9 |

The nine documents are the unique latest pre-event symbol-evidence accessions from Phase 332: eight candidate-match documents and the TSBK/RVSB mismatch. The sample is purposive, selected conditional on a TradingSymbol fact; 4/9 is not an estimate of market-wide coverage.

## Direct mappings demonstrated

**FTAI — 4 symbols, 4 explicit classes**
- `FTAI` → Class A common shares.
- `FTAIN` → Series C 8.25% fixed-rate-reset cumulative perpetual redeemable preferred shares.
- `FTAIO` → Series B 8.00% fixed-to-floating cumulative perpetual redeemable preferred shares.
- `FTAIP` → Series A 8.25% fixed-to-floating cumulative perpetual redeemable preferred shares.

**STR — 2 symbols, 2 explicit classes**
- `STR` → Class A common stock.
- `STRWS` → Warrants to purchase Class A common stock.

**PCG — 10 symbols, 10 explicit classes**
- `PCG` → Common stock.
- `PCGU` → Equity Units.
- `PCG-PA` → 6% nonredeemable preferred.
- `PCG-PB` → 5.50% nonredeemable preferred.
- `PCG-PC` → 5% nonredeemable preferred.
- `PCG-PD` → 5% redeemable preferred.
- `PCG-PE` → 5% Series A redeemable preferred.
- `PCG-PG` → 4.80% redeemable preferred.
- `PCG-PH` → 4.50% redeemable preferred.
- `PCG-PI` → 4.36% Series A redeemable preferred.

**DLR — 4 symbols, 4 explicit classes**
- `DLR` → Common stock.
- `DLRPRJ` → Series J cumulative redeemable preferred.
- `DLRPRK` → Series K cumulative redeemable preferred.
- `DLRPRL` → Series L cumulative redeemable preferred.

In these four filings, each TradingSymbol fact carried its own explicit class-axis member and the same XBRL context contained the corresponding security title. These are direct structured bindings, not ticker-name heuristics.

## Five documents not promoted to class mapping

The remaining five documents each contained a single issuer-level TradingSymbol fact but no class axis on that fact. The same context often included a Security12bTitle (e.g. Common Stock), but without a class dimension this remains issuer-level evidence only:

- TSBK candidate / Riverview: actual pre-event symbol fact `RVSB`, not `TSBK`.
- LFCR, SAFE, NWLI and NWN: one symbol each; no direct class axis.

No listing-exchange axis was present on the 25 TradingSymbol facts in this nine-document sample. Phase 333 therefore resolves some share classes, not exchange/listing identity.

## Interpretation and next step

This is a meaningful feasibility result: SEC event-filing XBRL can directly bind symbols to share classes for some multi-class issuers, including common, preferred, equity-unit and warrant classes. It is not universal: 5/9 documents remain issuer-level only, and the sample is highly selected.

Next, expand to a stratified sample across the full 28-pair collision panel and multiple periods, deduplicate co-filers, apply the 365-day anchor-freshness rule, and measure direct class-binding coverage before considering a security-master graph. Keep ambiguous classes quarantined. The TSBK Form 4 XML remains unresolved.

## Controls

- All nine primary XBRL instances match their Phase 332 SHA-256; symbol sets match exactly.
- No class mapping is inferred from document-level co-occurrence.
- No security master or universe coverage admitted; no alpha/return/OOS/bootstrap/LOO test; no holdout use.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; production, universe, capital and parameters unchanged.
- No vendor contact or purchase.

