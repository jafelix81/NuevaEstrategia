# Phase 44 — Cboe Equity Option Volume Feasibility Gate

**Date:** 2026-10-27  
**Status:** FEASIBLE_PUBLIC_CANDIDATE_PENDING_SYMBOL-COVERAGE_AUDIT  
**Baseline:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Why this source is worth testing

Cboe publishes historical options-volume data across its exchanges. Its historical-data interface allows historical options volume to be downloaded by symbol, product type, or all symbols, with daily/weekly/monthly/annual aggregation. Cboe also maintains an equity-option-volume archive reaching back to 2006; starting September 2019, historical equity-options volume is available through the historical-options-data download interface.

This is materially more accessible than contract-level options flow/open-interest/IV datasets, which remain commercially licensed. It therefore provides a credible public fallback for the options branch without weakening the PIT standard.

The richer Cboe Open-Close dataset is also economically attractive but licensed: Cboe documents EOD participant-capacity buckets (customer, professional customer, broker-dealer, market maker), buy/sell and open/close fields, with C1 history back to January 2005 and BZX/C2/EDGX history from 2018. This confirms that the economically strongest options hypothesis is feasible in principle, but it is not reproducibly available to this repository without licensed access and therefore must not be approximated with inferior public proxies.

## Candidate hypothesis

Options activity may contain incremental information about informed positioning or attention when it is unusually large relative to the underlying security's normal activity. The interpretation is deliberately agnostic: high option volume can reflect hedging, speculation, market making, or information. We do **not** assume it is "smart money."

Primary candidate features, to be specified before OOS testing:

1. abnormal option volume relative to the symbol's own trailing history;
2. option-volume acceleration/change;
3. option volume relative to underlying share volume / dollar volume;
4. persistence of abnormal option activity;
5. interaction with frozen LTM/F80 rank rather than replacement of LTM/F80;
6. only if the source provides a defensible directional split, evaluate call/put imbalance separately. Do not infer direction from raw option volume.

## Feasibility requirements before alpha testing

- establish exact historical start/end dates available for the requested symbol-level files;
- verify coverage of the frozen universe at representative dates;
- verify ticker continuity and symbol changes;
- identify the actual publication/download availability date for each historical partition and apply a conservative knowledge-date rule;
- verify whether historical files are revisions or immutable snapshots;
- document exchange coverage and any methodology changes;
- avoid mixing Cboe-only activity with OPRA-wide activity unless coverage is explicitly understood;
- compare all candidates against the same frozen LTM/F80 universe, dates, exposure and costs.

## Kill conditions

Do not proceed to alpha if symbol-level coverage is materially incomplete, PIT availability cannot be established, or the data cannot be reproduced. Do not use raw option volume as evidence of informed trading.

## If the gate passes

Run a chronological incremental test versus frozen LTM/F80. No factor selection on the final OOS period. Evaluate IC/rank behavior, portfolio spread, incremental C20 return, drawdown/volatility, bootstrap confidence intervals and leave-one-period-out stability. Use identical exposure and costs. A positive result is not promotable unless the effect is economically plausible and survives OOS/LOO/ bootstrap checks.

## Current conclusion

**Proceed to actual-file and symbol-coverage audit.** This source is a promising low-cost complement to the commercial Cboe contract-level options datasets, but there is currently **no alpha evidence** and no justification to alter the frozen baseline.

## Official source verification (2026-10-27)

- Cboe Historical Options Data documents symbol/product/all-symbol downloads and daily through annual aggregation.
- Cboe states its Equity Option Volume Archive reaches back to 2006 and that the historical-download mechanism covers equity-options volume from September 2019 onward.
- Cboe DataShop documents Open-Close EOD history from January 2005 for C1 and from January 2018 for BZX/C2/EDGX, but access is licensed.

Official sources:
- https://www.cboe.com/us/options/market_statistics/historical_data/
- https://datashop.cboe.com/cboe-options-open-close-volume-summary
