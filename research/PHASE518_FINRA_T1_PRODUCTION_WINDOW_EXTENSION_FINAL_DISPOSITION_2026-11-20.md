# Phase 518 — FINRA T1 production-window extension: final feasibility disposition

**Audit timestamp:** 2026-11-20 08:32:12 UTC  
**Run:** [44701029373](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44701029373)  
**Disposition:** COMPLETE — historical date-clock/coverage extension validated; aggregate weekly signal sample gate FAILS; no return or alpha test authorized.

## 1. Execution and integrity

The corrected Phase 518 workflow completed successfully after PR #172 merged the per-week overlap-clock repair into this feature branch.

- Offline regression job: success.
- Live audit job: success.
- 50/50 incremental weeks retrieved from FINRA `weeklySummary`.
- 3,497,002 rows retrieved across the 50 weeks.
- All pages reconciled to FINRA Record-Total.
- All 50 week-level publication clocks passed.
- Combined inventory: 259 consecutive weeks, 2021-11-15 through 2026-10-26; no duplicate weeks or gaps.
- Two historical overlap checks passed:
  - 2021-12-06: HHI 0.165246 historical vs 0.16524579 current.
  - 2024-05-20: HHI 0.172722 historical vs 0.17272223 current.
- The corrected code derives each overlap's first eligible NYSE session from that overlap's own `initialPublishedDate`; it no longer reuses the final incremental week's publication date.

Artifact: [phase518-finra-t1-production-window-extension](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44701029373/artifacts/14613284655). The artifact contains only `combined_weekly.csv` and `summary.json`; raw FINRA rows, MPIDs, CRDs, participant names and ticker strings were not retained.

## 2. Coverage and concentration interpretation

The incremental 50-week panel has:
- 49/50 weeks with revision-stable share-volume coverage at least 90%;
- 48/50 weeks at least 95%;
- one week below 90% (2026-03-23: 79.931859%);
- one additional week below 95% (2026-08-10: 94.631992%).

The combined 259-week aggregate panel includes an early 2021-11-15 partial-coverage week (5.660434% share coverage); it must not be treated as an ordinary fully covered observation.

The feature is an equal-weighted cross-sectional mean of per-symbol ATS reporting-participant concentration. It is not beneficial-owner identity, institutional ownership, buyer/seller direction, or proof of informed trading. HHI autocorrelation is high (lag 1: 0.687699, n=239; lag 4: 0.481133, n=212), so any future test must distinguish persistent market structure from predictive information and control for prior returns/momentum.

## 3. Aggregate weekly sample feasibility — FAIL

The current aggregate feature has only 259 weekly observations. The pre-coded chronological sample gates do not pass:

| Outcome maturity horizon | Matured features | Evaluation observations | High / non-high | Gate |
|---|---:|---:|---:|---|
| 5 sessions | 189 | 137 | 26 / 111 | FAIL |
| 10 sessions | 188 | 136 | 26 / 110 | FAIL |
| 20 sessions | 186 | 132 | 24 / 108 | FAIL |

Required evaluation minima are 150 observations, 30 high and 100 non-high. Each horizon fails at least the total and high-count minima.

The strict 52/52 reference rule yields only 19 valid observations (14 high). The 48/52 / 80th-percentile alternative yields 190 observations (44 high, 146 non-high), but it is explicitly exploratory and not preregistered. It is not an admitted signal definition and does not cure the chronological evaluation-sample shortfall.

**Decision:** kill the current *aggregate weekly HHI time-series test path for insufficient sample size*. Do not loosen thresholds after seeing the counts. No returns, labels, model fit, alpha, OOS, bootstrap, LOO or holdout were run.

## 4. Next feasible FINRA research unit: symbol-week panel

The historical Phase 375 audit reports 432,804 revision-stable symbol-week groups across 209 weeks (98.633996% symbol coverage and 96.943175% share-volume coverage). The Phase 518 live extension also processes roughly 2,400–2,700 symbols per week. This suggests a symbol-week panel may have materially more observations than the 259-row aggregate series.

However, neither immutable artifact retains the per-symbol feature rows; only weekly aggregates were preserved. Therefore the symbol-week panel cannot be reconstructed from the existing artifacts alone. A new, narrowly scoped query is required.

Next gate:
1. Test FINRA `domainFilters` on `issueSymbolIdentifier` for a small, predeclared sample of the frozen 335-ticker snapshot on one historical week.
2. Verify that the historical endpoint applies the domain filter exactly, preserves both `ATS_W_SMBL` and `ATS_W_SMBL_FIRM` rows, and allows the aggregate/participant bridge to reconcile.
3. If supported, estimate exact ticker-string coverage for the 335 snapshot, but label it a coverage diagnostic only: the 335-name snapshot is not a historical active-universe membership table, and ticker reuse/class changes remain unresolved.
4. Preserve only derived symbol-week features and a non-reversible or controlled join key; never persist participant identifiers or raw rows.
5. Require the effective-dated identity bridge and date-appropriate active-universe/return source before any return test.

FINRA's public Query API documentation recommends filters and documents `domainFilters`, but historical datasets have restricted filter behavior. The one-week probe must establish actual support rather than assume it. Official documentation: https://developer.finra.org/docs.

## 5. Other source status at preflight

- **FINRA Reg SHO:** latest scheduled run [44669121290](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44669121290) ran on pre-Phase-515 main SHA `8850828...`; it returned 8 HTTP-200 files, 0 valid, 8 invalid. Phase 515 passed 59/59 offline tests in PR CI [44674320007](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44674320007), but no post-merge live validation is yet evidenced.
- **SEC Form 4:** scheduled run [44656159115](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44656159115) captured 457 new accessions; 10-document structured backfill appended 22 detail rows; 1,190 accessions remain; no signal-eligible rows.
- **SEC Form 144:** scheduled run [44662324343](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44662324343) captured 70 events and appended 542 structured detail rows; ledger total 80 accessions / 596 rows; 368 accessions remain; no signal-eligible rows.
- **CFTC TFF:** run [44668300202](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44668300202) retained 3,039 rows (852 each for Dow, E-mini S&P and Nasdaq Mini; 483 Russell) and found no new report/revision. Prospective capture only; historical archive `Updated` is not an acceptable PIT clock.
- **Databento Security Master:** strongest documented identity candidate, but no API key, paid plan, sample or vendor data has been obtained. The Nov 10, 2026 migration warning means production `listing_status` is not historical PIT before the Dec 10 cutover; any pre-cutover pilot must use the preview gateway and retain API version.

## 6. Strategy and authorization

- `F80_TOP20_PARTIAL50_BASELINE_C20`: unchanged and frozen.
- Universe, parameters, exposure, costs, holdout and production: unchanged.
- New signals admitted: 0.
- Return/alpha tests: not run.
- OOS/bootstrap/LOO: not run.
- Historical signal-test authorization: false.

**Final disposition:** Phase 518 passes the data retrieval, date-clock, pagination and overlap-reconciliation gates. The aggregate weekly feature fails the predeclared sample-size gate. Continue only through a separate symbol-week feasibility probe; do not backfill or relax the aggregate sample definition to manufacture a positive result.
