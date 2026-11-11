# Phase 286 — Nasdaq Options Trade Outline (NOTO) and Options Pulse feasibility audit

**Audit date:** 2026-11-11 UTC  
**Branch:** phase286-nasdaq-options-trade-outline-feasibility  
**Status:** METADATA_FEASIBILITY_ONLY — NOTO is a high-priority conditional venue-level options-flow candidate; NOP is a derived secondary comparator. No raw-data admission, PIT admission or alpha test.  
**Control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Executive decision

**Nasdaq Options Trade Outline (NOTO) is a materially stronger options-flow candidate than a generic sentiment score.** It provides per-option-series aggregate trade quantity and volume by exchange origin category and position-opening/closing type, with history advertised from November 2011. The End-of-Day (EOD) report includes total industry volume and open interest, and is described as available the next business day at approximately 7:00 a.m. ET. The intraday product updates every ten minutes and, according to the SEC-filed product description, is available within two minutes after each ten-minute interval. The intraday snapshots are cumulative, not independent interval increments.

The initial product audited here is **NOM-only**. The SEC filing reported NOM options market share of approximately 5–6% in Q2 2024. This is not full OPRA coverage and the 2024 market-share figure must not be assumed to be current. Nasdaq markets a broader six-exchange Trade Outline family (NOM, PHLX, ISE, GEMX, MRX and NTX), but each venue has its own product, schema/history and fee schedule. Do not assume that the six feeds form a ready-made, gap-free panel.

**Nasdaq Options Pulse (NOP/NOSI)** is a secondary derived-sentiment candidate. Its symbol, sector/industry and market scores update every ten minutes and history is advertised from January 2019. Nasdaq describes it as using customer and professional-customer opening-buy transactions across Nasdaq options exchanges. Its score methodology is less transparent than NOTO's underlying origin/open-close aggregates, and it is not independent confirmation of NOTO.

This source merits a future sample gate, but **no purchase, trial, vendor contact, API call, license acceptance or data download is authorized or was initiated**. Data rights are restrictive and published historical-fee information is inconsistent across official Nasdaq documents; no budget commitment is recommended without resolving the full license and price.

## 1. NOTO measurement semantics

Official sources:
- Nasdaq Data Link NOTO: https://data.nasdaq.com/databases/NOTOI
- SEC-filed NOTO product definition (Release 34-101098, 2024-09-19): https://www.sec.gov/files/rules/sro/nasdaq/2024/34-101098.pdf
- Current Nasdaq Options 7 rulebook and fee schedule: https://listingcenter.nasdaq.com/rulebook/nasdaq/rules/Nasdaq%20Options%207

NOTO provides aggregate quantity and volume for option series traded on NOM, classified by origin type:
- Customer;
- Broker-Dealer;
- Market Maker;
- Firm; and
- Professional.

For customers and professionals, the product further subdivides activity into trade-size buckets. It distinguishes position-opening from position-closing activity. EOD reports also provide total exchange volume, total industry volume and open interest by series; EOD opening-buy, closing-buy, opening-sell and closing-sell fields include first, high, low and last trade prices.

### Origin labels are not beneficial-owner identities

- **Customer** means an OCC Customer-range transaction that is not for a broker/dealer account and is not for a Professional.
- **Professional** means a person or entity that is not a broker/dealer and averages more than 390 listed-options orders per day during a calendar month for its own beneficial account(s). This is an activity threshold, not an institutional/fund classification.
- **Firm** is an OCC Firm-range clearing designation. It is not a named proprietary-trading firm.
- **Market Maker** is a registered NOM market maker.
- **Broker-Dealer** is a separate origin category.

No category identifies a named hedge fund, beneficial owner, asset manager or account. Do not call Professional “institutional money,” and do not assume Firm or Market Maker trades are directional informed bets.

### Opening/closing is not aggressor direction

The SEC-filed definition says:
- an opening purchase creates or increases a long position in the option series;
- an opening write creates or increases a short position in the option series;
- a closing purchase reduces or eliminates a short option position; and
- a closing sale reduces or eliminates a long option position.

These are position/open-close classifications, not a signed NBBO aggressor flag. “Opening buy” is not by itself bullish for the underlying: the series may be a put or call, and a buyer's option delta can have either sign. Opening writes, closing buys and closing sales must remain separate. Multi-leg strategies, hedges and market-making inventory can still make the net underlying interpretation ambiguous.

