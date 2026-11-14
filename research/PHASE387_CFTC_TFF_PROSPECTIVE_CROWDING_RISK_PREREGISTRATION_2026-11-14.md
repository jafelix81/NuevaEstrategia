# Phase 387 — CFTC TFF prospective index-crowding / downside-risk hypothesis

**Date:** 2026-11-14 UTC  
**Status:** preregistered design only; no forward-return test or signal admission.  
**Source:** CFTC Traders in Financial Futures (TFF), Futures Only, dataset `gpe5-46if`.  
**Initial contracts:** CME E-mini S&P 500 (`13874A`) and CME Nasdaq-100 Mini (`209742`). Russell E-mini is excluded from the initial test to avoid adding another contract-era and market hypothesis before the first two are evaluated.

## 1. Why this is a new hypothesis rather than a rerun of Phase 23C

Phase 23C tested a small, adaptive directional COT feature/direction search over 12 pseudo-OOS dates. Its results were weak and selection-sensitive; it is killed and must not be repeated or optimized.

Phase 387 asks a materially different, preregistered question: **does extreme Leveraged Money net-long positioning contain incremental information about subsequent downside risk / drawdown, rather than directional mean return?** The intended first use, if supported, is risk-regime context, not stock ranking and not a claim that Leveraged Money is informed capital.

No Phase 23C feature search, threshold tuning, horizon search, or reused pseudo-OOS/holdout is allowed.

## 2. Availability and data policy

- Historical CFTC archive rows remain schema/contract diagnostics only. They are **not** used to calculate signal thresholds, feature history, training labels, returns, or backtest observations.
- Only new report-date/contract keys first observed by the scheduled Phase 384 pipeline are eligible for this prospective study. The pipeline first-receipt timestamp is the conservative knowledge clock; a late arrival or revision is never backdated.
- A report can be used only from the first regular NYSE session strictly after its recorded first receipt. No same-day close/open is assumed.
- The weekday capture schedule is 22:15 UTC. The official CFTC schedule lists the report for positions as of 2026-11-10 for release on 2026-11-16 at 3:30 p.m. ET. The workflow is now merged to `main`; the first eligible observation must still be verified in the resulting scheduled run.
- The TFF source may change from weekly to semiweekly. The capture workflow's cadence guard must label WEEKLY / SEMIWEEKLY / IRREGULAR. The Phase 387 weekly feature definition is suspended if the observed cadence is not weekly; no weekly-to-semiweekly stitching or annualization is allowed without a new preregistration.
- Contract codes remain separate. Do not splice the pre-2017 Russell Mini era into Russell E-mini, and do not combine ICE Russell codes.

## 3. Frozen feature definitions

All positions are divided by reported open interest. Spreading positions remain separate and are never added to directional net:

- `LM_NET_OI = (Leveraged Money long - Leveraged Money short) / open_interest`
- `AM_NET_OI = (Asset Manager long - Asset Manager short) / open_interest`
- `DEALER_NET_OI = (Dealer long - Dealer short) / open_interest`
- `LM_AM_DIVERGENCE = LM_NET_OI - AM_NET_OI`
- `LM_CHANGE_4 = LM_NET_OI(t) - LM_NET_OI(t-4)`, only when all four report intervals are valid and each adjacent report gap is 6–8 calendar days.

