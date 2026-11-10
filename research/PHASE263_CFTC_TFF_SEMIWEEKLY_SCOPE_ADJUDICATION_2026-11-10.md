# Phase 263 — CFTC TFF semiweekly-scope adjudication

**Audit date:** 2026-11-10 UTC  
**Disposition:** retain the existing weekly TFF assumption until the CFTC explicitly confirms TFF scope and an updated TFF release schedule is observable.  
**Research role:** publication-regime and capture-readiness audit only; no positioning feature or return test.

## Executive decision

The CFTC announced on 2026-10-27 a plan to publish COT data twice weekly by the end of 2026: Monday positions on Wednesday and Wednesday positions on Friday, both at 3:30 p.m. ET. The announcement frames the change as a response to feedback from the agricultural community and refers to more timely information about activity in agricultural markets. It does not explicitly identify Traders in Financial Futures (TFF) or specify a TFF implementation date.

As of 2026-11-10, the current CFTC COT page still describes weekly Tuesday-position / Friday-publication reporting, its FAQ still says the report is published once a week, and the public release schedule remains weekly. The current TFF futures-only and futures-and-options-combined files both show report date **2026-11-03**. No official TFF Wednesday/Friday schedule or two-report-per-week TFF observation was found.

**Decision:** do not infer that the semiweekly announcement applies to TFF. Keep the existing weekday polling protocol, which already accommodates either cadence without changing the event clock. This is a scope clarification, not a claim that TFF can never move to semiweekly publication.

## 1. Evidence reviewed

| Official evidence | Observation on 2026-11-10 | Interpretation |
|---|---|---|
| CFTC Release 9316-26, 2026-10-27 | Twice-weekly COT plan by end-2026; Monday→Wednesday and Wednesday→Friday at 15:30 ET; announcement context is agricultural markets | Does not explicitly confirm TFF scope |
| COT landing page | Describes weekly reports based on Tuesday positions and Friday release | Current public index still reflects weekly regime |
| COT FAQ, frequency answer | Says the report is currently published once per week | Current FAQ has not yet documented the new schedule |
| Official 2026 release schedule | Lists weekly dates, usually Fridays, with holiday shifts; no TFF Wednesday schedule | No TFF-specific semiweekly calendar |
| Current TFF futures-only file | FinFutWk.txt; current report date 2026-11-03 | One current report date |
| Current TFF combined file | FinComWk.txt; current report date 2026-11-03 | One current report date |

The COT index identifies TFF as the financial-futures report family (currencies, Treasuries, stock indexes, VIX and related financial contracts), separate from the Disaggregated agricultural/physical-market reports. TFF categories remain Dealer/Intermediary, Asset Manager/Institutional, Leveraged Funds and Other Reportables.

The CFTC explains that classifications are based on predominant business purpose self-reported on Form 40, not the reason for a specific position; individual trader classifications are not disclosed. Contract markets can also disappear when reportable traders fall below the 20-trader threshold. Therefore, category labels do not identify beneficial owners or verified informed traders, and a missing market is not zero.

## 2. Operational decision

Phase 239 already extended the existing Phase 234 CFTC capture workflow to poll both TFF streams every weekday after the 15:30 ET target. Phase 263 makes no workflow change:

- Retain the existing 20:35 UTC Monday–Friday poll and concurrency group.
- Do not create a second TFF workflow.
- Keep futures-only and combined files separate.
- Continue to hash and append each observed response version.
- First scheduled observation remains a baseline state, not a backdated report event.
- New reports become usable only from the pipeline's own first-observed receipt time; the report/as-of date is never the knowledge time.
- Same-report-date new hashes remain revision/state-only unless correction semantics are separately adjudicated.
- Manual dispatch remains non-PIT.

The scheduled capture is a conservative known-by timestamp, not proof of the CFTC's exact first-publication instant. The CFTC FAQ states that only the most recent 13 months of historical release dates are listed, so this does not repair the older historical PIT gap.

## 3. Fail-closed confirmation rule

A future TFF cadence change is admitted only when all three are present:

1. An official CFTC statement explicitly includes TFF / financial futures in the changed cadence.
2. An official TFF-specific Wednesday/Friday release schedule is published.
3. Two distinct TFF report dates are actually observed within the same publication week across the official TFF streams.

Until then, the weekly assumption is retained for interpretation and feature timing, while weekday polling remains unchanged. The rule prevents the broad COT announcement from silently changing the TFF PIT clock.

## 4. Research implications

TFF remains a broad futures-market positioning source, not a stock-level signal. Its historical report data begin 2006-06-13, but the full historical release-date series is unavailable. Categories are business-purpose classifications, not beneficial-owner identities or proof of informed trading. Stock-index futures positioning may be tested as a market-regime/context variable only after the prospective receipt protocol has accumulated enough immutable observations and the contract-market identity/missingness rules are stable.

No stock-level Smart Money feature is admitted. No returns, alpha, bootstrap/LOO, chronological OOS or holdout test was performed.

## 5. Reproducibility

- Code: phase263_cftc_tff_semiweekly_scope_gate.py
- Tests: test_phase263_cftc_tff_semiweekly_scope_gate.py
- Result: phase263_cftc_tff_semiweekly_scope_gate_result.json
- Workflow: .github/workflows/phase263_cftc_tff_semiweekly_scope_gate.yml

The deterministic suite verifies scope, official-schedule requirements, current TFF report date, two-stream separation, weekday polling continuity, no duplicate workflow, report-date/knowledge-time separation, and the no-alpha/F80 controls.

## Official sources

1. CFTC, [Release 9316-26 — Semiweekly COT publication plan, 2026-10-27](https://www.cftc.gov/PressRoom/PressReleases/9316-26).
2. CFTC, [Commitments of Traders index and methodology](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm).
3. CFTC, [2026 COT release schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm).
4. CFTC, [TFF futures-only current file](https://www.cftc.gov/dea/newcot/FinFutWk.txt).
5. CFTC, [TFF futures-and-options combined current file](https://www.cftc.gov/dea/newcot/FinComWk.txt).

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. The legacy holdout remains CONSUMED_NOT_PRISTINE and unused.
