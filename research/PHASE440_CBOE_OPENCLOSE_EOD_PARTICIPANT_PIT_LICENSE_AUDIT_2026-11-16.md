# Phase 440 — Cboe Open-Close EOD participant-flow, availability, and license gate

**Audit time:** 2026-11-16 17:33 UTC  
**Disposition:** Cboe Open-Close EOD is now the strongest documented *participant-capacity × buy/sell × open/close* candidate in the current source set. It is **not** consolidated OPRA, not beneficial-owner identity, not strict-PIT admitted, and not an alpha signal. A lawful sample/eligible trial plus private data handling is required before row-level validation.

## 1. Operational preflight — repository and Actions

- Repository: `jafelix81/NuevaEstrategia`; default branch: `main`.
- Latest mainline research state before this phase records Phase 439 merged at `43bc72fa2e0f223a850058ef2a18eda516f51fbe`. The most recent observed repository commit is the Phase 439 operational preflight record `fd3b07c5d38e04e55e271ed580cc62423348132e` at 2026-11-16 16:45 UTC.
- Latest verified Actions run: [43910774320](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43910774320), Phase 439 Form 4 identity audit. Job `offline-regression` (`133451752102`) completed successfully; compile passed and all 5/5 unit tests passed. The job steps and decoded log were inspected; no artifact was configured or expected.
- The 16:45 UTC state audit reported 7,675 historical Actions runs and zero active/queued runs. This phase did not dispatch, rerun, or duplicate any workflow. The next SEC Form 144 hourly :37 slot was 17:37 UTC and had not yet arrived at this 17:33 UTC audit.
- Repository structure recheck: 274 branches (three full pages plus an empty final cursor page), 56 open PRs, and 67 workflow files. The existing draft research PRs were left untouched.

## 2. What the official EOD product actually contains

The current Cboe Open-Close product page describes four exchange-specific options datasets: BZX, C1, C2, and EDGX. Files are separate by exchange and include all option series with trading volume on the selected exchange(s). Cboe's factsheet describes the product as covering approximately 98% of trading activity; that statement is not interpreted as 98% of the entire U.S. options market. The product's explicit scope remains the four Cboe venues.

The EOD v1.3 specification (dated 2025-11-10) provides, at option-series/day grain:

- Underlying symbol, security type, option root, expiration, strike, call/put, calendar DTE, and series type.
- First/high/low/last trade prices.
- Exchange volume, total-industry volume, open interest, previous open interest, and previous close.
- Participant-capacity buckets with buy/sell and open/close dimensions: Firm, Broker/Dealer, Market Maker, Customer, and Professional Customer. Customer and Professional Customer are further split into trade-size buckets (<100, 100–199, and >=200 contracts).
- Both trade-count and contract-volume measures for the participant buckets.

The EOD file's `total_exchange_vol` counts both sides of an exchange trade. Participant buckets must not be assumed to sum to that field until tested on actual rows; the sample-level reconciliation is still open.

### Participant categories are proxies, not investor identities

The factsheet defines:
- Customer/Individual: retail investors **and institutional clients**.
- Professional Customer: professional traders and institutional participants (the factsheet describes an average of 390+ daily volumes).
- Broker/Dealer: registered broker-dealer firms.
- Firm: proprietary trading firms and market participants.
- Market Maker: designated market makers and liquidity providers.

The raw capacity codes in the EOD specification map as follows: Firm = F/L/J; Broker/Dealer = B; Market Maker = M/N; Customer = C; Professional Customer = U/W. Code W is a legacy Professional code before October 2019.

Therefore:
- Professional Customer is a useful professional-capacity proxy, not a verified institutional beneficial-owner category.
- Customer is not a pure retail category.
- Firm and Broker/Dealer must remain separate.
- No category identifies a fund, beneficial owner, account, trader, or whether the participant had private information.

## 3. Historical coverage and schema regimes

Official Cboe documentation currently lists:

| Venue | EOD history start |
|---|---:|
| C1 | 2005-01-03 |
| BZX | 2018-01-02 |
| C2 | 2018-01-02 |
| EDGX | 2018-01-02 |

The C1 EOD file has a format break beginning 2011-01-02; the pre-2011 legacy specification must be parsed separately. The series-type field changed on 2024-10-16 to add `F` for Flex options; pre-change values used S/N for standard/nonstandard series. These are separate parser regimes, not cosmetic normalization.

The product page also documents historical convention breaks already noted in Phases 355–357:
- C1 Open Interest / Previous Open Interest shifted one day ahead through 2019-10-04.
- C2 Open Interest / Previous Open Interest shifted one day ahead through 2018-05-11.
- C2 Total Industry Volume was doubled through 2018-05-11.
- C1 Total Exchange Volume used (Buy + Sell) / 2 through 2019-10-04; the later convention is Buy + Sell.
- C1/C2 Previous Close was historically venue-specific through the same respective convention dates.

The product page says all fields are sourced directly from Cboe except Total Industry Volume and Open Interest, which are third-party value-adds on a best-effort basis. The EOD spec further distinguishes preliminary and final files:
- One preliminary and one final file are delivered per day per exchange.
- Preliminary Total Industry Volume and Open Interest come from OPRA.
- Final values are sourced from OCC and may differ from preliminary values.

Never overwrite the preliminary file with the final file. Preserve both as immutable vintages, with raw-byte SHA-256, filename, trade date, venue, schema version, actual first-received timestamp, and subsequent replacement/correction lineage.

## 4. Availability clock: promising, but not certified

The v1.3 EOD specification says subscriptions typically deliver preliminary and final files between 00:30 and 01:00 U.S. Eastern the following morning. The product page describes EOD delivery as overnight after midnight Eastern. Neither statement is a guarantee of the first time our process receives a usable final file.

