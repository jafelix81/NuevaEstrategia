# Phase 437 — Item 408 issuer-specific XBRL extension preservation

**Date:** 2026-11-16  
**Status:** parser robustness improvement completed; no alpha admission  
**Trigger:** Phase 436 cross-issuer audit exposed custom Item 408 taxonomy facts in CarGurus (CARG).

## Finding

The CarGurus 2024 Q1 Item 408 rendering contains issuer-specific extension facts in addition to the standard ECD facts:

- `carg_Rule10B51ArrModifiedFlag`
- `carg_NonRule10B51ArrModifiedFlag`
- `carg_TrdArrExpirationDate`
- `carg_IndividualAxis` and `carg_TradingArrAxis` dimensions

The original Phase 433 parser intentionally extracted only facts whose prefix resolved to the SEC ECD namespace and whose local concept appeared in its ECD allowlist. Therefore, it preserved the standard ECD facts and context dimensions, but silently omitted the CARG-specific modification and expiration facts.

This matters because plan lifecycle is part of the signal definition. If a filing reports a modification or issuer-specific expiration fact and the parser drops it, the resulting plan state can be stale or incomplete.

Primary SEC evidence:
- CarGurus Item 408 table and gross/net share caveats: https://www.sec.gov/Archives/edgar/data/1494259/000095017024056957/R10.htm
- The same filing's issuer-specific modification flag and expiration-date concepts, including CARG-specific IndividualAxis and TradingArrAxis members: https://www.sec.gov/Archives/edgar/data/1494259/000095017024056957/R10.htm
- Filing index and acceptance metadata: https://www.sec.gov/Archives/edgar/data/1494259/000095017024056957/0000950170-24-056957-index.htm

## Parser change

Updated `research/phase433_item408_ixbrl_parser.py`:

1. Keep standard ECD facts in the existing `facts` collection.
2. Add standard ECD modified-flag concepts to the allowlist.
3. Preserve issuer-specific IX facts in a separate `issuer_extension_facts` collection when their local concept names match Item 408 arrangement/lifecycle patterns (Rule/NonRule 10b5-1, TrdArr, TradingArr).
4. Preserve the extension namespace URI, original prefix, context, dimensions, period, unit, scale, raw value, nil state and hidden state.
5. Report separate standard and extension fact counts; total Item 408 fact count includes both.
6. Do not reinterpret extension facts as standard ECD facts, infer direction, infer active-plan status, or aggregate amounts.

This is a conservative preservation layer, not a universal semantic mapper. Issuer extension concepts still require issuer-specific review and should not be mapped to a common feature solely from their names.

## Regression tests

Added `research/test_phase437_item408_issuer_extension_facts.py` with a synthetic Inline XBRL fixture using the actual CARG extension concept names observed in the SEC rendering. Tests cover:

- Standard ECD and issuer extension fact separation.
- Preservation of CARG modification and expiration facts.
- Preservation of a false modification flag rather than dropping it.
- Custom namespace URI and IndividualAxis dimension preservation.
- Standard ECD modified-flag recognition.
- Exclusion of unrelated custom facts such as Revenue.
- Correct extraction status when extension facts exist.
- Continued preservation of the original ECD facts.

**Important limitation:** the regression fixture is synthetic. The parser has not yet been run against the original downloaded CARG filing bytes, and the new extension layer has not been validated across a representative issuer population. Raw-byte acquisition still requires the configured SEC_USER_AGENT integration.

## Admission decision

| Gate | Result |
|---|---|
| Detect custom CARG Item 408 extension concepts in SEC rendering | PASS |
| Preserve custom extension facts separately | PASS in synthetic regression |
| Preserve dimensions and original context | PASS in synthetic regression |
| Run parser on raw CARG filing bytes | NOT RUN |
| Cross-issuer extension taxonomy coverage | NOT ESTABLISHED |
| Complete plan lifecycle reconstruction | NOT ESTABLISHED |
| Signal, returns, incremental LTM/F80, OOS, bootstrap, LOO or holdout | NOT TESTED |

**Decision:** parser robustness improved; Item 408 remains a conditional research source only. No alpha or signal admitted. No trading code, production, frozen baseline, universe, holdout, capital or exposure changed.

## Reproducibility

- Parser: `research/phase433_item408_ixbrl_parser.py`
- Tests: `research/test_phase437_item408_issuer_extension_facts.py`
- Existing workflow: `.github/workflows/phase433_item408_ixbrl_parser.yml` extended through Phase 437; no new workflow created.
