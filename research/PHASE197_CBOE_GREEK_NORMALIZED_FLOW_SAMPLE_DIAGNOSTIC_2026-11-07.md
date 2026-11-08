# Phase 197 — Cboe Greek-normalized option-flow sample diagnostic

**Audit date:** 2026-11-07  
**Hosted run:** [42426000132](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42426000132)  
**Artifact:** [phase197-cboe-greek-normalized-flow-sample, 13594768613](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42426000132/artifacts/13594768613)  
**Disposition:** SAMPLE MEASUREMENT PASS; STRICT PIT AND ALPHA NOT ADMITTED.

## 1. Reproducible sample

The public Cboe CALCS sample for 2026-01-07 contains 74,999 populated prints, one underlying and 308 distinct contract tuples. The base and CALCS members reconcile on their core trade rows. The sample archive SHA-256 is a02504e156db28b3f007d9d25a534e4c88ffd8d24ac43f3bf84885583a3d10b8; the canonical core-row digest recorded by Phase 194/196 is 4dd0e041ca3b1921a2f5a6a3825a9505be234947736232fb47f18e93c74d1b06.

The hosted job passed compilation, **12/12 offline tests**, public sample retrieval, sample-only control checks and metadata-only artifact upload.

## 2. Exact-at-NBBO sample measurements

| Metric | Result |
|---|---:|
| Prints | 74,999 |
| Classified prints | 52,346 |
| At ask | 24,649 prints / 172,313 contracts |
| At bid | 27,697 prints / 209,076 contracts |
| Other NBBO classes, not signed | 149,838 contracts |
| Ask minus bid contracts | **−36,763** |
| Gross delta units, no multiplier | 98,071.4443 |
| Signed underlying delta units, no multiplier | −8,224.0943 |
| Underlying-delta imbalance | **−8.385819%** |
| Option-demand absolute-delta imbalance | +0.285221% |
| Vega imbalance | −6.953840% |

The raw trade-delta sign matched the call/put convention in all 74,656 nonzero-delta rows. There were 343 zero-delta rows and zero negative-vega rows.

The negative underlying-delta proxy is the combined effect of candidate call selling and candidate put buying. The option-demand absolute-delta proxy is close to balanced. These are descriptive quantities from exact-at-bid/ask prints only, not verified buyer/seller identities or beneficial-owner positions.

## 3. Interpretation and limits

- One date and one underlying do not establish cross-sectional or temporal stability.
- 149,838 contracts were not assigned a direction under the conservative exact-at-bid/ask rule.
- Contract multipliers and adjusted deliverables were not applied or independently verified.
- Trade conditions were not filtered; current condition/exchange maps are not effective-dated historical reference data.
- quote_datetime was not used because the public sample's time-only field remains semantically unresolved.
- Trade execution time is not first-receipt/knowledge time. No immutable historical first-receipt ledger was available.
- The result is not a measure of institutional participation. Execution price relative to NBBO is only a buyer/seller initiation proxy.

**Decision:** retain the Greek-normalized calculation as a measurement specification for future multi-date testing, but do not optimize the one-day imbalance or admit it as a feature. First obtain multi-date/multi-underlying coverage, effective-dated condition semantics, verified multipliers/deliverables and actual first-receipt vintages. Then test Flow→Stock and Flow→Option separately against frozen LTM/F80 with identical exposure, costs, chronological OOS, bootstrap and LOO.

## 4. Controls

No forward-return or alpha test was run; no holdout was used; no data were purchased; no vendor was contacted; production was not changed. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

**Audit-trail correction:** at the time of this Phase 198 commit, the repository contained the Phase 197 Python audit, tests, workflow and hosted metadata artifact, but no standalone Phase 197 Markdown report or committed result summary. This file and its companion JSON close that documentation gap; they do not add or alter sample rows.
