# Smart Money Research state addendum — Phase 511

**As of:** 2026-11-19 local  
**Mainline baseline:** f9000ab6579b81b2c7946d37532a67cf5b617d86; no production change.

## New option-derived candidate

OptionMetrics IvyDB Implied Dividend is admitted as a conditional research candidate, not as a smart-money identity measure. It estimates risk-neutral future dividends from American-style single-name options. Advertised history begins 2018-01-01, but the product was publicly launched 2024-10-02 and only nightly FTP updates are documented. Historical first-delivery vintages, correction policy, exact file-ready time, and causal filter specification are not verified.

The vendor's 2018–2026 paper reports 54 bp/month gross low-gap minus high-gap, industry-neutral Sharpe 0.71 and FF6 annualized alpha 3.94% with t=1.48 (not conventionally significant). This is a vendor-authored result without a verified independent holdout or net-cost record. It is hypothesis-generating only.

## Admission gates

- Historical 2018–2024 backfill is not strict PIT absent original vintages or independent reconstruction.
- Need exact nightly receipt timestamps, revision/version policy, and confirmation the Kalman/Gaussian filter is one-sided.
- Need effective-dated SecurityID crosswalk, delisted coverage, and overlap against the 335-name F80 universe.
- Need sample, quote, license and usage rights; no contact or purchase performed.
- Preregister the dividend-gap and dividend-cut hypotheses, control for trailing yield and sector/factors, and test equal-exposure incremental value versus frozen LTM/F80 only after data gates pass.

No backtest, event study, OOS, bootstrap or LOO was run. No signal admitted. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
