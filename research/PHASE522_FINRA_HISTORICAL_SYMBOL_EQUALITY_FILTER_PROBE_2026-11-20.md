# Phase 522 — FINRA historical symbol equality-filter probe

**Audit timestamp:** 2026-11-20 09:34:28 UTC  
**Final run:** [44711825847](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44711825847)  
**Artifact:** [14616309604](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44711825847/artifacts/14616309604)  
**Disposition:** SYMBOL EQUALITY FILTER REJECTED (HTTP 400); historical endpoint is partition/tier-filtered only.

## 1. Probe design

After Phase 521 showed that `domainFilters` were rejected, Phase 522 tested the documented historical `compareFilters` path with:
- `weekStartDate = 2024-05-20`;
- `tierIdentifier = T1`;
- `issueSymbolIdentifier = EQUAL` for the first symbol in the same predeclared 10-name manifest.

The probe was deliberately stopped after the first HTTP 400; it did not send ten repeated rejected requests.

## 2. Result

- Initial run [44711710024](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44711710024) passed offline tests but the live job exposed a direct-script import-path defect before any FINRA request. The import was corrected in commit `21303f958610a9557d93dc4ae3638a93af5889f2`.
- Final run [44711825847](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44711825847): offline tests and live diagnostic both succeeded.
- One symbol-equality request attempted; HTTP 400; zero rows returned.
- The probe stopped immediately. No participant bridge, revision or concentration feature was evaluated.
- No raw rows, participant identifiers or ticker strings were persisted.

## 3. Official API constraint confirms the result

FINRA's official Weekly Summary dataset documentation says `weeklySummaryHistoric` requires exactly one time partition filter (`weekStartDate`, `historicalWeek` or `historicalMonth`), optionally allows `tierIdentifier`, and states: **no other fields can be used to filter the data**. It also says the historic dataset is a rolling four-year archive and recommends asynchronous requests for large-volume retrieval when timeouts occur.

Source: https://developer.finra.org/docs

Therefore both Phase 521's `domainFilters` attempt and Phase 522's `issueSymbolIdentifier = EQUAL` attempt were structurally unsupported. This is not evidence of missing symbols or zero volume; it is a query-capability restriction.

## 4. Research decision

- Do not retry symbol-level filters against `weeklySummaryHistoric`.
- Do not issue one request per ticker or scale a brute-force query.
- A symbol-week panel remains technically possible only by retrieving full week/T1 partitions and filtering symbols in memory. Phase 375 previously processed 11,917,933? No: its recorded total is **10,917,933** rows across 209 weeks; Phase 518 added 3,497,002 rows across 50 weeks. Existing artifacts retained weekly aggregates, not per-symbol features, so a panel cannot be reconstructed without a new one-time full-partition extraction.
- Do not repeat the older four-year extraction until the identity and return-data gates are resolved. FINRA says historical data older than one year is static; any future extraction should be a single planned asynchronous/batched job, not recurring re-downloads.
- The 335-name Phase 21C snapshot is not a historical active-universe membership table. Exact ticker-string overlap is only a coverage diagnostic; it cannot resolve symbol reuse, class changes, delistings or historical eligibility.
- Phase 518's aggregate weekly HHI time-series path remains killed for insufficient chronological evaluation sample size. A future symbol-week panel would be a separate hypothesis and preregistration, not a relaxation of the failed aggregate gate.

## 5. Other source priority

FINRA T1 is now deprioritized pending a justified full-partition panel extraction and identity/price bridge. The options research ranking in Phase 373 remains more promising for a future conditional pilot:
1. OptionMetrics IvyDB TradeFlow — all-U.S.-options signed-flow candidate, but product launched 2026-09-30; advertised 2016 history is backfill, not contemporaneous PIT. Licensing, versions, sample, and first-receipt gates remain open.
2. Cboe Option Trades — independent OPRA-wide trade/NBBO reconstruction candidate; no capacity, open/close or beneficial-owner fields.
3. Cboe Open-Close EOD — complementary four-venue capacity × side × open/close data; historical PIT/vintages and licensing remain open.
No purchase, trial, vendor contact or data acquisition was made.

## 6. Controls

- Returns/labels/model fit/alpha/OOS/bootstrap/LOO/holdout: not used.
- Research-observation eligible rows: 0.
- Signal-eligible rows: 0.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, exposure, costs, holdout and production remain unchanged.
