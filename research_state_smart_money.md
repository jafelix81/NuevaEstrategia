# Smart Money Research State

## Phase 26A — FINRA OTC/ATS feasibility
**Status:** PROMOTE_WITH_ACCESS_UNCERTAINTY

The official FINRA metadata endpoint confirms `OTCMARKET/WEEKLYSUMMARYHISTORIC` and describes a rolling four-year historical window, weekly partitions, and fields including issue identifier, firm CRD and weekly summary information. The production data endpoint does not support unauthenticated GET and returned HTTP 405; the authenticated/mock route returned HTTP 401 without credentials. Therefore no signal is built from OTC/ATS data until reproducible access and point-in-time publication timing are established.

**Decision:** Do not treat off-exchange activity as smart money by assumption. Keep the source conditional on access.

## Phase 27A — SEC Form N-PORT feasibility
**Status:** PROMOTED TO PIT COVERAGE AUDIT

SEC Form N-PORT provides monthly portfolio holdings for registered management investment companies and eligible ETFs. The SEC publishes quarterly structured datasets covering October 2019 through September 2026. The public dataset page states that holdings are reported for each month and that only information disseminated by the Commission is included.

Potential hypothesis: aggregate changes in institutional fund/ETF holdings may contain incremental information versus frozen LTM/F80, especially when measured as ownership breadth, net value change, concentration, or persistence rather than raw fund activity.

Critical safeguards:
- use dissemination/filing availability, not portfolio month-end, as the knowledge date;
- account for amendments and restatements;
- distinguish fund/ETF ownership from directional informed trading;
- map securities historically using stable identifiers, never current ticker alone;
- audit universe coverage before modeling;
- no model construction until schema, identifier mapping, ex-ante timing and coverage pass audit.

## Phase 27D — SEC N-PORT PIT universe coverage
**Status:** IN PROGRESS / INFRASTRUCTURE FIX APPLIED

The initial all-period runner was repeatedly cancelled by the hosted runner while processing the large SEC ZIPs. It successfully completed 2019Q4 at 83.88% coverage and 2020Q4 at 88.96%, but no artifact was produced before cancellation. This is treated as an execution/infrastructure problem, not as evidence against the data source.

The audit was refactored to be period-scoped and parallelizable: four matrix jobs, each processing two historical periods, with separate artifacts. This preserves the same frozen 335-name universe, CUSIP-first mapping, conservative FILING_DATE knowledge rule, and no-survivorship policy while preventing one long sequential job from invalidating the entire audit.

**Promotion rule:** do not proceed to alpha construction until the historical coverage/mapping audit completes and shows adequate universe coverage, acceptable identifier ambiguity, and reproducible PIT timing across the sampled history.

## Phase 27G — SEC N-PORT series-panel correction
**Status:** COMPLETE / ALPHA NOT TESTED

27G corrected a methodological flaw in 27F: different fund-series panels had been compared across snapshots, so a series absent from the later snapshot could be incorrectly interpreted as a 100% position exit. The corrected panel compares only `SERIES_ID`s present in both snapshots; a missing ticker holding inside a common series is a valid zero, while a missing series is excluded from deltas. The 2021Q4→2022Q4 pilot produced only 3 common fund series and 21 usable universe tickers, so it was a methodological correction rather than alpha evidence.

## Phase 27H — SEC N-PORT longitudinal panel
**Status:** NO ACTIVE RUN FOUND / FEASIBILITY ONLY

No active 27H workflow run is currently present on the historical branch. No alpha is promoted from N-PORT. The dose-response work remains negative/unstable and N-PORT is not allowed to modify F80.

## Phase 28D — SEC 13D/13G PIT event audit
**Status:** ENGINEERING UPGRADE STAGED

The original issuer-targeted audit completed successfully on 2026-10-23 and established that filing-level PIT retrieval is feasible, but the current SEC ticker map covered only part of the frozen universe. The next engineering step uses SEC current ticker→CIK plus a historical ticker→CIK crosswalk, validates the selected CIK against SEC submissions, and then extracts economic fields from the actual filing while keeping `filing_date` as the sole PIT knowledge date.

The upgraded extractor records, when present: reporting person, reporting person type, beneficial shares, percent of class, sole/shared voting power, sole/shared dispositive power, transaction-purpose text, event date (diagnostic only), amendment status, filing lag and mapping source. This is an extraction audit, not an alpha test.

## Phase 28E — SEC 13D/13G historical CIK crosswalk
**Status:** COMPLETE

Run 39929661159 completed successfully. The audit covered all 335 frozen tickers and produced a validated identity crosswalk:
- SEC current ticker mapping: 301/335
- historical mapper mapping: 305/335
- selected CIKs: 308/335
- SEC-validated CIKs: 308/335
- unresolved tickers: 27/335
- selected CIKs with 13D/13G history in the audit window: 304/335
- mapping conflicts: 2
- validation errors: 0

The historical mapper is used only for identity discovery. It is not treated as an information source. `filing_date` remains the PIT knowledge date. The audit artifact is `phase28e-sec-13dg-historical-cik-crosswalk`.

## Other Smart Money source feasibility

CFTC COT is retained as a regime/context candidate rather than a stock-selector source: the CFTC publishes complete futures-only history back to 1986 and futures-and-options combined history from 1995, with weekly report dates. This has excellent historical depth but weak direct mapping to individual equities. citeturn0search0turn0search14

Options data remains conditional. Cboe provides historical options-volume downloads by symbol/product/month/year, but the currently verified public source does not by itself establish a complete, reproducible long-history contract-level PIT panel for open interest/IV/skew across the frozen stock universe. Therefore no options alpha is promoted yet. citeturn0search13

13F remains promising for institutional ownership because SEC describes quarterly holdings disclosures for managers over $100M, including shares and market value, but the 45-day reporting delay must be treated explicitly as the ex-ante knowledge date. SEC also publishes structured 13F datasets. citeturn0search8turn0search48

**Research rule:** no Smart Money source is promoted because it is intuitively “smart.” It must demonstrate ex-ante availability, adequate historical coverage, stable identifiers, incremental information versus frozen LTM/F80, and chronological OOS robustness.

**F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.**