**Strict-PIT decision:** historical archive rows do not contain our historical first-receipt ledger. They may be used for schema/coverage research and retrospective feature warm-up, but they are not strict-PIT eligible merely because the file is labelled with a prior trade date.

A prospective capture must:
1. Poll/download both preliminary and final versions under an authorized account.
2. Record the actual receipt timestamp before parsing.
3. Preserve original bytes, SHA-256, venue, trade date, filename, schema, and response/transfer metadata.
4. Never backdate a delayed file. A feature becomes eligible only after the first verified receipt of the exact version used.
5. Keep preliminary and final snapshots separate; any later final/OCC update is a new vintage.

## 5. Coverage, feature construction, and validation gates

The historical archive includes series with trading volume on selected Cboe exchanges, not every listed option contract and not every underlying in the frozen 335-name universe. No exact F80 coverage percentage has been established. A missing underlying/series row is missing coverage, not zero flow.

Before any return test, a lawful sample or eligible trial must establish:
- Underlying coverage by date against the frozen 335-name security master, including inactive/delisted names and historical ticker/class continuity.
- Per-underlying Cboe venue share: sum of Cboe exchange volume divided by one deduplicated Total Industry Volume value per option series. Do not sum duplicated industry-volume/OI fields across exchange files.
- Row/series uniqueness across venues, option roots, adjusted/nonstandard/Flex contracts, and corporate-action lineage.
- Participant-bucket arithmetic and reconciliation against `total_exchange_vol`; preserve unexplained residuals.
- Preliminary-versus-final OI/industry-volume differences and exact version timing.
- C1 pre-2011 and participant-code/schema regimes, including the October 2019 Professional code transition and October 2024 Flex-series change.
- Missing, stale, zero, and vendor-best-effort fields as distinct states.

### Hypotheses to preregister — not signals

1. Professional Customer opening-buy versus opening-sell imbalance, separately for calls and puts.
2. Whether that imbalance differs from Customer, Firm, Broker/Dealer, or Market Maker activity.
3. Whether opening activity persists into later OCC open-interest changes; volume alone is not proof of new positions.
4. Whether any apparent relationship survives controls for Cboe venue share, total option volume, open interest, underlying liquidity, expiry/DTE, calls versus puts, and market regime.
5. Whether it adds information beyond frozen LTM/F80, and whether results survive identical exposure/costs, chronological OOS, block bootstrap, LOO, and multiple-hypothesis controls.

No delta-weighted exposure is proposed from this EOD file alone: the file does not provide trade-time IV/Greeks, and last-trade price may be stale. No “institutional” or “smart-money” label will be attached to a capacity bucket. The buy/sell/open/close fields are participant-side activity, not aggressor-side classification. Complex/auction trade-condition detail is not present at this aggregate grain.

## 6. Pricing, trial, and public-repository license constraint

The 2026 Cboe fee-schedule filing (SR-CBOE-2026-021) lists the following EOD Open-Close historical download rates:
- 1–4 years: $600 per month.
- Five or more years: $300 per month.
- Daily EOD updates: $600 per month.

The same filed schedule describes a free trial of up to six months of historical EOD Open-Close data for TPH and non-TPH recipients who have not previously purchased the historical EOD product or received a prior free trial. Eligibility and the current order terms have not been confirmed. No account, trial, vendor contact, purchase, or payment was initiated.

Licensing is decisive for this repository:
- Cboe's product page says raw data is licensed for internal use only and may not be redistributed externally.
- External distribution of derived data requires additional licensing fees and approval; the filed schedule lists a $5,000/month external-distribution fee for derived data.
- This repository is public. **Do not place raw Open-Close files, raw-derived panel data, or vendor artifacts in this public repository or its public GitHub Actions artifacts.** Do not create a workflow that uploads licensed data here. Any pilot must run in a private, license-authorized storage/compute environment; public GitHub may contain only code and non-proprietary documentation, subject to the actual agreement.

The public sample link is present on the product page, but this audit environment could not retrieve its ZIP bytes (the web fetcher rejects the ZIP content type and the container has no outbound DNS). No sample rows were inspected. This is a tooling limitation, not evidence that the sample itself is unavailable.

## 7. Decision and next gate

**Decision:** promote Cboe Open-Close EOD to the top *conditional participant-capacity × side × open/close* candidate, complementary to OptionMetrics IvyDB TradeFlow (conditional signed-flow candidate) and Cboe Option Trades / ThetaData (raw OPRA reconstruction candidates). It is not a consolidated all-market flow source, not a beneficial-owner feed, and not a strict-PIT or alpha-admitted source.

Next gate:
1. Confirm eligibility for the Cboe six-month historical EOD trial or obtain an authorized sample.
2. Keep all licensed bytes and derived panels outside the public GitHub repository.
3. Validate schema, preliminary/final vintages, arithmetic, historical convention regimes, and exact 335-name/date coverage.
4. Only then preregister a limited exploratory feature test with a conservative first-eligible session and the existing F80/LTM comparison discipline.

Other gates remain unchanged: FINRA Phase 20C 328/329 price histories; Form 4 identity only 4/15 issuers, 16/42 accessions, and 16/41 issuer-filing-date units in the Phase 346 purposive sample; CFTC TFF remains bootstrap-only until the first scheduled post-release capture; SEC 13D/G awaits the monitored-contact `SEC_USER_AGENT`. No source has been admitted to the model.

No stock-return, price-impact, alpha, incremental LTM/F80, OOS, bootstrap, LOO, or holdout test was run in this phase. No production, universe, parameter, capital, exposure, or frozen-baseline change.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
