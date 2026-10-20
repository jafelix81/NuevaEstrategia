# Smart Money Research State

## Phase 26A — FINRA OTC/ATS feasibility
**Status:** PROMOTE_WITH_ACCESS_UNCERTAINTY

The official FINRA metadata endpoint confirms `OTCMARKET/WEEKLYSUMMARYHISTORIC` and describes a rolling four-year historical window, weekly partitions, and fields including issue identifier, firm CRD and weekly summary information. The production data endpoint does not support unauthenticated GET and returned HTTP 405; the authenticated/mock route returned HTTP 401 without credentials. Therefore no signal is built from OTC/ATS data until reproducible access and point-in-time publication timing are established.

**Decision:** Do not treat off-exchange activity as smart money by assumption. Keep the source conditional on access.

## Phase 27A — SEC Form N-PORT feasibility
**Status:** CREATED / PENDING RUN

SEC Form N-PORT provides monthly portfolio holdings for registered management investment companies and eligible ETFs. The SEC publishes quarterly structured datasets covering October 2019 through September 2026. The public dataset page states that holdings are reported for each month and that only information disseminated by the Commission is included.

Potential hypothesis: aggregate changes in institutional fund/ETF holdings may contain incremental information versus frozen LTM/F80, especially when measured as ownership breadth, net value change, concentration, or persistence rather than raw fund activity.

Critical safeguards:
- use dissemination/filing availability, not portfolio month-end, as the knowledge date;
- account for amendments and restatements;
- distinguish fund/ETF ownership from directional informed trading;
- map securities historically using stable identifiers, never current ticker alone;
- audit universe coverage before modeling;
- do not download multi-hundred-MB datasets merely to prove feasibility;
- no model construction until schema, identifier mapping, ex-ante timing and coverage pass audit.

**F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.**
