# Phase 187 — ORATS Near-EOD public sample, measurement semantics and PIT feasibility

**Audit date:** 2026-11-07  
**Status before hosted sample:** conditional broad options-context candidate; not signed flow, not strict historical PIT, no alpha test authorized. Public sample audit is executed by the path-filtered hosted workflow. No paid data, account, vendor contact, return test, holdout or production change.

## Executive decision

ORATS Near-EOD is a materially lower-cost, broad-coverage options-context candidate than exchange-specific participant-flow subscriptions. Its public product page advertises a daily US equity-options chain snapshot 14 minutes before the close, over 5,000 symbols, historical data since 2007, and individual pricing of $599 one-time for history plus $99/month for new daily files. This is a vendor claim and individual pricing display, not a confirmed professional/institutional license quote.

The data can provide option volume, prior-night open interest, NBBO, IV and model-derived Greeks. It does not provide aggressor direction, open/close classification, participant capacity or beneficial-owner identity. It must not be called Smart Money flow. Its appropriate role is IV/skew, option-activity and liquidity context alongside a genuinely signed-flow source.

## 1. Officially documented product scope

- Near-EOD snapshot: 14 minutes before the close; full US equity options chain; 5,000+ symbols; history advertised since 2007.
- Recurring daily files: product documentation says each day's file is ready each night at midnight; the recurring subscription starts from the subscription date and does not include earlier data.
- Historical archive: one-time download from ORATS-hosted S3; access window is 14 days after purchase.
- Published individual pricing on the current product page: $599 one-time historical Near-EOD archive; $99/month recurring daily delivery.
- One-minute chain product: history from August 2020; published individual pricing $1,500 one-time historical and $199/month recurring; storage/transfer charges are separately estimated at $1,000–$2,000. The API page separately says OPRA-information coverage is 1,270 tickers from January 2022; do not conflate that subset with the 5,000+ chain universe.
- Professional/institutional pricing and business-use terms are not established by the individual price display and require separate written confirmation before any use.

Official references:
- https://orats.com/near-eod-data
- https://orats.com/university/historical-data
- https://orats.com/one-minute-data
- https://orats.com/intraday-data-api
- https://orats.com/docs/historical-data-api

## 2. Measurement semantics

The ORATS data dictionary defines:
- call/put volume as the total daily contracts traded at the time observed; for a 15:46 ET snapshot this is cumulative activity up to that snapshot, not an interval increment and not signed flow;
- call/put open interest as OCC open interest updated the previous night, not same-day opening activity;
- bid/ask and implied-volatility fields as option-market context;
- smoothed IV/Greeks and theoretical values as model-derived;
- stockPrice / spotPrice as put-call-parity-derived reference values for internal use, not independent stock prices.

No trade aggressor, buy/sell initiation, open/close state, participant type, clearing capacity or beneficial-owner identifier is documented in this product. Do not infer opening demand from volume or delta OI alone.

## 3. PIT and historical-vintage ruling

The historical archive is a retrospective backfill. A timestamp such as updatedAt/quote time is not the first time a subscriber received the file. The recurring product's nightly-midnight availability claim is useful for a prospective capture process, but it is not a historical per-file first-receipt ledger or proof that old backfill files were immutable as originally disseminated.

For any future prospective use:
1. Capture the first delivered file after receipt, with UTC receipt timestamp and raw SHA-256.
2. Preserve every replacement/correction as a new immutable vintage.
3. Trade no earlier than the next regular session after actual receipt for the daily file.
4. Join to an independent, effective-dated stock-price/security master; do not use ORATS put-call-parity reference price as the return series.
5. Resolve adjusted option deliverables, ticker changes and inactive/delisted names.

Until then: historical first receipt, revision lineage, inactive-name coverage and strict PIT remain unverified; no historical alpha test is authorized.

## 4. Public sample audit

The workflow downloads only the sample linked by ORATS University (ORATS_SMV_Strikes_20240103.zip). It stores no raw rows, symbols or contracts. It reports row count, distinct underlyings, contract-key duplicates, trade-date consistency, required-field completeness, timestamp timezone/shape, zero/missing volume/OI/IV diagnostics and hashes. The sample is one date only; it cannot establish continuous 2007–present coverage or historical inactive-name retention.

