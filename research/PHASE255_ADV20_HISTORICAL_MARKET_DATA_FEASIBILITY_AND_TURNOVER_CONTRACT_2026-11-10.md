# Phase 255 — ADV20 historical market-data feasibility and dollar-turnover contract

**Audit date:** 2026-11-10 UTC  
**Disposition:** source feasibility audit completed; no vendor source admitted under current access/licensing and historical-vintage evidence. ADV20 calculation contract PASS, 26/26 hosted tests.  
**Scope:** public documentation audit and synthetic feature-contract validation only. No account creation, API key, vendor contact, purchase, raw vendor download, SEC bulk request, return test or holdout use.

## Executive decision

The strongest practical candidates for the Form 144 proposed-sale denominator are:

1. **CRSP** as the research-quality benchmark if an authorized WRDS/CRSP subscription is available: daily and monthly data, active and inactive securities, survivor-bias-free history and permanent PERMNO/PERMCO identifiers.
2. **Massive** as the strongest API-oriented candidate for the 2023–2026 event window: 5-year daily bars on Starter, historical date-based ticker reference data, delisted symbols, and a daily VWAP/volume pair. However, its published individual market-data terms restrict non-professional personal use and prohibit non-display/derivative investment-strategy use unless separately licensed. Its historical security-master rows are effective-dated current vendor records, not preserved original vintages. No individual plan is admitted.
3. **Sharadar** has strong EOD coverage of active and delisted US stocks back to December 1997 and split-adjusted price/volume, but the published license is personal-use only and excludes professional, commercial and organizational use. A separate commercial arrangement would be required.

Norgate, Tiingo and Nasdaq Data Link remain secondary or unadmitted candidates for the specific 289-issuer Form 144 panel. No data provider has been purchased or contacted.

## 1. Source feasibility matrix

| Source | Historical coverage / delisted | Identity and PIT evidence | License / access decision |
|---|---|---|---|
| CRSP US Stocks | Daily/monthly data and corporate actions for 32,000+ active and inactive US securities; inception 1926/1965 | Permanent PERMNO/PERMCO; survivor-bias-free history. Exact original release-vintage semantics still need confirmation. | **Preferred research benchmark if authorized access exists.** Subscription information required; no access verified. |
| Massive (formerly Polygon) | Listed US bars from 2003-09-10; Starter has 5 years, Developer 10, Advanced all history. All Tickers can return past-date listings and delisted symbols. Five-year window covers the Form 144 panel beginning 2023-04-13 as of 2026-11-09. | Date-based lists are effective-dated but are the vendor's current maintained records, not archived historical versions. No permanent ID survives every security change; share_class_figi is the better join where present but can change/be missing; CIK is issuer-level and cannot distinguish classes. | **Strong API candidate, not admitted.** Published individual terms are non-professional/personal; non-display or investment-strategy derivatives require a separate license, and upload/hosting restrictions make GitHub Actions processing unsuitable without written permission. |
| Sharadar SEP | Active and delisted US public stocks; 21,000 tickers; history to 1997-12; daily delivery at 17:30 and 23:30 ET; reporting lag under one day. | Corporate-actions table covers ticker changes, splits, listing/delisting and delist reasons. `lastupdated` is a sync field, not an immutable first-receipt archive. Published stock fields include split-adjusted close and split-adjusted volume; no daily VWAP is documented in the stock table. | **Not admitted under personal license.** Published terms exclude professional, institutional, commercial and organizational use; commercial access would need a separate arrangement through Nasdaq or another channel. |
| Norgate | Platinum-level trial includes delisted securities and historical index constituents, but the three-week trial is limited to two years of history. | Local updater; historical index constituent features are useful, but original receipt/vintage semantics are not established here. | **Trial insufficient for the full Form 144 period.** As of 2026-11-09 it cannot cover the earliest 2023 events. |
| Tiingo EOD | 30+ years advertised; raw and adjusted OHLCV. | EOD corrections can update through the evening (published availability around 17:30 ET, corrections until 20:00 ET); no explicit delisted-history/security-master guarantee was established in this audit. | **Not admitted** until delisted coverage and effective-dated identity are demonstrated. |
| Nasdaq Data Link Bars | 10+ years of historical bars for US-listed and OTCBB securities. | Current product description does not establish a complete delisted/security-class crosswalk or immutable historical vintages. | **Not admitted** until delisted coverage, identifier continuity and commercial permissions are verified. |

### Evidence and important limitations

