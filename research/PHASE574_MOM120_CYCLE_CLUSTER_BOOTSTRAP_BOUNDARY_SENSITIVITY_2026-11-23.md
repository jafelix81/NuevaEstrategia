# Phase 574 — MOM120 cycle-cluster bootstrap and boundary sensitivity re-audit

**Audit cutoff:** 2026-11-23 12:27 UTC  
**Main HEAD at preflight:** `7e20efe193e08e3ad8bc543b45dd567b2936ff08`  
**Disposition:** additional dependence-aware sensitivity analysis of the already-examined Phase 426 historical OOS window; promising diagnostic, not fresh OOS evidence and not eligible for promotion.

## 1. Preflight

- Actions API: 8,074 total runs; latest 100 = 96 success / 4 failure; zero queued/in-progress.
- Latest natural Form 144 run remains [45137579123](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45137579123), with both jobs successful and Phase 565 post-capture reconciliation passed.
- Latest natural Form 4 run remains [45133809578](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45133809578), with both jobs successful.
- No newer run appears in the repository-wide run inventory at this cutoff. The next Form 4 :17 slot was only 10 minutes past its nominal minute; no new delivery-gap conclusion was added. Form 144's next :47 slot had not yet arrived.
- Branch census: 373 (100 + 100 + 100 + 73); open PRs: 72.
- Main research state and Phase 573 report were reviewed. No workflow was dispatched or duplicated.

## 2. Immutable input and reproducibility

Re-downloaded Phase 426 Actions artifact [14191029663](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43789923762/artifacts/14191029663) from run [43789923762](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43789923762).

- ZIP SHA-256: `2ae79509bb090c8e024f97b074fe1351b8a8747541091150cc991493a2d4450b`
- Input file: `paired_exposure_matched_excess_C20.csv`
- CSV SHA-256: `4ac2215f18ba67d0f5b21a5549928a34fc37872e4a8361e42a4ea3112f846b1d`
- 721 paired daily observations, 2024-01-02 through 2026-11-13.
- The artifact's data-coverage manifest says 335/335 tickers loaded but `point_in_time_security_master=false`; the universe remains survivorship/identity limited.

## 3. Method

For each stored `cycle_id`, calculate:

- Daily paired excess = `DailyReturn_mom - DailyReturn_ltm`.
- Cycle mean daily excess.
- Compounded relative return = product(1 + MOM120 daily return) / product(1 + LTM daily return) - 1.

Then resample whole cycle clusters with replacement (200,000 bootstrap draws; NumPy seed `20261123`) and calculate percentile 95% intervals for the equal-cycle mean daily excess. This avoids treating 721 serially dependent daily observations as 721 independent observations.

Two boundary treatments are reported:
1. All 10 observed cycle groups, including the initial 6-session boundary fragment.
2. The 9 comparable/near-comparable groups after excluding only that initial 6-session fragment. The terminal 75-session group is retained. Exclusion is for cycle-length comparability, not because of its return.

The sign test is descriptive and assumes independent cycles; it is not treated as definitive inference with only 9–10 clusters.

## 4. Results

| Cycle treatment | Clusters | Positive relative cycles | Equal-cycle mean daily excess | 95% cycle-bootstrap CI | One-sided sign-test p | Minimum leave-one-cycle-out mean |
|---|---:|---:|---:|---:|---:|---:|
| All groups | 10 | 8/10 | 2.734 bps | -3.432 to 7.478 bps | 0.0547 | 1.637 bps |
| Exclude 6-session initial stub | 9 | 8/9 | 5.340 bps | 2.554 to 8.362 bps | 0.0195 | 4.431 bps |

Additional checks:

- Day-weighted mean daily excess: 5.169 bps with all groups; 5.386 bps excluding the initial stub.
- The 6-session initial stub (2024-01-02–2024-01-09) was negative: -20.712 bps mean daily excess and -1.250% compounded relative return.
- Cycles 23–30 each contain 80 sessions and all eight were positive on a compounded relative basis.
- The terminal 75-session cycle (2026-07-31–2026-11-13) was negative: -1.273 bps mean daily excess and -0.968% compounded relative return.
- The 9-cluster mean log relative return is 0.04204 per cycle (4.294% after exponentiation); this is a historical relative comparison, not an annualized forecast.

The original Phase 426 circular block bootstrap at C20 reported a positive 80-session-block 95% interval of 2.463–7.922 bps/day. This reanalysis is directionally consistent when comparing the 9 comparable cycles, but the all-10 boundary treatment crosses zero. The boundary sensitivity must remain visible. The reproducible script reports the 9-cycle equal-cluster interval as 2.554–8.362 bps/day and the day-weighted interval as 2.614–8.376 bps/day.

## 5. Reproduction

- Script: [phase574_mom120_cycle_cluster_bootstrap.py](phase574_mom120_cycle_cluster_bootstrap.py)
- Unit tests: [test_phase574_mom120_cycle_cluster_bootstrap.py](test_phase574_mom120_cycle_cluster_bootstrap.py)
- Local validation: 3/3 tests passed.
- The script verifies the source CSV SHA-256 and 721-row count, uses 200,000 cluster-bootstrap draws with seed `20261123`, and emits both boundary treatments. Input is `paired_exposure_matched_excess_C20.csv` from artifact 14191029663.

## 6. Interpretation and disposition

This supports retaining MOM120 as a **promising historical diagnostic**: its exposure-matched excess was positive in 8 of 9 comparable/near-comparable cycles, and the cycle-cluster bootstrap interval was positive under that boundary definition.

It does **not** establish a new or independent edge:

- The 2024-01-02–2026-11-13 period was already examined in Phase 426; this is not a fresh holdout.
- Only 9 comparable cycle clusters exist; cluster independence and regime breadth are limited.
- The all-10 treatment, including the initial boundary stub, produces a confidence interval crossing zero.
- The 335-name universe is not point-in-time and is not survivorship-free.
- The input prices are not a point-in-time vendor vintage.
- MOM120 is a momentum reweighting highly correlated with LTM, not evidence of institutional or informed trading.
- No new feature residualization against LTM was possible from this artifact because it contains portfolio returns and checks, not the underlying point-in-time cross-sectional factor panel.

**Decision:** retain the candidate for prospective shadow tracking and a future conditional/residual test, but do not promote, retune, consume the final holdout, or change production. A valid next test requires a point-in-time security master, a genuinely untouched prospective sample, residualization/conditioning on LTM, identical exposure and costs, and dependence-aware bootstrap/LOO at the signal-cycle level.

## 7. Frozen controls

- `F80_TOP20_PARTIAL50_BASELINE_C20`: unchanged and frozen.
- Universe, parameters, capital, exposure, costs, holdout and production: unchanged.
- New Smart Money signals admitted: 0.
- New independent OOS observations: 0.
- New model fit or production test: none.
