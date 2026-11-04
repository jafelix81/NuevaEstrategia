# Phase 68 — SEC fund ticker map repair results

**Date:** 2026-11-04  
**Actions run:** 41828426133 — success  
**Artifact:** 13321546076 — phase68-sec-fund-ticker-map-audit  
**Artifact SHA-256:** ec09dc05f3b97d2a8b2ea3a8240e1582ef3ee50d28af91b3cb0593841c7d0c0e

## Result

The parser fix adding the SEC mutual-fund field name symbol resolves all 27 previously unmapped tickers in the 335-name current universe.

| Metric | Before | After |
|---|---:|---:|
| Mapped tickers | 308/335 | 335/335 |
| Unresolved tickers | 27 | 0 |
| Candidate registrant CIKs | 309 | 319 |
| Mapping-source errors | 0 | 0 |

All 27 previously unresolved tickers were returned by company_tickers_mf.json:
ARKF, ARKG, ARKK, ARKQ, ARKW, BITO, IEFA, IWM, JETS, KRE, OIH, SMH, SOXX, VEA, VNQ, VWO, XBI, XLB, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV and XLY.

The mutual-fund source contributed 28 universe ticker mappings, including QQQ which also appears in the fallback mapper. The corrected map retains each fund's seriesId and classId.

## Shared registrant CIKs

Six CIKs map to multiple tickers:
- 0001579982: ARKF, ARKG, ARKK, ARKQ, ARKW.
- 0001100663: IEFA, IWM, SOXX.
- 0001064642: KRE, XBI.
- 0001137360: OIH, SMH.
- 0001064641: XLB, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY.
- 0001064640: Z, ZG.

The output reports six shared CIKs; two tickers have multiple CIK candidates in the source union. Use the artifact CSV as the exact row-level source of truth.

## Interpretation and remaining limits

This closes the current ticker-to-registrant CIK mapping gap for the 335 current symbols. It does **not** establish historical PIT ticker/CIK validity, historical F80 membership, predecessor/delisted issuer coverage or security-level attribution for funds.

A registrant CIK can represent multiple fund series/classes. Keep seriesId/classId and do not assign a trust-level Form 144 filing to every ETF sharing that registrant. The filing's security class and a historical series/class crosswalk must resolve the specific instrument. Current fund maps can also lag symbol changes or retain stale/recycled symbols.

## Decision

- Phase 68 current mapping gate: PASS (335/335; zero source errors).
- Historical PIT security-master gate: NOT TESTED.
- Fund series/class-to-Form-144 security-class gate: NOT TESTED.
- No forward returns or alpha tests.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
