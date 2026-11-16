# Phase 442 — Norgate terminal-return, Python API and licensing gate recheck

**Audit time:** 2026-11-16 19:17 UTC  
**Disposition:** Norgate remains a credible daily-price / stable-asset-ID cross-check, but **is not sufficient as the sole total-return label source for a survivorship-safe FINRA Phase 20C study**. Its own documentation says it does not provide delisting returns or terminal recovery values. CRSP remains the preferred return/delisting benchmark if licensed access is available.  
**Scope:** documentation and provider-contract recheck only. No account, trial, purchase, vendor contact, data download, return test, alpha test, OOS, bootstrap, LOO or holdout use.

## 1. Repository and Actions preflight

- Main HEAD at start: `21502d5ccd2fb3223a70315e9fa322c3a2154702` (Phase 441).
- Latest 100 Actions runs: 62 success, 37 failure, 1 cancelled. Total runs reported: 7,676.
- Explicit status inspection found **zero queued, in-progress, requested or waiting runs**.
- Audited 276 branches across three API pages (100/100/76), 56 open PRs and 67 workflow files. No Phase 442 branch or PR existed. No workflow was dispatched, rerun or duplicated.
- Latest run: [43918910577](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43918910577), Phase 350 SEC 13D/G parent retrieval, created 2026-11-16 17:29:27 UTC. Offline validation passed; job `133480557295` failed at contact validation because `SEC_USER_AGENT` was empty. The SEC archive retrieval step was skipped and no artifact was produced. PR [#37](https://github.com/jafelix81/NuevaEstrategia/pull/37) remains open awaiting that repository secret.
- Latest SEC Form 144 capture: [43862500790](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43862500790), created 2026-11-16 11:59:13 UTC, successful. The capture appended 55 feed observations (50 Form 144 + 5 Form 144/A), found zero new accessions/events, and reported no feed-window gap. Metadata-only artifact [14223876987](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43862500790/artifacts/14223876987), ZIP SHA-256 `a1a806b330723ab6d8487727518b80fe70ea3ed93a9a30a93720a09f904d74aa`.
- Latest CFTC TFF run: [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200), created 2026-11-13 23:03 UTC. This was a **push/bootstrap**, not a scheduled prospective capture. Logs show 11/11 tests, 3,035 historical warm-up rows, zero signal-eligible historical rows, and `BASELINE_ALREADY_EXISTS_NO_OVERWRITE`; no persistent capture change. Artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705), SHA-256 `c7a652038336f852e3c51792d1bdc96ebc1368176bdafdae0693332fb4224eef`.
- At this audit, the CFTC's holiday-delayed TFF/COT release was still scheduled for **2026-11-16 20:30 UTC**; the existing Phase 384 capture is scheduled for 22:15 UTC. No early or duplicate poll was run. The CFTC semiweekly announcement remains a planned end-2026 regime change; the current release calendar has not yet demonstrated a TFF semiweekly cadence.

This phase reuses, rather than repeats, the broader source comparison in [Phase 390](PHASE390_FINRA_PUBLIC_SECURITY_MASTER_FEASIBILITY_2026-11-14.md) and the provider ranking in [Phase 414](PHASE414_FINRA_PRICE_PROVIDER_CANDIDATE_AUDIT_2026-11-15.md). The new work is limited to a targeted recheck of the Python interface, terminal-return semantics, revision policy and current EULA.

## 2. What Norgate can do

Official Norgate documentation and the Python package documentation establish:

- US Stocks **Platinum** includes daily history back to 1990, delisted securities and historical index constituents. The US Listed/Delisted dataset is described as essentially complete from late 1992 for its included security types, subject to stated exclusions.
- The three-week free trial exposes Platinum-level features, including delisted securities and historical index constituents, but is deliberately limited to **two years of price history**. It cannot validate the complete 2016-10-24 to 2026-10-24 Phase 20C window.
- The paid Platinum history extent is sufficient in principle for that window. The current official US package page lists **USD 346.50 for six months or USD 630 for twelve months**; subscriptions are fixed-term (no monthly option). The free trial remains three weeks / two years. No quote, account or purchase was requested.
- The documented Python package supports Windows only and requires Norgate Data Updater to be installed and running. It exposes `assetid(symbol)`, `symbol(assetid)`, `price_timeseries(assetid, ...)`, `index_constituent_timeseries` and `major_exchange_listed_timeseries`.
- The Python interface supports explicit adjustment choices: unadjusted, capital reconstructions, capital plus special distributions, and total-return adjustment. Date padding can be disabled.
- Norgate's `assetid` is documented as stable through symbol/name changes, exchange/OTC transitions, delisting and corporate actions. This is materially better than a ticker-only join.

