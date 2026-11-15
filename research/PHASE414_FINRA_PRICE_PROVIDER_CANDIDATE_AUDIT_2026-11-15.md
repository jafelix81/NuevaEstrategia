# Phase 414 — FINRA Phase 20C historical price-provider candidate audit

**Audit date:** 2026-11-15 UTC  
**Disposition:** Massive Stocks Advanced is the strongest documented candidate for a controlled exact-universe coverage trial; it is NOT admitted until all 329 required histories, inactive/predecessor identities, OHLC adjustment and license conditions pass. No purchase, API key, vendor contact or data request was made.
**Research class:** provider-contract feasibility and cost/implementation ranking only. No return or signal test.

## 1. Repository and Actions audit performed first

- Main HEAD at audit start: `13363ee35563bd578da5f70e2fc64efcad6be458`.
- Inspected the latest 100 Actions runs, the first 100 branch records, all 56 open PRs returned by the API, the current research directory, relevant workflows, and the current Smart Money state. No Phase 414 branch or PR existed. No run was queued or in progress at the audit timestamp.
- The only schedule event in the latest 100 runs was SEC Form 144 run [43670461605](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43670461605), created 2026-11-15 03:01:47Z and completed 03:02:06Z. Both jobs succeeded; offline regression passed 15/15. The live job appended 55 feed observations (50 Form 144 + 5 Form 144/A), found zero new accessions/events, and flagged no feed-window gap. Its last poll receipt was 03:02:02Z. No later SEC schedule run appeared in the latest 100 by 10:15Z. This is an observed delivery gap, not proof that the workflow is disabled; do not manually dispatch or duplicate it.
- SEC artifact: [14143174642](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43670461605/artifacts/14143174642).
- CFTC Phase 384 remains a weekday 22:15 UTC capture. The last run [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200) was a push/bootstrap, not a scheduled observation; it contains 3,035 historical warm-up rows and zero eligible historical rows. Sunday had no scheduled weekday slot. Next expected run is Monday 2026-11-16 22:15 UTC, after the scheduled 20:30 UTC release.
- Existing PR #57 remains the Phase 381 fallback branch and is still a draft on a stacked base. This report does not duplicate that branch or merge any stacked PR.

## 2. Candidate ranking

| Candidate | Documented coverage / access | Price indication | Main limitation | Decision |
|---|---|---:|---|---|
| **Massive Stocks Advanced** | Listed US stock daily bars from 2003-09-10; historical All Tickers by date, including inactive/delisted records; corporate-action endpoints | $199/month, individual use only | No downloadable security master; no vendor-as-known historical vintages; older FIGI/type/exchange fields can be missing; identity joins need careful share-class handling | **Primary trial candidate, conditional** |
| Norgate US Stocks Platinum | Daily history back to 1990; selected delisted securities and historical index constituents | $630/year | Local Windows database / export workflow; trial limited to two years; package excludes some OTC-only and special delisted types | **Strong independent cross-check** |
| EODHD Historian | 30+ years EOD; delisted symbol list and EOD history; US symbol-change history | $19.99/month personal plan | Delisted before 2018 has EOD only; corporate-action detail is not documented for those pre-2018 delisted records | **Lower-cost secondary probe** |
| Tiingo Power | 30+ years price history; broad listed-symbol count | $30/month individual plan | Current pricing page does not establish delisted-security completeness or a historical point-in-time security master | **Not admitted pending delisted audit** |

## 3. Why Massive is the primary candidate

Official Massive documentation says listed US stock bars, trades and quotes begin on **2003-09-10**. Stocks Advanced exposes all of that history; its pricing page lists 20+ years and $199/month for individual use. The Phase 20C price window (2016-10-24 through 2026-10-24) is therefore inside the documented plan window.

The All Tickers endpoint supports a historical date parameter and active/inactive filtering. Historical date lists include companies that have since delisted, under the symbol/name/exchange then in force. Inactive names can be queried with active=false. This is materially better than a currently-active-only list.

However, this is an effective-dated reconstruction, **not a vintage of what the vendor knew on that historical date**. Massive explicitly says it has no downloadable security-master file, no permanent identifier surviving every security change, and older rows can lack FIGI, CIK, type or exchange fields. Share-class FIGI is the preferred join key when present; CIK plus ticker is only a fallback because CIK identifies the issuer, not the share class. The experimental ticker-events endpoint is not a substitute for a validated security master.

Massive provides separate split and dividend endpoints. Split records include adjustment_type and historical_adjustment_factor; dividends include cash_amount, split_adjusted_cash_amount and historical_adjustment_factor. Daily aggregate bars default to split adjustment, not a complete total-return series. The implementation must explicitly reconcile dividend factors and split factors, avoid double-adjustment, and retain raw OHLC plus all adjustment inputs.

Massive flat files are unadjusted and may be replaced after publication; corporate-action endpoints update daily without a published time of day. If used, archive raw responses, retrieval timestamps, hashes, API version/parameters and later revisions. Do not treat retrospective corporate-action metadata as information available to a signal on the original date.

