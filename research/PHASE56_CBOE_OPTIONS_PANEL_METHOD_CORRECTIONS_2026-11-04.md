# Phase 56 — Cboe options panel methodology corrections
Date: 2026-11-04
Branch: phase57-miax-open-close-feasibility
Status: preregistered design refinement; no return test authorized.

## Evidence reviewed

### Cboe Open-Close EOD
- Canonical sample run: [41762583602](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41762583602), artifact 13291147097.
- EOD C1 sample date: 2025-03-28; the EOD member is explicitly a 20% sample.
- EOD rows: 23,179; current frozen-335 symbols appearing: 288 (85.97%). This is a sample reach statistic, not historical ticker coverage.
- The same ZIP includes 10-minute (78,468 rows; 302/335 names) and 1-minute (87,322 rows; 305/335 names) samples. These are separate intraday files and do not change the EOD gate.
- EOD schema gate passed. The sample is C1 only; it does not demonstrate all-four-exchange coverage or historical PIT completeness.
- Official DataShop page: https://datashop.cboe.com/cboe-options-open-close-volume-summary
- Official factsheet: https://datashop.cboe.com/documents/Cboe_Open-Close_Factsheet.pdf

Cboe documents four exchange-specific files (BZX, C1, C2, EDGX), overnight EOD delivery after midnight ET, C1 EOD history from 2005-01-03 and BZX/C2/EDGX EOD history from 2018-01-02. Total industry volume and open interest are third-party best-effort values. Historical conventions differ by exchange/date and must be corrected or excluded.

### Cboe Option EOD Summary
- Canonical sample run: [41763011186](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41763011186), artifact 13290668468.
- Sample date: 2023-08-25; 32,672 rows per variant; underlyings: ^SPX, SPY, TSLA, ^VIX.
- Only TSLA overlaps the current frozen-335 list (1/335). Therefore the sample validates schema/Calcs only; it is not evidence of universe coverage.
- Base schema and optional Calcs gates passed. Positive-IV rates were 92.75% (no-CGI variant) and 91.26% (CGI/historical variant); positive OI 77.20%; positive trade volume 40.35%. Zero/invalid Greeks/IV must not be treated as valid zeros.
- Official product page: https://datashop.cboe.com/option-eod-summary
- The product page documents full-OPRA U.S. stock/ETF/index options, 15:45 and EOD NBBO snapshots, EOD OHLC/volume/VWAP/OI, optional 15:45 IV/Greeks, and history from January 2012. Options on futures and non-U.S. markets are excluded.

### OCC Volume Query
- Corrected full-universe run: [41763113005](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41763113005), artifact 13292225481.
- The completed job log reports 645/670 valid ticker-date queries (96.27%): 325/335 on 2025-01-03 and 320/335 on 2026-11-02. All valid rows had matching Activity Date; no HTTP/query errors.
- The data-depth gate is explicitly FAIL_FOR_LONG_OOS: OCC returned an explicit 24-month retention limit at 2024-01-03.
- Returned fields are quantity, underlying, option symbol, account type, call/put, exchange and activity date. With the all-series query it does not return strike, expiry, buy/sell aggressor, open/close or actual OI. PIT publication timestamp is unverified.
- Decision: recent complementary aggregate only; not a long-history participant-flow substitute.

## Required methodological corrections before panel construction

1. **Contract multiplier and deliverables.** Replace the unscaled prototype with:
   `net_open_delta_shares[p,t] = Σ_i delta_1545[i,t] × multiplier[i,t] × (open_buy[i,p,t] - open_sell[i,p,t])`.
   Obtain multiplier and deliverable from a point-in-time OCC series/reference source. Never assume multiplier=100 for every series. Exclude adjusted/non-standard contracts until their deliverables are deterministically resolved. The same rule applies to closing flow.

2. **15:45 Delta is a mark, not trade-time Delta.** The daily Open-Close file aggregates all-day exchange activity, while Option EOD supplies a 15:45 Greek snapshot. Label the resulting feature `15:45-marked delta-equivalent flow`, not exact executed delta. Keep unweighted net opening contracts as a separate baseline diagnostic; do not add post-hoc Greek transformations.

3. **Venue coverage.** Cboe participant classifications describe Cboe-exchange executions, not all OPRA executions. Do not call the Cboe flow total-market flow. Join to full-OPRA Option EOD volume and report venue share/coverage by underlying-date. Do not use `total_industry_vol` as the denominator until its third-party provenance, units and historical conventions are independently reconciled.

4. **Open interest denominator.** Use prior-available-session OI as the primary normalization denominator. Do not divide by same-day OI until the precise measurement/publication convention is verified. Keep raw signed flow, prior-OI-normalized flow, full-OPRA-volume-normalized flow and underlying-ADTV-normalized delta notional as separately named variables.

5. **Economic units.** A dollar delta proxy is `underlying_price × net_open_delta_shares`. Normalize by prior 20-session underlying dollar ADTV (known before the event). Preserve raw contract counts and participant categories; do not pool categories before separate tests.

6. **Historical optionability and coverage.** The denominator is not automatically all 335 equities. Build the point-in-time set of F80 members with listed/traded OPRA option series on each date using the full-OPRA Option EOD panel. Report (a) all-335 reach, (b) historically optionable F80 reach, (c) daily optionable ticker-date completeness, and (d) Cboe share of full-OPRA volume. Missing exchange rows are not proof that a stock was not optionable.

7. **Exact series join.** Join by trade date, underlying, root, expiration, strike and put/call; retain exchange for Open-Close. Use an OCC historical series map for adjusted roots, multiplier and deliverable. No fuzzy root mapping.

8. **PIT and execution.** Cboe Open-Close EOD is delivered overnight after midnight ET. Option EOD is daily but its exact historical delivery timestamp has not been evidenced. Set conservative KnowledgeDate to the next trading session for both. Because the frozen strategy's execution convention is end-of-day, the first comparable signal execution is the close of that next session; apply identical execution timing to baseline and augmented portfolios. Preserve raw trade date, delivery/acceptance timestamp, KnowledgeDate and execution date separately.

9. **Taxonomy.** Cboe's factsheet says Customer includes retail and institutional clients; Pro Customer includes professional traders and institutional participants; Firm is proprietary trading firms/market participants; Market Maker is a liquidity-provider category. These are exchange capacity labels, not beneficial-owner identities or proof of informed trading. The factsheet's approximately 98% classification statement must not be described as 98% of total OPRA market share.

## Updated data gates

- Full-OPRA Option EOD: obtain a representative 335-symbol pick-list extract (including historical/delisted names where available) for multiple dates and measure actual overlap with the PIT F80 optionable universe. The four-underlying public sample cannot pass this gate.
- Cboe Open-Close: obtain exact EOD files for all four exchanges and a full, non-sampled date; validate per-exchange coverage, daily completeness, units and historical convention breaks.
- Historical series metadata: obtain PIT OCC series/deliverable/multiplier mapping.
- PIT: retain evidence of actual delivery timestamps or use the conservative next-session rule.
- Licensing: confirm internal-use and derived-data permissions and exact pick-list/Calcs price before bulk retrieval.
- Only after these gates pass may the preregistered incremental tests against frozen LTM/F80 begin.

No forward returns were used in this addendum. No alpha claim. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
