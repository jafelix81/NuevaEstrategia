# Phase 534 — SEC MIDAS per-security metrics: semantics, structural breaks and PIT feasibility (2026-11-20)

## Executive disposition

SEC MIDAS is a **public, historically broad market-microstructure source**, but it is not a direct measure of institutional flow or off-exchange/dark-pool activity. The public *Metrics by Individual Security* files contain daily per-security observations in quarterly ZIP releases. The official SEC page currently lists 59 quarters from 2012 Q1 through 2026 Q3, covering more than 4,800 securities.

The source is technically attractive for a slow-moving liquidity / market-quality / volatility-risk hypothesis. It is **not yet eligible for a daily historical backtest** because historical first-publication timestamps, F80-335 coverage, and a permanent/effective-dated security identity crosswalk have not been verified. No sample ZIP was successfully downloaded in this phase.

**Disposition: retain as a conditional public market-microstructure candidate; do not label it smart-money flow; no signal, return test or F80 change.**

## 1. Official coverage and acquisition scale

Official source: [SEC Metrics by Individual Security](https://www.sec.gov/data-research/sec-markets-data/marketstructuredata-security).

- Observation period shown by the SEC: January 2012–September 2026.
- 59 quarterly ZIP files are listed, from 2012 Q1 through 2026 Q3, with no missing quarter in the current SEC listing.
- SEC describes coverage of more than 4,800 securities.
- The page lists 19 columns: `Ticker`, `Date`, `Security`, `McapRank`, `TurnRank`, `VolatilityRank`, `PriceRank`, `Cancels`, `Trades`, `LitTrades`, `OddLots`, `Hidden`, `TradesForHidden`, `OrderVol`, `TradeVol`, `LitVol`, `OddLotVol`, `HiddenVol`, and `TradeVolForHidden`.
- Listed quarterly archive sizes range from 11.45 MB (2012 Q1) to 24.42 MB (2026 Q3). Summing the rounded sizes displayed by the SEC gives approximately 982.96 MB compressed for all 59 files.
- The separate *Metrics by Individual Security and Exchange* product is much larger: its 2026 Q2 archive is 189.97 MB versus 22.65 MB for the non-exchange-partitioned 2026 Q2 archive. Start with the smaller per-security panel; do not acquire the exchange-partitioned history unless a specific hypothesis requires exchange decomposition.

The 2014 Q2, 2016 Q1–Q4 and 2019 Q4 archives previously described by a third-party catalog as missing are present in the current official SEC per-security download table. This confirms current catalog presence, not the third party's ingestion history or the historical date on which each ZIP first became public.

## 2. Critical semantic correction: HiddenVol is not dark-pool volume

The SEC's *Market Activity Report Methodology* and MIDAS FAQ materially narrow what these variables mean.

- `HiddenVol` is volume from **on-exchange executions against hidden/undisplayed resting orders**.
- `TradeVolForHidden` is the denominator for exchanges where the SEC can determine whether executions involved hidden resting orders. It is not necessarily identical to total composite market volume.
- The SEC says these public market-activity metrics generally exclude off-exchange executions, opening/closing auctions and off-hours activity.
- Some exchanges are excluded from hidden-order ratios when their feeds do not permit conclusive identification. The FAQ specifically names NYSE, Amex, CHX and NSX among feeds for which hidden-order identification is unavailable in the described calculation.
- The MIDAS system itself collects off-exchange executions, but that does **not** mean the public per-security metric table exposes off-exchange/dark-pool volume.

Therefore:
- Do not call `HiddenVol` dark-pool volume.
- Do not interpret it as signed buying/selling, institutional accumulation, or participant identity.
- If constructing a hidden-execution share, use the SEC-defined eligible denominator (`HiddenVol / TradeVolForHidden`) only after confirming units, missingness, and exchange coverage from the ZIP README and data sample.
- Preserve the raw fields and denominator; never silently substitute `TradeVol`.

Sources:
- [SEC Market Activity Report Methodology](https://www.sec.gov/featured-topics/market-structure-analytics/market-activity-report-methodology)
- [SEC MIDAS Feedback / FAQ](https://www.sec.gov/securities-topics/market-structure-analytics/midas-feedback)
- [SEC Hidden Volume Ratios data highlight](https://www.sec.gov/about/hidden-volume-ratios)
- [SEC About MIDAS](https://www.sec.gov/securities-topics/market-structure-analytics/midas-market-information-data-analytics-system)

## 3. Structural breaks and comparability gates

At least three explicit regime boundaries must be preserved:

1. **January 2014:** the first full month in which odd-lot trades were reported to the SIP, allowing a fuller reconciliation of direct-feed and SIP trades. The SEC methodology describes use of SIP trades not present on the NYSE/Amex direct level-book feed to identify executions against undisplayed orders. Do not assume pre-2014 hidden/odd-lot measurements are comparable to later periods.
2. **May 1, 2017:** MIDAS changed from the NYSE Ultra feed to the NYSE Integrated Feed. The SEC says this feed supplies an indicator for trades involving resting undisplayed orders. The methodology also says NYSE/Amex contributions to Cancel-to-Trade, Odd-Lot Rate and Odd-Lot Volume were excluded from quarterly user files before this change and included after the NIF change. Treat these fields as regime-dependent.
3. **November 3, 2025:** the SEC's new round-lot definition introduced four price-based round-lot tiers, updated semiannually. Odd-lot counts and volume before and after this date are not a single homogeneous series without a documented adjustment.

Additional interpretation constraint: SEC explains that Cancel-to-Trade is a count ratio and does not provide an exact numerical representation of what happens to orders; partial executions and partial cancellations differ. Do not describe it as a direct cancellation probability or spoofing measure.

These boundaries must be represented as explicit feature metadata and separate validation strata. No full-history z-score or normalization may bridge them without a tested regime treatment.

## 4. Point-in-time availability

The files contain daily observations but are released as quarterly ZIPs. A row's `Date` is the market observation date, **not** the date a researcher could first have downloaded the quarter's file.

The current SEC landing page provides the archive list and a page-level “Last Reviewed or Updated” date. It does not provide a per-quarter first-publication timestamp for each ZIP. The linked RSS feed is a possible route to recover release notices, but historical item timestamps and archive snapshots have not yet been reconciled in this phase.

Consequences:
- Historical daily rows are not automatically daily PIT data.
- Do not assign quarter-end, file date, crawl date, or the current page's last-reviewed date as a historical availability timestamp.
- A historical event study or backtest is blocked until per-quarter release dates are recovered from reliable SEC RSS/archive evidence or a conservative availability rule is independently justified.
- Prospective capture can store the SEC RSS item, page snapshot, archive URL, response receipt interval, file hash and quarter coverage when each new release appears. The receipt is an upper bound, not exact first public availability.

## 5. Universe and identity coverage

The SEC methodology says the included stock/ETP list is sourced from CRSP daily data (SHRCD 10/11 for stocks; 73 for ETPs) and updated monthly with a 3–4 week lag from the final trading day of the prior month.

The public column list contains ticker and security name, but no CUSIP, issuer CIK or permanent security identifier. The source's >4,800-security headline does not establish:
- overlap with the historical 335-name F80 universe;
- coverage of delisted securities and historical ticker changes;
- share-class uniqueness;
- absence of survivorship or CRSP-universe selection effects.

A ticker-only join is not acceptable. Require an effective-dated security master and a coverage report by quarter, including unmatched, ambiguous, delisted and share-class cases. The CRSP universe refresh lag must be represented in the availability/coverage audit.

## 6. Hypotheses retained for a later, properly timed test

These are market-microstructure hypotheses, not claims about “smart money”:

- **H1 — hidden-liquidity / risk state:** abnormal `HiddenVol / TradeVolForHidden` may help forecast subsequent realized volatility, spread/liquidity deterioration or downside tail risk. It has no direction by itself.
- **H2 — order interaction / liquidity state:** changes in `TradeVol / OrderVol` and carefully defined cancel/trade metrics may add information about subsequent liquidity or price impact. The cancel/trade ratio must not be interpreted as spoofing or exact cancellation probability.
- **H3 — odd-lot composition:** odd-lot share/volume measures may describe changes in market microstructure or volatility regimes. This hypothesis must be split around January 2014 and November 3, 2025 and must not be relabeled as “retail flow” without independent participant evidence.

Primary role should initially be **risk/liquidity context**, not directional stock ranking. Test incremental information versus frozen LTM/F80 with identical universe, exposure and costs only after all PIT and identity gates pass. Use chronological splits, bootstrap/LOO and untouched OOS; do not select thresholds on the holdout.

## 7. Next feasibility gate

Before any forward-return test:

1. Retrieve a stratified sample of 2012 Q1, 2014 Q2, 2017 Q2, 2025 Q4 and 2026 Q3 ZIPs through an authorized SEC download client.
2. Preserve URL, retrieval time, HTTP headers, byte count and SHA-256; inspect the ZIP README and exact CSV schema/units.
3. Verify date ranges, duplicate keys, missingness, field units, security counts, and whether quarterly ZIPs overlap or revise prior observations.
4. Recover first-publication dates for all historical quarters from SEC RSS/archive evidence; if not recoverable, keep the historical PIT gate closed.
5. Reconcile ticker/security names to the effective-dated historical F80 universe and report coverage by quarter.
6. Only then construct candidate features and test H1–H3 against frozen LTM/F80.

## 8. Phase disposition and controls

- SEC MIDAS: **conditional public market-microstructure / risk-feature source**.
- Direct smart-money or off-exchange signal: **not supported by this dataset**.
- Historical daily PIT: **not verified**.
- F80-335 historical identity/coverage: **not verified**.
- ZIP sample parsed in this phase: **0** (the external download attempt was unsuccessful; no sample was inferred).
- Forward-return/event study/backtest/OOS/bootstrap/LOO: **not run**.
- New signals admitted: **0**.
- `F80_TOP20_PARTIAL50_BASELINE_C20`: unchanged and frozen.
- No universe, parameters, exposure, costs, capital, holdout or production changes.
- No raw MIDAS data or vendor data committed.

## GitHub / Actions preflight

At the 2026-11-20 20:26 UTC snapshot:
- Main HEAD was `8c1eb319efd31f355f8a07738410f0dbd0e67983`.
- Latest Actions API page contained 7,984 runs; no queued or in-progress runs were returned.
- The latest natural Form 4 run was [44794670480](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44794670480), completed successfully and created `reporting_owners.csv`.
- The latest natural Form 144 run was [44796839433](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44796839433), completed successfully.
- The next Form 4 cron slot (20:17 UTC) was not yet visible in the Actions run list at this snapshot. No manual dispatch or rerun was made; allow GitHub's existing schedule to arrive naturally.
- The bounded owner-enrichment queue still places Atea Form 4 accessions `0001193125-26-469038` and `0001193125-26-469037` at positions 2 and 3 in the next ten-accession batch. The previous zero-row crosswalk is therefore not a failed match test.
- Latest FINRA Reg SHO live run [44669121290](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44669121290) predates the Phase 515 parser repair: 8 HTTP-200 responses, 8 invalid files, 0 valid files. It is not post-fix validation.
- Open options feasibility drafts #186 (ThetaData), #188 (Massive), and #171 (OCC) remain separate; no purchase or vendor sample was made.

No workflow was dispatched, duplicated or cancelled.