## 2. History, delivery and point-in-time limitations

| Item | Published specification | Research implication |
|---|---|---|
| Historical start | November 2011 | Long history is attractive, subject to actual archive continuity |
| EOD timing | Next business day; SEC filing says approximately 7:00 a.m. ET | Potentially usable before the next regular session only after actual first receipt is captured |
| Intraday timing | Ten-minute snapshots; available within two minutes after interval end | Potentially timely, but not a real-time feed |
| Intraday snapshot semantics | Each snapshot is cumulative for current and previous snapshots | Difference consecutive snapshots; never sum cumulative snapshots |
| Intraday current table | Current trade date; resets at 01:40 UTC | Reset and trading-date boundaries must be verified |
| Intraday history table | Historical monthly files; Nasdaq Data Link page says updated at 21:00 UTC with current trade date | Historical file update is not historical first-receipt evidence |
| Venue scope | NOM proprietary exchange data only | Not OPRA-wide; no other-exchange intraday trades included |
| EOD denominator | Total industry volume by option series | Can measure NOM's share of industry volume at EOD; do not assume an intraday denominator |
| Revisions | No immutable as-published snapshot/revision policy established in this audit | Preserve actual received bytes and every revision; PIT not admitted |

The published EOD schedule is a useful availability hypothesis, not a historical receipt ledger. The intraday cumulative snapshots require actual receipt timestamps and version capture; a later corrected cumulative snapshot can otherwise contaminate a backtest. Historical monthly files are not proof that the originally disseminated snapshot can be reconstructed.

### Contract identity and universe coverage

The documented series fields include underlying symbol, option symbol, expiration, strike, put/call, days to expiration and standard/non-standard series type. Before use, require an effective-dated option master that handles adjusted/non-standard contracts, corporate actions, symbol changes, expiration conventions and delisted underlyings. Measure overlap against the exact frozen F80 universe and historical optionable universe. Do not join by underlying ticker alone.

The EOD total-industry-volume field is valuable: it allows a per-series NOM/industry activity ratio, subject to identical series identity and report vintage. The 5–6% NOM market-share figure cited for Q2 2024 is a venue-wide historical context only, not a substitute for per-series coverage or a current market-share estimate.

## 3. Pricing and license gate

The current Nasdaq Options 7 rulebook lists:
- EOD NOTO: **USD 575/month**;
- intraday NOTO: **USD 2,000/month**;
- most recent 36 months of history for current distributors: **USD 3,000 EOD** or **USD 6,000 intraday**;
- external distribution of derived NOTO data: **USD 4,000/month**, in addition to the data subscription.

The same current rulebook lists ad-hoc historical requests at USD 575 per EOD month and USD 2,000 per intraday month. However, Nasdaq's official 2025–2027 price-list PDF lists historical data at USD 250 per requested EOD month and USD 500 per requested intraday month. **This is an unresolved official-document price discrepancy.** Do not estimate or approve a full-history purchase from either number; obtain a current written quote only if explicitly authorized.

Nasdaq Data Link describes NOTO as Premium and internal-use-only. The rulebook provides a separate fee for external distribution of derived data; this does not imply that raw exchange data may be redistributed. Intended internal research, storage, derivative-feature, backtest and any later distribution rights must be confirmed before acquisition.

## 4. Nasdaq Options Pulse (NOP/NOSI) — secondary candidate

Official pages:
- Nasdaq Options Pulse: https://www.nasdaq.com/products/data/options-pulse
- Nasdaq Data Link combined Investor Activity Intelligence: https://data.nasdaq.com/databases/NIFI

Nasdaq advertises:
- symbol-level, sector/industry and market-level sentiment;
- ten-minute sentiment-score and interval-score updates;
- history from January 2019; and
- a methodology based on customer and professional-customer opening-buy transactions across Nasdaq options exchanges.

The published table schema exposes scores, not the full origin/open-close quantities. This is a derived signal with less transparent construction than NOTO. It may be useful as a vendor benchmark or lower-friction comparator, but it is **not independent confirmation** if it is built from overlapping Nasdaq options activity. Require formula/version history, revisions, coverage and first-receipt evidence before considering a test.

## 5. Research hypotheses — preregister before returns

