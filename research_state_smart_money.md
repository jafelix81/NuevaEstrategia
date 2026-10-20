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
**Status:** RUNNING / FEASIBILITY AUDIT ONLY

27H generalizes the 27G correction across four historical pairs: 2019Q4→2020Q4, 2021Q4→2022Q4, 2023Q4→2024Q4, and 2025Q4→2026Q3. Each pair is processed independently in a matrix job to avoid the long sequential SEC ZIP processing that previously caused runner cancellations. The audit measures series counts, common-series continuity, frozen-335 universe coverage, identifier ambiguity and usable signal breadth.

No alpha is being tested in 27H. No return data is used and no production model is changed. Promotion to an alpha test requires materially broader and sufficiently stable longitudinal coverage; otherwise N-PORT will be archived and the research line will move to another Smart Money source.

**F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.**
