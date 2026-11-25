# Phase 46 — Cboe public historical options-volume archive disposition

**Audit date:** 2026-11-25 UTC  
**Evidence:** [Actions run 40841944879](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40841944879), artifact [12882404738](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40841944879/artifacts/12882404738).  
**Disposition:** `KILLED_FOR_FROZEN_F80_UNIVERSE`.

## Actual-file coverage result

The Phase 46 workflow downloaded and parsed four public Cboe monthly symbol-rank workbooks. The frozen comparison universe contained 335 tickers.

| Month | Unique symbols in file | Frozen-universe matches | Coverage |
|---|---:|---:|---:|
| 2018-01 | 2,938 | 216 | 64.48% |
| 2018-12 | 2,873 | 229 | 68.36% |
| 2019-01 | 2,889 | 233 | 69.55% |
| 2019-08 | 2,893 | 238 | 71.04% |

Minimum observed coverage was **64.48%**. Three of four representative files failed the project's predeclared 70% minimum-coverage gate. The workflow correctly returned `FAIL_FILE_SCHEMA_COVERAGE`.

## Research decision

Kill this public monthly symbol-rank archive as a candidate input for the frozen 335-name Smart Money research line.

Reasons:

1. Universe coverage is below the predeclared threshold in three of four sampled months.
2. The archive is a monthly, symbol-level volume ranking; it is not a contract-level OPRA tape and does not provide the signed trade/NBBO, opening/closing, participant-capacity, open-interest, implied-volatility or skew detail required by the higher-value options hypotheses.
3. The archive does not expose a historical file-publication/first-receipt timestamp. A month label cannot establish ex-ante availability.
4. Restricting the strategy to the covered subset or imputing missing tickers would change the frozen universe and risk selection/survivorship bias.

The 2019-08 file's 71.04% coverage does not override the failure in the other sampled months. Do not use these workbooks as a predictive feature, do not infer informed trading from aggregate volume, and do not run an alpha/backtest on this source.

Cboe's public page describes the archive as historical options volume downloadable by symbol, product type or all symbols for a month/year, and cautions that the volume/put-call information is supplied without a guarantee of accuracy. That is useful descriptive market context, not a complete institutional-flow dataset. See [Cboe Historical Options Data Download](https://www.cboe.com/us/options/market_statistics/historical_data/).

## Keep separate from paid-data feasibility

This kill applies only to the public monthly symbol-rank archive. It does **not** adjudicate the separate, paid OPRA-wide Option Trades/Option Quotes products or Cboe Open-Close EOD studied in Phase 547. Those products remain conditional data-feasibility candidates only; exact 335-name/date coverage, actual first-receipt/correction vintages, pricing and license terms remain unverified. No sample, vendor contact, quote request, purchase or license acceptance is authorized. The current options-data budget remains USD 0.

## Frozen strategy disposition

- `F80_TOP20_PARTIAL50_BASELINE_C20` unchanged.
- No signal admitted; no return test, OOS, bootstrap or LOO performed.
- No change to universe, capital, exposure, costs, parameters or holding period.
- PR #7 is closed without merging the failed audit workflow; this disposition preserves the measured result and kill reason.