1. **New option-position formation by origin:** test opening-buy and opening-write activity separately for Customer, Professional, Firm, Broker-Dealer and Market Maker categories, split by call/put, expiry and moneyness. Convert to delta-adjusted exposure only with point-in-time option Greeks and contract identity. Do not assume a directional sign.
2. **Opening versus closing:** test whether fresh position formation adds information beyond closing/covering activity and ordinary option volume. Do not interpret a rise in OI as a directional buyer signal; OI is bilateral.
3. **Venue concentration:** use EOD NOM volume divided by total industry volume for the same series to test whether a venue-specific flow signal is stable or only reflects changing NOM market share. Treat the denominator as EOD-only unless the source documents otherwise.
4. **Origin/size interaction:** test Professional and Customer trade-size buckets separately. Professional is an order-frequency class, not an institution; do not label it hedge-fund flow.
5. **NOP comparison:** compare the derived sentiment score against NOTO only as a related-source benchmark. Do not call agreement between them independent validation.
6. **Underlying versus option outcomes:** evaluate underlying-stock returns separately from option-contract returns. Option P&L requires executable bid/ask, spread, IV, delta/gamma, theta, expiry and realistic transaction costs.

Falsify any feature that is only a proxy for past returns, loses its effect after venue-share normalization, is concentrated in a few symbols/expiries, fails after costs, or does not survive chronological OOS, date/issuer clustering, leave-one-out and multiplicity controls.

## 6. Admission plan

1. Obtain explicit authorization before any trial, purchase, vendor contact or terms acceptance.
2. Request a small stratified EOD sample across early, middle and recent years, with raw original files, metadata, corrections/bust policy, historical delivery versions and exact option-series reference data.
3. Prefer EOD first: the next-business-day morning release is easier to timestamp and potentially sufficient for the user's daily/close-oriented strategy. Preserve actual receipt time, response metadata, raw bytes and SHA-256; never backdate from the nominal 7 a.m. schedule.
4. Measure per-series and per-underlying coverage, NOM/industry volume ratio, active/inactive contract continuity, missing days, non-standard contract share, origin-category sparsity and revisions.
5. If intraday is later considered, capture live ten-minute snapshots prospectively, preserve receipt timestamps, difference cumulative snapshots, reconcile reset boundaries, and audit bust/correction handling.
6. Evaluate the other five Nasdaq options venues separately before any combined feed. Normalize venue-specific origin categories, definitions, calendars, schemas, histories and fees; never assume identical categories or complete coverage.
7. Only after admission, preregister a new chronological test against frozen LTM/F80, identical exposure/costs, date/issuer/contract-clustered bootstrap, leave-one-out, multiple-testing control and a fresh prospective holdout.

## 7. Decision

| Source | Role | Priority | Admission |
|---|---|---:|---|
| NOTO EOD | Per-series position formation by origin and open/close | 1, conditional | Metadata only; no raw sample/PIT/alpha |
| NOTO intraday | Ten-minute cumulative position-flow snapshots | 2, conditional | More difficult receipt/vintage contract; no PIT |
| Other Nasdaq Trade Outline venues | Potential cross-venue origin/open-close panel | 3, conditional | Separate venue audits required |
| Nasdaq Options Pulse (NOP/NOSI) | Derived ten-minute sentiment comparator | 4, conditional | Formula/version and overlap unresolved |

**No raw data were downloaded. No API key was used. No vendor was contacted. No trial, purchase or license was accepted. No backtest, return test, bootstrap, LOO, holdout or alpha test was run.** F80, production, universe, capital and parameters are unchanged.

## 8. Official sources

1. Nasdaq Data Link NOTO product documentation: https://data.nasdaq.com/databases/NOTOI
2. SEC Release 34-101098, *Codify the Definition of Nasdaq Options Trade Outline* (2024-09-19): https://www.sec.gov/files/rules/sro/nasdaq/2024/34-101098.pdf
3. Current Nasdaq Options 7 rulebook: https://listingcenter.nasdaq.com/rulebook/nasdaq/rules/Nasdaq%20Options%207
4. Nasdaq US Options Price List 2025–2027: https://www.nasdaqtrader.com/content/ProductsServices/PriceList/Nasdaq_US_Options_Price_List_2025_2026_2027.pdf
5. Nasdaq Options Trade Outline suite: https://www.nasdaq.com/products/data/options/trade-outline
6. Nasdaq Options Pulse: https://www.nasdaq.com/products/data/options-pulse

This phase is a public-specification and licensing feasibility audit only. It does not admit NOTO or NOP into the research dataset.