- CRSP describes daily/monthly market data and corporate actions for 32,000+ active/inactive securities, permanent PERMNO/PERMCO identifiers and survivor-bias-free history: [CRSP US Stock Databases](https://www.crsp.org/research/crsp-us-stock-databases-2025-layout/).
- Massive says its All Tickers endpoint can construct past-date US stock lists back to 2003-09-10, including subsequently delisted companies, but it has no permanent identifier; share_class_figi can be missing or change, CIK does not identify a share class, and past-date rows are the vendor's current maintained record rather than a historical copy: [security-master FAQ](https://massive.com/knowledge-base/article/does-massive-have-a-downloadable-security-master).
- Massive's listed-stock bars begin 2003-09-10; plan history is 2 years Basic, 5 Starter, 10 Developer and all history Advanced: [history FAQ](https://massive.com/knowledge-base/article/how-much-historical-stock-data-does-massive-have).
- Massive's VWAP `vw` is the size-weighted average of every trade that contributes to the bar's volume `v`, including some trades that do not set high/low. Thus `vw × v` is the best documented reported-turnover measure in this candidate, not executable liquidity: [VWAP methodology](https://massive.com/knowledge-base/article/how-is-a-stock-bars-vwap-calculated-and-why-can-it-fall-outside-the-high-and-low).
- Massive emits no placeholder bar when no eligible trade exists. A missing bar is not a zero-volume observation and cannot be silently filled: [missing aggregates FAQ](https://massive.com/knowledge-base/article/why-are-there-missing-aggregates-in-massives-data).
- The currently published market-data terms PDF is still titled Polygon.io and dated 2024-10-09. It limits individual access to personal, non-business/non-commercial use; prohibits non-display or derivative investment-strategy use unless separately licensed; and restricts copying/uploading market data to other servers without prior written consent. Current commercial terms must be confirmed before any use: [Market Data Terms](https://massive.com/terms/market_data_terms.pdf).
- Sharadar documents active and delisted stocks, split-adjusted close/volume, 21,000 tickers and December 1997 history: [Stock Prices](https://sharadar.com/docs/stocks). Its published terms are personal-use only and exclude professional or organizational use: [License Terms](https://sharadar.com/terms).
- Norgate's official FAQ limits its free trial to two years even though it includes Platinum-level delisted/index-constituent features: [Norgate trial FAQ](https://norgatedata.com/data-package-faq.php).
- Tiingo's EOD documentation says corrections may arrive through 20:00 ET and both raw and adjusted prices are available: [Tiingo EOD documentation](https://www.tiingo.com/documentation/end-of-day).

## 2. ADV20 feature definition

For a Form 144 filed on date (D), the proposed denominator is based on exactly the 20 completed XNYS sessions strictly before (D). The session list must come from an authoritative XNYS calendar and is supplied explicitly to the calculation contract.

For each session (t):

[
DV_t = VWAP_t 	imes Volume_t
]

[
ADV20_D = rac{1}{20}sum_{t=1}^{20} DV_t
]

The proposed-sale scale measure is:

[
ProposedNotionalADV20Days_D =
rac{ProposedSaleNotional_D}{ADV20_D}
]

Interpretation is deliberately narrow: proposed notional relative to recent reported dollar turnover. It is **not** an executed sale, a forecast of actual selling pressure, or a market-impact estimate.

### Required controls

- VWAP and volume must use the same share basis: both raw or both split-adjusted. Mixed bases are rejected; dividend-adjusted prices are not admitted for turnover.
- Decimal volume is preserved; no integer truncation.
- No close×volume fallback in the primary contract. VWAP×volume is used where the vendor documents that VWAP and volume cover the same trade set.
- Exactly 20 distinct expected XNYS sessions must be supplied, all strictly before the Form 144 filing date.
- Same-day/future bars, duplicates, missing sessions, invalid values and unknown adjustment bases fail closed.
- A missing bar is UNKNOWN, not zero-filled. Massive explicitly emits no placeholder when no eligible trade exists; without trade-level/completeness evidence, a missing session cannot be distinguished safely from an incomplete observation.
- The caller must provide the authoritative XNYS calendar; this helper checks the supplied session set but does not itself implement or validate the exchange calendar.
- Massive's VWAP includes volume-eligible odd-lot, average-price and contingent trades. This is a reported-turnover measure, not a measure of immediately executable displayed liquidity. A trade-condition-filtered sensitivity would require a separately licensed trade-level source.

## 3. Implemented contract

New helper: `research/phase255_adv20_source_feasibility.py`

New tests: `research/test_phase255_adv20_source_feasibility.py`

The helper uses Decimal arithmetic and:
- calculates daily notional from VWAP × same-basis volume;
- supports raw/raw and split-adjusted/split-adjusted pairs;
- rejects mixed or dividend-adjusted bases;
- preserves fractional volume;
- validates the exact 20-session pre-event window;
- rejects missing/extra/duplicate sessions and same-day/future bars;
- never imputes a missing bar as zero;
- computes proposed-notional/ADV20 only when ADV20 is valid.

## 4. Hosted validation

The first run [42764563857](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42764563857) exposed one test-only formatting mismatch: the mathematically identical Decimal output `19500` was compared with the string `19500.0`. The expectation was corrected, then fractional-volume and split-adjustment-invariance tests were added.

An intermediate run [42764633916](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42764633916) passed 24/24. Final run:

- [Phase 255 run 42764720861](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42764720861)
- Job: `129658390045`
- Result: **26/26 tests passed**
- [Metadata-only artifact 13739416974](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42764720861/artifacts/13739416974), 421 bytes, SHA-256 `be975ca3108944ba6a65acafa28cc446bf8f37a81eddadfaba218ed2212b4a90`

The artifact explicitly records that no raw vendor data was acquired, no source license was admitted, no historical vendor vintages were verified, no ADV20 was computed for the Form 144 panel and no alpha was admitted.

## 5. Decision and next gate

No source is currently admissible for the Form 144 ADV20 panel. The preferred path is:
1. use CRSP/WRDS if an authorized subscription is available; otherwise
2. obtain a written commercial/business agreement from Massive or a commercial Sharadar/Nasdaq channel that explicitly permits non-display quantitative research, derived investment-strategy work and the intended cloud/CI processing; then
3. run a 20–30 issuer stratified sample, including delisted and multi-class issuers, and archive original files, request parameters, first receipt UTC, vendor update timestamps, SHA-256 and correction versions; then
4. measure exact class/ticker mapping and 20-session coverage before scaling to all 289 issuers.

The raw SEC XBRL pilot remains separately blocked by the missing authorized GitHub secret `SEC_CONTACT_EMAIL`. No email was guessed and no bulk request was sent.

## 6. Controls

No market data was purchased, no vendor account or API key was created, and no vendor was contacted. No Form 144 ADV20 values were calculated from live or historical vendor data. No forward returns, event study, alpha, bootstrap/LOO, chronological OOS or holdout test was run. The consumed legacy holdout was not reused. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; production, universe, capital and trading parameters are unchanged.
