# Phase 68 — SEC mutual-fund/ETF ticker-to-CIK mapping repair

**Date:** 2026-11-04  
**Status:** Mapping parser correction and coverage audit; no PIT or economic test.

## 1. Defect found

Phase 50's current CIK candidate mapper queried the official SEC company_tickers_mf.json source but extracted only ticker, classTicker or class_ticker. The official mutual-fund mapping uses the field name symbol, alongside cik, seriesId and classId. Therefore the mutual-fund/ETF source could be downloaded successfully while its ticker rows were silently ignored.

This is a plausible explanation for the 27 unresolved current tickers in Phase 66, all of which are ETF/fund symbols. It must be confirmed by the hosted Phase 68 mapping audit rather than assumed.

Official source:
https://www.sec.gov/files/company_tickers_mf.json

The source schema is also documented in SEC CIK mapping references:
https://github.com/jadchaar/sec-cik-mapper

## 2. Code correction

Added ticker_from_sec_row() to accept:
- ticker
- classTicker
- class_ticker
- symbol

The existing mapping logic already retains seriesId and classId in fund_classes. Phase 68 adds a unit test for the official symbol field and preserves fund series/class metadata in the output.

## 3. Coverage audit

The mapping audit compares the corrected 335-ticker result with the 27 names unresolved in Phase 66:
ARKF, ARKG, ARKK, ARKQ, ARKW, BITO, IEFA, IWM, JETS, KRE, OIH, SMH, SOXX, VEA, VNQ, VWO, XBI, XLB, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV and XLY.

It reports:
- newly mapped and still-unresolved names;
- CIKs shared by multiple ticker symbols;
- multiple CIK candidates per ticker;
- source provenance and series/class IDs;
- mapping-source errors.

The gate is deliberately modest: preserve at least the previous 308/335 mapped names and require zero source errors. It does not require every fund ticker to resolve if the official file does not contain it.

## 4. Important fund identity limitation

A fund registrant CIK can represent many series and classes. A ticker-to-registrant CIK mapping is not sufficient to assign a filing to one ETF security. The seriesId/classId must be retained, and the Form 144 security-class description must be reconciled separately. A current fund mapping is also not historical: symbols can change, funds can liquidate, and tickers can be reused.

Consequently, Phase 68 is only a current identifier repair. It does not establish historical F80 membership, PIT ticker validity, or security-level event attribution.

## 5. Decision

Do not calculate forward returns. Do not use the corrected current map as a historical security master. After the mapping audit, determine whether the newly resolved fund registrants add any usable issuer-level Form 144 candidates and whether security-class lineage can identify the exact fund series. If not, classify those ETF cases as unresolved/inapplicable rather than assigning a trust-level filing to every ticker under that registrant.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
