# Phase 541 — CFTC TFF cadence transition and PIT recheck

**Audit cutoff:** 2026-11-21 05:22 UTC  
**Disposition:** the TFF Futures Only dataset remains weekly in observed prospective captures. Existing weekday polling is structurally adequate for the announced COT semiweekly transition. Historical rows have useful depth but no defensible full-history first-publication clock; they remain excluded from feature eligibility.

## 1. Official CFTC schedule versus actual TFF behavior

On 2026-10-27, the CFTC announced a plan to increase COT publication from once to twice weekly by the end of 2026: Monday position data on Wednesday and Wednesday position data on Friday, both at 3:30 p.m. ET. The announcement does not specify the exact activation date or prove that the TFF Futures Only Socrata resource `gpe5-46if` has transitioned.

Official announcement: https://www.cftc.gov/PressRoom/PressReleases/9316-26

At this audit cutoff, the official 2026 release calendar still lists the November dates 6, 16 (holiday-delayed), 20 and 30 (holiday-delayed). The COT landing page/FAQ continues to describe the normal weekly Tuesday-position / Friday-publication process. No separate Wednesday TFF report date has appeared in the prospective `gpe5-46if` capture ledger.

Official release schedule: https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm  
COT reports and FAQ: https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm

**Decision:** do not relabel TFF as semiweekly based on the general COT announcement alone. Require actual new TFF report dates and prospective first-receipt observations.

## 2. Prospective TFF evidence

The append-only prospective ledger contains two report vintages per tracked contract:

| Report date | First receipt UTC | Capture run |
|---|---|---:|
| 2026-11-10 | 2026-11-18 03:44:57Z | 44232546204 |
| 2026-11-17 | 2026-11-21 03:17:36Z | 44860341977 |

The latest report date advances by seven calendar days, consistent with weekly rather than semiweekly reporting. The 2026-11-17 snapshot was scheduled for publication on 2026-11-20; the collector first observed it at 03:17:36Z on 2026-11-21. That timestamp is the conservative pipeline first-receipt clock, not a claim about the exact instant the data first became public.

The latest capture appended one new report per contract (four contract events). The archive now contains 3,043 rows:
- E-mini S&P 500, Nasdaq Mini and DJIA x $5: 853 weekly rows each, 2010-07-20 through 2026-11-17.
- Russell E-mini: 484 rows, 2017-08-15 through 2026-11-17.

There are no gaps exceeding eight days in the four contract histories. This is useful historical coverage, but report dates are not publication timestamps. The CFTC FAQ says historical release-date listings are only maintained for the most recent 13 months; therefore the archive cannot be promoted to a full-history PIT panel merely by assigning report dates or assuming a fixed Friday release. Historical backfill remains excluded from features, labels and returns tests.

## 3. Capture cadence and atomic-batch controls

The current Phase 384 workflow polls on weekdays at 22:25 UTC, after the CFTC's announced 3:30 p.m. ET publication time. Daily polling is adequate to observe either Wednesday or Friday releases if the semiweekly schedule reaches TFF. The actual capture timestamp remains authoritative for research eligibility; schedule delays are never backdated.

Phase 395's atomic-batch guard remains essential: at most the newest newly observed report per contract in a single API response is eligible. Older catch-up reports returned in the same response, revisions and late arrivals remain ineligible. They cannot be ordered into artificial sequential observations merely because their report dates differ.

No cron change is needed now. Continue the existing weekday capture and watch the actual TFF report-date pattern.

## 4. Existing hypothesis remains weekly-only

Phase 387 is a preregistered **weekly** index-futures crowding/downside-risk hypothesis. It is not Phase 23C's killed adaptive directional search and must not be re-optimized.

Its fixed design requires:
- 52 prior, prospectively first-seen weekly observations for the prior-only percentile reference;
- at least 150 valid prospective evaluation observations per contract, including at least 30 high-crowding and 100 non-high observations;
- a four-report outcome-maturity gap and completed 20-session outcomes before training;
- dependence-robust inference and separate ES/NQ reporting.

At one observation per week, the full warm-up/training/evaluation/maturity design is measured in years, not weeks. Do not accelerate the weekly sample count by treating two reports in a week as two weekly observations.

If TFF actually becomes semiweekly, Phase 387 remains frozen. A separate preregistration must preserve economic time units: a one-year reference window would require approximately 104 semiweekly observations, not 52. It must also redefine outcome overlap, maturity, event-count gates and dependence-aware inference before forward returns are inspected.

## 5. Interpretation

TFF categories are aggregate regulatory classifications, not verified identities of informed investors. The CFTC explains that trader categories are based on Form 40 business-purpose classifications and do not reveal individual traders or their reasons for holding positions. Index-futures positioning can be tested as a broad market-regime/risk-context feature; it cannot identify accumulation or distribution in individual F80 equities.

Phase 540's two-vintage normalized net/OI changes remain mixed across contracts and categories. No common risk-on/risk-off pattern is established. Two prospective vintages are not enough for a rolling percentile, stable persistence estimate or predictive test.

## 6. Cross-source operational state

- **FINRA Reg SHO:** prior scheduled run [44860690600](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600) received eight HTTP-200 files and rejected all eight for `duplicate_symbol_in_consolidated_file`; zero valid or eligible observations. Phase 539 PR [#197](https://github.com/jafelix81/NuevaEstrategia/pull/197) has now been merged to main at [c7666f03](https://github.com/jafelix81/NuevaEstrategia/commit/c7666f03a6e01c569fce7b98e1651490bf2376dc). Its metadata-only diagnostic is fail-closed. The next natural scheduled poll must validate it; no manual dispatch or rerun was made.
- **SEC Form 4/Form 144:** scheduled runs [44846461134](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134) and [44847230610](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44847230610) succeeded. The strict crosswalk has three descriptive matches and zero signal-eligible matches. The two Atea proposed sales remain classified as option-exercise/tax-planning related, not discretionary bearish sales.
- **Phase 20C:** price-history coverage remains 328/335. Seven inactive/renamed/acquired names still need terminal/successor total-return and corporate-action reconstruction.

## Frozen controls

- `F80_TOP20_PARTIAL50_BASELINE_C20` unchanged.
- Historical CFTC backfill not feature-eligible.
- New signals admitted: **0**.
- No return/alpha test, OOS, bootstrap, LOO, holdout, exposure, cost, universe or production change.