## 4. Material risks and exact acceptance gate

Massive is a provider candidate, not a pass. Before Phase 20C can calculate any return:

1. Retrieve all 335 diagnostic-universe symbols, including inactive/delisted symbols, for the exact 2016-10-24 to 2026-10-24 window. Preserve the original 329-valid-history gate and do not drop symbols to make the test pass.
2. Demonstrate at least 220 valid daily observations for every symbol required by the existing gate, with no unexplained gaps. The seven previously unresolved symbols remain AVB, EA, EQR, LPRO, ROKU, WBD and WBS.
3. Build an effective-dated symbol/share-class crosswalk using share_class_figi where present, CIK plus ticker only as a flagged fallback, and independent SEC/issuer evidence for ambiguous classes, mergers and reused tickers. Do not use issuer CIK alone as a share-class identifier.
4. Audit inactive/delisted and predecessor records, ticker changes, merger consideration, cash delistings, splits, special distributions and dividends. Distinguish missing history from a security that did not yet exist or had already ceased trading.
5. Reconstruct split- and dividend-adjusted OHLC consistently. Verify raw-to-adjusted arithmetic on controls and corporate-action cases; do not combine adjusted close with unadjusted open/high/low.
6. Compare a stratified sample against an independent source, including AAPL/MSFT/NVDA/SPY controls and all seven unresolved names. Require price concordance within a predeclared tolerance and investigate every material discrepancy.
7. Freeze raw response hashes, retrieval timestamps, query parameters, symbol crosswalk version, corporate-action version and provider/license terms before opening any FINRA forward returns.
8. If the API returns historical membership lists, record that they are retrospective effective-date reconstructions, not original historical publication vintages. Use them only for identity/coverage unless independent evidence establishes the relevant PIT fact.

Only after all gates pass may the existing Phase 20C FINRA test resume. Keep the FINRA publication-time, next-session-open entry, costs, chronological splits, bootstrap/LOO and identical-exposure comparison unchanged. A price-source pass is not evidence of alpha.

## 5. Alternatives and why they are secondary

**Norgate Platinum** has the clearest packaged survivorship-bias-free positioning: US daily history to 1990, selected delisted securities and historical index constituents. The current official package page lists USD 630 for 12 months. Its local Windows database and export/plugin workflow are less convenient for the Linux GitHub Actions pipeline. The official trial is three weeks but limited to two years, so it cannot by itself certify the full 10-year Phase 20C window.

**EODHD** is materially cheaper and explicitly documents delisted-symbol retrieval and EOD history. Its own table says delisted securities before 2018 have EOD only, while delisted after 2018 have EOD, fundamentals, dividends and splits. That makes it a possible price probe, but not yet a sufficient corporate-action/identity solution for all delisted cases in the 2016–2026 window.

**Tiingo** advertises 30+ years of EOD history and $30/month Power access, but the current pricing page does not establish that delisted securities and a complete historical security master are covered. Do not use it to replace the failed symbols until that is documented and tested.

## 6. Decision and controls

- **Recommended next provider to test if authorized:** Massive Stocks Advanced, using a one-month individual-use subscription only if the intended use falls within that license. No subscription was started and no payment was made.
- Norgate Platinum is the preferred independent cross-check if its local Windows export can be made reproducible and its license permits the intended research use.
- EODHD may be used only as a secondary price cross-check after its adjusted-OHLC and pre-2018 delisted corporate-action limitations are resolved.
- No vendor was contacted, no credentials were requested, no API calls were made, no dataset was downloaded and no provider was admitted.
- FINRA Phase 20C remains blocked at 328/329 valid price histories. This is a data-completeness failure, not a negative signal result.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, holdout, capital, exposure and production remain unchanged. No forward-return, alpha, OOS, bootstrap or LOO test was run.

## Official source references

- Massive Stocks pricing: https://massive.com/pricing
- Massive historical stock coverage: https://massive.com/knowledge-base/article/how-much-historical-stock-data-does-massive-have
- Massive historical All Tickers / security-master limitations: https://massive.com/knowledge-base/article/does-massive-have-a-downloadable-security-master
- Massive split adjustments: https://massive.com/knowledge-base/article/does-massive-support-normal-and-reverse-splits
- Massive dividend adjustments: https://massive.com/knowledge-base/article/does-massive-adjust-historic-dividends-for-splits
- Massive aggregate adjustment conventions: https://massive.com/blog/aggs-api-updates
- Norgate US stock packages: https://norgatedata.com/stockmarketpackages.php
- Norgate trial/history FAQ: https://norgatedata.com/data-package-faq.php
- EODHD delisted data: https://eodhd.com/financial-apis/delisted-stock-companies-data-2
- EODHD pricing: https://eodhd.com/pricing/
- Tiingo pricing: https://www.tiingo.com/pricing