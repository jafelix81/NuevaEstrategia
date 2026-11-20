## Phase 521 — FINRA historical symbol-domain filter probe (2026-11-20)

- The one-week probe against `weeklySummaryHistoric` for a predeclared 10-name subset of the frozen 335 snapshot returned HTTP 400 when using `domainFilters` on `issueSymbolIdentifier`. Run [44711398973](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44711398973) passed offline tests and completed the live diagnostic; artifact [14617172938](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44711398973/artifacts/14617172938) contains aggregate metadata only.
- Disposition: historical `domainFilters` not supported for this query. No rows, symbol coverage or concentration features were returned; 0 eligible observations and 0 signals.
- Do not retry the same filter or scale the extraction. Next bounded test: one request per symbol using `issueSymbolIdentifier = EQUAL`, plus the week and T1 partition equality filters, for the same 10-name manifest and one week. Stop if the field is not an allowed historical compare filter.
- This probe is a response to Phase 518's aggregate weekly sample gate failure; it does not change the aggregate gate or authorize any return test. The 335-name snapshot is not a historical active-universe table, and ticker identity remains unresolved.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