Hosted result and aggregate artifact are added to this report after the workflow completes.

## 5. Research disposition

- Retain ORATS Near-EOD as a conditional, low-cost IV/skew/option-activity context candidate.
- Do not rank it as a participant-flow or informed-trading source.
- Prefer it for a possible broad-universe context panel only after sample integrity, inactive/delisted coverage, adjusted-contract mapping, professional license and prospective first-receipt capture are resolved.
- Do not use ORATS-derived underlying prices for equity returns.
- Keep signed-flow hypotheses separate: IVolatility/TradeFlow aggressor inference; Cboe/Nasdaq venue-specific open/close capacity; ORATS context controls.
- Any eventual signal must be tested against LTM/F80 with identical exposure/costs, chronological OOS, block bootstrap, issuer LOO and multiple-testing control.

No purchase, vendor contact, alpha/return test, holdout use or production change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## Hosted sample execution — schema correction and contract-identity follow-up (2026-11-07)

### First attempt: parser assumption corrected
- Run [42388926580](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42388926580) downloaded the public ZIP (66,808,802 compressed bytes; archive SHA-256 `e04a37310b0f453fedc03a000c55adfc517a119279150173916ebdc5fb514570`) and found one CSV member, `ORATS_SMV_Strikes_20240103.csv`, with 39 columns (member SHA-256 `e97a9835c4ed56da50b61656f1cb8811b8e5e69ffb74e1d9f3d5ca2a75ff39ae`).
- The first parser incorrectly required `updatedAt`. The flat-file sample does not contain it. The job stopped before row iteration; artifact [13580856815](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42388926580/artifacts/13580856815) contains metadata only. This was an auditor defect, not a source-file failure.

### Second attempt: row-level sample diagnostics
- Run [42390402753](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42390402753) used the corrected optional-timestamp parser and completed row iteration. It found **716,822 rows**, **5,787 distinct underlying symbols**, one CSV member and 39 columns.
- Core structural checks passed: zero trade-date/filename mismatches, zero missing required values, zero invalid strikes/expirations and zero invalid/negative volume or OI values.
- The incomplete key `ticker + trade_date + expiration + strike + root` produced 1,590 candidate collisions (715,232 distinct partial keys). The auditor incorrectly treated these as confirmed duplicate contracts and failed the sample gate. The file has no `root` or `optionSymbol` column, so these are **partial-key collisions**, not proven duplicate records.
- The sample also contains `cOpra` and `pOpra` columns. The public Near-EOD field list reviewed does not define these two fields. Their values must remain opaque until semantics are verified. The next audit records only nonblank/unique counts, pair uniqueness and string-length distributions; it never persists the raw codes or assumes they are valid option identifiers.
- IV zero/missing diagnostics: call/put mid-IV 14,867/18,852 rows (2.07%/2.63%); call/put bid-IV 387,949/417,371 (54.12%/58.23%). Zero call/put volume rows were 599,189/621,057; zero call/put OI rows were 354,006/419,702. These are diagnostics, not proof of missing data or a signal.
- The second run's metadata-only artifact is [13581540031](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42390402753/artifacts/13581540031). No raw rows, symbols or opaque codes were persisted.

### Correction in this revision
- Separate the structural file gate from partial-key identity diagnostics. Partial-key collisions no longer masquerade as confirmed duplicate contracts or invalidate the CSV's core schema/row checks.
- Add opaque `cOpra`/`pOpra` pair diagnostics (coverage, unique counts, pair collisions and lengths) without asserting their meaning. A unique pair is only a candidate identifier; semantics, adjusted deliverables and historical identity remain unverified.
- A structural sample pass still does **not** admit historical PIT: no per-file first-receipt ledger, immutable correction vintages, full historical coverage or inactive-name coverage has been proven.

No purchase, vendor contact, alpha/return test, holdout use or production change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.


### Third attempt: regression-control correction
- Run [42390781028](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42390781028) compiled successfully but stopped in the offline suite: 12/13 tests passed. The remaining test referenced `controls.raw_contracts_persisted`, which was present in member metadata but omitted from the archive-level controls object. No sample download occurred and no artifact was produced.
- This commit adds the missing archive-level `raw_contracts_persisted` and `raw_opaque_codes_persisted` flags. It does not change the structural/identity admission rules or authorize PIT/alpha use.