Primary crowding variable: the percentile rank of current `LM_NET_OI) against the **prior 52 prospectively captured weekly observations** for the same contract. The current observation is excluded from its own reference distribution. At least 26 valid prior observations are required before any feature can be evaluated; the first 52 prospective observations are reserved as a warm-up period. Static historical backfill is not a substitute for this warm-up.

Primary exposure state: `HIGH_LM_CROWDING = percentile >= 80`. The threshold is fixed at the 80th percentile. No alternative thresholds are to be searched to rescue a failed result.

The Asset Manager and Dealer variables are predeclared controls / secondary descriptors. They are not independently searched for a better result in this phase.

## 4. Primary hypothesis and outcomes

**H1 (one-sided):** for ES and NQ separately, a high Leveraged Money net-long crowding observation predicts worse downside risk over the next 20 NYSE sessions than non-high-crowding observations, after conditioning on information already available at the signal time.

Primary outcome:
- maximum peak-to-trough drawdown from the first eligible session's opening price through the following 20-session window, using split/dividend-adjusted SPY and QQQ price series as transparent index proxies.

Co-primary robustness outcome:
- downside semivariance of daily returns over the same 20-session window.

Secondary, non-promotion outcomes:
- forward total returns at 5, 10, 20 and 40 sessions;
- 20-session realized volatility;
- frequency of a loss worse than the unconditional 90th-percentile loss threshold fixed from the prospective test sample only after the preregistered sample is complete.

Price and control data are aligned to the first eligible session. Entry reference is that session's regular-session open; no price observed after the entry timestamp may be used as a predictor.

## 5. Controls and incremental-information test

The baseline risk model is fixed before outcome inspection and contains:
- prior 20-session realized volatility;
- prior 20-session SPY/QQQ return;
- prior 252-session momentum;
- VIX close available before the first eligible session.

The incremental model adds only `HIGH_LM_CROWDING` and the continuous prior-only `LM_NET_OI) percentile. No interactions, nonlinear splines, feature selection or alternative category substitutions are permitted in this phase.

The first-stage question is whether TFF adds incremental information to this index-level risk model. Only if it passes may a separate portfolio-level shadow test be preregistered against frozen F80/LTM. That later test must use identical holdings, costs, execution assumptions and average realized exposure; a simple lower-exposure portfolio is not evidence of alpha.

## 6. Chronology, sample size and inference

- First 52 valid prospectively captured weekly reports per contract: feature warm-up only.
- Thereafter, observations are evaluated strictly forward in capture order. No random train/test split.
- Minimum primary evaluation sample: 150 valid prospective observations per contract, including at least 30 high-crowding observations and 100 non-high observations. If the gate is not met, continue collecting; do not relax the thresholds.
- The 20-session outcomes overlap for weekly signals. Inference must account for serial dependence using a moving/stationary block bootstrap with block length fixed at four weeks, plus HAC/Newey-West sensitivity. A naive IID bootstrap is prohibited.
- Report ES and NQ separately before any pooled summary. Pooled results cannot conceal opposite signs.
- The primary test is one-sided for worse downside risk. Report effect size, confidence interval, event count, missingness and all eligible observations. Secondary horizons are descriptive and subject to Holm adjustment; they cannot be used to promote the hypothesis if H1 fails.
- Leave-one-year-out / leave-one-calendar-regime-out sensitivity is required once enough prospective history exists. Do not consume the legacy holdout.

## 7. Kill / advance rules

Kill the hypothesis as a risk signal if any of the following occurs:
1. The primary downside-risk effect is non-positive or its dependence-robust 95% interval includes no deterioration after the minimum sample is met.
2. The result disappears after the fixed baseline controls.
3. ES and NQ have materially opposite signs without a preregistered economic explanation.
4. The effect is explained by prior momentum / volatility / VIX or by return-chasing rather than incremental positioning information.
5. Data cadence, first-receipt lineage, contract identity or price alignment fails.

Advance only to a separately preregistered F80/LTM shadow-overlay test if the primary effect is positive in the hypothesized direction, survives block bootstrap and HAC, is not driven by one calendar year, and has a plausible economic magnitude after realistic implementation costs. No live trade or production change is authorized by Phase 387.

## 8. Explicit exclusions and controls

- No use of static CFTC historical backfill for predictor features or outcome selection.
- No use of the legacy Phase 23C pseudo-OOS dates to claim replication.
- No use of the consumed legacy holdout.
- No stock-level signal, no trade instruction, no portfolio allocation, and no capital/exposure change.
- No vendor contact or data purchase.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No CAGR target and no minimum/maximum holding-period constraint is imposed on the broader strategy research; the 20-session primary risk horizon here is a hypothesis-specific outcome, not a portfolio holding-period rule.

## 9. Current status

Phase 384's prospective capture workflow has been merged to `main` in commit `e88e553afc235916e37e9236e1890b714163c229`. The hosted branch-push bootstrap passed 11/11 tests and preserved the 3,035-row historical baseline without overwriting it. The first scheduled capture is pending; until a scheduled run verifies a new report's first receipt, Phase 387 has no eligible observations.

Phase 387 is a preregistration only. It contains no empirical result and authorizes no alpha, OOS, portfolio, or production claim.