Official documentation:
- [Norgate US stock packages and current price](https://norgatedata.com/stockmarketpackages.php)
- [Norgate data FAQ](https://norgatedata.com/data-package-faq.php)
- [Norgate Python package/API](https://pypi.org/project/norgatedata/)

## 3. The newly decisive limitation: no delisting return

Norgate explicitly states that it **does not provide the reason for delisting or a delisting return / terminal recovery value**. It recommends that users close a simulated position on the final available trading bar. It also states that there is no information about events after a security delists.

That is not sufficient for a strict total-economic-return label when a security delists during the forward measurement window. The final quoted price may be a useful mark, but it is not necessarily the cash, stock consideration, bankruptcy recovery or final distribution received by shareholders.

Consequences:

1. Norgate can supply daily OHLCV and a stable asset identifier for covered securities.
2. Norgate alone cannot complete every terminal outcome for delisted securities.
3. A final-bar liquidation convention would be an explicit approximation, not an observed delisting return. It must not be silently substituted for terminal proceeds.
4. For Phase 20C, where forward outcomes may cross a merger, cash acquisition, bankruptcy or liquidation, a source with explicit delisting returns / payment information remains necessary.

Norgate's official FAQ: https://norgatedata.com/data-package-faq.php#delisting-return

## 4. Identity, revisions and PIT limits

### Identity

- `assetid` is stable, but Norgate says it does not provide prior symbols/tickers or their change dates; only the current symbol and current company name are exposed.
- It does not provide CUSIP/ISIN as alternative identifiers.
- A historical ticker that has been superseded may not be directly searchable under the old symbol. A separate, defensible mapping from the original 335-name list to Norgate assetids is still required.
- Daily historical index membership is available at Platinum level, but announcement dates are not. This can support an index-defined universe; it cannot reconstruct the user's arbitrary fixed 335-name list or its unrecovered original selection rule.

### Revisions and price adjustment

- Norgate states that corrections to trades, corporate actions, dividends, listing status and surviving-entity determinations are applied continuously.
- There is **no notification or versioning mechanism** for those corrections.
- A retrieval-time snapshot and SHA-256 can make the downloaded file reproducible from that point onward, but cannot reconstruct what Norgate's database contained at an earlier historical date.
- If ever tested, use raw/unadjusted prices for predictor construction where possible, and a separately frozen total-return series for ex-post outcome labels. Do not allow retrospectively adjusted historical prices to become an unexamined predictor vintage. Disable padding unless a specific feature requires it.
- These properties make Norgate an EOD price/identity source, not a historical record-known security-master feed.

## 5. Licensing and storage gate — EULA version 20261107

The current published EULA and subscription FAQ make the use boundary explicit:

- The license is to one individual and is limited to that individual's own non-commercial personal trading/research.
- Third-party cloud or hosted processing is permitted only as a tool for that individual's personal research, with the data remaining private and inaccessible to other users.
- Uploading the data to a shared/public repository or providing access to another person, business or organisation is not permitted.
- Norgate's FAQ says there is no current business/commercial license.
- Exported/extracted data must be deleted after the subscription/trial expires, unless the subscription is being renewed imminently. The EULA's definition of derived data is narrow; formatting, filtering, normalizing or compressing market data does not automatically make it retainable derived data.

Official terms:
- [Subscription & licensing FAQ](https://norgatedata.com/faq.php)
- [End User Licensing Agreement 20261107](https://norgatedata.com/subscribe/eula.php)

Operational consequence for this public GitHub repository:

- Never commit Norgate raw data, exported CSVs, assetid crosswalks, raw price rows or reconstructible transformations.
- Do not upload them as GitHub Actions artifacts or print them in public logs.
- If a future user-authorized evaluation occurs, keep licensed content in a private environment; publish only code, hashes, coverage counts and statistics that are genuinely non-reconstructible and permitted by the license.
- Do not use Norgate data for law-firm/client/business research under the current personal-use-only terms.

## 6. Comparison with CRSP

CRSP remains the preferred return/delisting benchmark if access can be obtained:

| Requirement | Norgate Platinum | CRSP US Stock Database |
|---|---|---|
| Daily US equity history | Yes | Yes |
| Active and inactive securities | Selected included types | Broad active/inactive coverage |
| Permanent security ID | Norgate assetid | PERMNO / PERMCO |
| Daily historical index membership | Yes, at eligible levels | Separate index products |
| Delisting return / terminal value | **Not provided** | Delisting data include DLRET / DLRETX and related delisting fields |
| Historical record-known revisions | No versioning | Must be evaluated separately; do not assume a full record-known clock |
| Personal-only license | Yes | License/access terms depend on subscription |

CRSP's current product description reports daily/monthly data for more than 32,000 active and inactive US securities and permanent PERMNO/PERMCO identifiers. Its stock-file layout includes a delisting table with delisting date, code, price, payment date, amount, DLRET and DLRETX.

Official references:
- [CRSP US Stock Databases](https://www.crsp.org/research/crsp-us-stock-databases-2025-layout/)
- [CRSP stock file layouts / delisting fields](https://www.crsp.org/wp-content/uploads/2023/10/crsp_us_stock.pdf)

CRSP still needs an independent PIT identity/record-known reference if mutable identity fields are predictors; its stronger terminal-return data do not automatically supply every historical record-known timestamp.

## 7. Updated decision and Phase 20C gate

**Norgate disposition: CONDITIONAL PRICE / IDENTITY CROSS-CHECK ONLY. NOT A STANDALONE TERMINAL-RETURN SOURCE.**

Do not replace Massive's Phase 414 primary-trial ranking or the Phase 412 blocker on the basis of documentation alone. If a lawful sample/trial is later authorized, Norgate can be evaluated for:
1. exact mapping of the original fixed universe to stable assetids;
2. presence and daily OHLC coverage of all seven unresolved names (AVB, EA, EQR, LPRO, ROKU, WBD, WBS) and positive controls;
3. exact 2016–2026 paid-history coverage (not established by the two-year trial);
4. split/dividend/total-return arithmetic and independent price concordance;
5. delisted terminal outcomes supplied by a separate source such as CRSP;
6. retrieval hashes, data revisions and license-compliant private storage.

The existing Phase 20C gate remains unchanged: preserve the fixed 335-name diagnostic universe and the 329-valid-history requirement; do not drop symbols, splice vendors, impute prices or claim unbiased OOS while the original 335-name selection rule remains unrecovered.

## 8. Controls

- No Norgate account, trial, subscription, quote, vendor contact or data download.
- No CRSP access request, account or purchase.
- No raw market data or assetid mapping acquired or persisted.
- No price fallback admitted; Phase 20C remains blocked at 328/329.
- No forward returns, alpha, OOS, bootstrap, LOO or holdout test.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, holdout, capital, exposure and production remain unchanged.
