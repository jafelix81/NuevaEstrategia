# Phase 133 — OCC Flex Reports equity open-interest historical feasibility result

**Date:** 2026-11-05  
**Live run:** [42097577204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42097577204)  
**Job:** 127491551422 (success)  
**Artifact:** [phase133-occ-flex-oi-historical-audit](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42097577204/artifacts/13448395010)  
**Artifact SHA-256:** 55abe7c48dd74bdcc9fdca6009deef6cb3e8fef5d157e94eb11cf91c08f0a318

## 1. Execution result

- Python compilation: PASS.
- Seven offline regression tests: PASS.
- Seven fixed-date public endpoint requests completed.
- Artifact uploaded successfully.
- No fixed 335-name universe was used.
- No returns, alpha, feature selection, vendor purchase/contact or production changes.

## 2. Historical-depth result

The endpoint returned the literal 30-byte message "File requested does not exist." for 2018-01-03, 2020-01-03, 2022-01-03 and 2024-01-03. It returned non-empty report files for 2025-01-03, 2026-01-05 and 2026-11-04 (2,016,332; 2,600,900; and 3,685,316 bytes, respectively).

The OCC Flex Reports UI explicitly states that data are available for the past 24 months. This agrees with the fixed-date boundary probes: the 2024-01-03 request is outside the accessible window, while the 2025/2026 samples are inside it. See the [official Flex Reports page](https://www.theocc.com/market-data/market-data-reports/series-and-trading-data/flex-reports).

**Long-history gate: FAIL.** This endpoint cannot supply the multi-cycle history needed for the primary chronological OOS study.

## 3. Schema adjudication and parser limitation

The live files are not ordinary CSV files. The response includes page/system headers and fixed-width report content. The Phase 133 generic CSV parser did not identify the record columns; its row_count values (11,325; 14,938; 21,485) are parser line/row counts, **not validated contract-row counts**. It found zero parsed OI values and zero verified contract keys. Do not treat those counts as a successful contract-level data parse.

The official [Flex Open Interest Record Layout](https://www.theocc.com/getcontentasset/c4bbef04-3062-46d5-865c-2361036e8c99/dfc3d011-8f63-43f6-9ed8-4b444333a1d0/flex-open-interest-record-layout.pdf) documents eight fields: Symbol, Put/Call, contract month/day/year, strike, mark price and open interest. It also documents a strike-format change effective 2017-03-25. That confirms the intended report is series/contract-level, but does not cure the parser failure or the 24-month retention limit.

The three recent files contain internal system-generation timestamps (19:27:18 ET on 2025-01-03; 19:23:23 ET on 2026-01-05; 19:33:24 ET on 2026-11-04). The HTTP responses had no Last-Modified or ETag; the HTTP Date is the retrieval date (2026-11-05), not the historical release date. Internal generation time is not proof of first public availability.

## 4. PIT and economic interpretation

- Public first-release time: NOT VERIFIED.
- Historical correction/vintage policy: NOT VERIFIED.
- Broad point-in-time underlying coverage, including inactive/delisted issuers: NOT VERIFIED.
- OI is contract inventory, not buyer/seller aggressor side, opening/closing intent, beneficial-owner identity or proof of informed positioning.
- The endpoint does not supply an IV/skew surface or Greeks in the documented OI record layout.

## 5. Decision

**Close Phase 133 as FAIL_FOR_LONG_OOS / RECENT_CROSSCHECK_ONLY.** Do not invest in a fixed-width parser for this endpoint unless a new, decision-relevant use case emerges. Its 24-month window cannot support a long multi-cycle OOS study, and its PIT release time is not verified.

The OCC Volume Query line (Phase 53B) independently has a 24-month window and lacks buy/sell side and open/close fields. Neither OCC endpoint should be called standalone Smart Money flow.

The highest-priority options candidate remains Cboe C1 Open-Close EOD (Phases 114/115), because its advertised history is much longer and its public sample supplies participant-capacity × buy/sell × open/close aggregates. It still requires historical archive accessibility, broad PIT underlying identity, final-file availability/revision handling and licensing gates. No purchase or vendor contact is authorized.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
