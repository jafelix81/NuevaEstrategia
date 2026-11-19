# Phase 501 — Cboe OPRA Option Trades + Option Quotes source/PIT feasibility audit

**Date:** 2026-11-19 UTC  
**Branch:** `phase501-cboe-opra-trades-quotes-pit-feasibility`  
**Baseline main:** `408a8fdfaeac81408760b90b2c0ecff2c34ae7b2`  
**Disposition:** strongest conditional independent options-flow candidate identified; **not admitted** for historical alpha or production.

## 1. Repository and Actions preflight

Reviewed the latest 20 main commits, open PR search results, the first 100 phase branches (pagination indicates additional branches), the Phase 500 report/state, Phase 500 PR #156, and run-specific jobs, logs and artifacts before starting this phase.

- Main latest commit at preflight: `408a8fdfaeac81408760b90b2c0ecff2c34ae7b2` (Phase 500).
- Phase 500 PR #156 is closed/merged. Its PR validation run [44534689780](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44534689780) passed **46/46** offline tests; `live-capture` was correctly skipped and the run produced no artifact.
- Phase 500's last repository-wide Actions census reported 7,892 runs and no active/queued runs in the latest 100 at that review. The connected GitHub operations expose run-specific jobs/logs/artifacts and commit-associated PR runs, but not a repository-wide scheduled-run listing; no stronger current census is claimed here.
- The latest inspected live SEC Form 144 poll remains [44521745535](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44521745535): partial. Its live job log confirms 3,292 bytes on Form 144 with an XML ParseError and 29 bytes/zero entries on 144/A, with a possible feed-window gap. The response bodies were not retained.
- The latest inspected FINRA live poll [44453548570](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44453548570) predates Phase 495. Its log confirms 8 HTTP 200 responses, 8 invalid files, zero valid files and zero eligible observations. The Phase 495 parser has only had offline validation in the inspected evidence; a post-fix live capture is still required.
- The latest inspected CFTC capture [44453066854](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44453066854) passed its 17 tests and made no persistent capture changes; no new report was admitted.
- Open source-gate items remain: Cboe Phase 357 PR #44 (PIT/product metadata), Issue #132 (sample redistribution rights for the separate Open-Close sample), and SEC 13D/G PR #37 (requires the repository's SEC contact User-Agent secret).

No existing workflow was started or duplicated. This phase is documentation-only.

## 2. Why this candidate is different

The Cboe **Option Trades** product is documented as a trade-by-trade file for every options print across the OPRA universe, with trade price/size, executing exchange and prevailing NBBO at the trade. Optional Calcs add point-in-time IV and Greeks. It covers U.S.-listed stock, ETF and index options, including GTH and RTH, but not futures options or non-U.S. markets.

The companion **Option Quotes** product provides 1-minute or custom interval option snapshots with NBBO, interval OHLC/volume, optional IV/Greeks and optional open interest. This makes the pair a plausible independent reconstruction source for:
- aggressor-side option flow from prints relative to contemporaneous NBBO;
- delta-/vega-weighted signed notional;
- call/put and tenor-specific flow;
- IV skew and term structure;
- volume/open-interest and subsequent open-interest-change context.

Unlike Cboe Open-Close, Option Trades spans OPRA rather than only Cboe exchanges. Unlike a proprietary participant-bucket feed, it permits independent trade-level reconstruction from prints and NBBO. It does **not** identify beneficial owners or prove institutional activity. Any signed-flow measure is an execution-aggressor proxy, not “smart money” by definition.

## 3. Official specification findings

### Option Trades

The current product page and v1.3 file specification describe:
- `underlying_symbol`, `market_date`, millisecond Eastern `quote_datetime`, OPRA `sequence_number`, option root, expiration, strike and call/put;
- exchange ID, trade size, trade price and trade-condition ID;
- contemporaneous NBBO bid/ask and sizes;
- optional trade IV and Greeks;
- underlying bid/ask, which default to zero when unavailable;
- GTH trades as well as RTH.

The file specification says `canceled_trade_condition_id` is legacy and always zero. It is not a usable cancellation ledger. Trade-condition and exchange-ID mapping files are required before filtering or signing prints.

### Option Quotes

The v1.1 specification describes end-of-interval Eastern timestamps, NBBO snapshots, interval OHLC/volume, optional IV/Greeks and optional OCC open interest.

The OCC OI field is **start-of-day OI**: the FAQ says DataShop uses the prior night's OCC end-of-day open interest at the start of the trading day and holds it static throughout that day until the next morning. It must not be relabeled as end-of-day OI or as an intraday changing position count.

A material microstructure regime break applies to quote sizes: effective 2026-06-22, bid/ask sizes are captured at the time of the most recent price change within the interval. Before that date, sizes reflected the latest price and size within the interval even if the price had not changed. Size-based features must be segmented or normalized for this break.

## 4. Historical coverage: conservative treatment

There is an official-document conflict:
- The current Option Trades product page says history begins **January 2012**.
- The current Option Quotes product page says history begins **January 2012**.
- The general DataShop FAQ table says Option Trades and Option Quotes begin **January 2010**.

Use **January 2012** as the conservative common start until Cboe confirms the discrepancy and per-symbol availability. Do not backfill 2010–2011 based only on the FAQ table.

“All OPRA universe” describes product scope, not a guarantee that every underlying/date is available. The purchase interface itself warns that specific symbols or dates may be unavailable. No 335-name frozen-universe coverage census, delisted-underlying coverage audit, or per-date gap map has been run.

### Identity and contract continuity

Underlying symbols and option roots are not a permanent security master. The file specification notes share-class formatting and non-standard option roots (including numeric suffixes). Corporate actions can change deliverables and contract multipliers.

Before joining options to F80 returns:
- use an effective-dated equity security master and historical ticker/class mapping;
- preserve option root/OSI and adjusted-contract status;
- quarantine adjusted/non-standard contracts until deliverables and multipliers are verified;
- exclude or separately classify indices, ETFs and non-equity underlyings;
- retain delisted and acquired underlyings rather than survivorship-filtering them.

No such join is certified by this phase.

## 5. PIT clock and correction policy

Cboe's FAQ states that daily files for trade date T are supplied the following day via SFTP, typically between 00:05 and 03:00 U.S. Eastern, but delays can cause the prior day's file to arrive during the following day after the market opens.

Consequences:
- Trade timestamps are event times, **not** vendor-availability timestamps.
- Historical archive coverage is not proof of historical first delivery.
- No historical per-file SFTP receipt log, vintage history, correction ledger or maximum delivery-delay guarantee was available in the reviewed public documentation.
- A provisional conservative historical convention would not use T data before the first regular session after the following delivery day (nominally T+2 open); however, absent a hard delivery bound and archived vintages, this is a research proxy, **not certified strict PIT**.
- Any prospective subscription must append first-seen SFTP receipt time, remote filename/size/mtime where exposed, local SHA-256, vendor revision/replacement status and retrieval outcome. Revisions must be append-only and never backdated.

Cboe's public documents do not resolve how Option Trades daily files represent late reports, cancels, busts, corrections or replacements. The legacy zero cancellation field makes this a mandatory vendor question. Do not assume a trade print is final or count every condition as an ordinary directional execution.

For a prospective test, use actual receipt timestamps and the first regular equity session strictly after receipt. For historical research, do not claim exact PIT until delivery/vintage and correction semantics are independently established.

## 6. Data-quality and feature-construction controls

1. Parse the official trade-condition and exchange-ID mappings; preserve the original condition and venue.
2. Separate RTH and GTH; start with RTH-only features and test GTH separately.
3. Classify buyer-/seller-initiated trades only when the trade can be reliably located relative to contemporaneous NBBO. Midpoint, locked/crossed, complex, auction, late, out-of-sequence and otherwise ambiguous conditions remain separate or excluded according to the official mapping.
4. Do not use `canceled_trade_condition_id` as a cancellation signal; it is documented as always zero.
5. Treat zero IV/Greeks as unavailable/model-failure cases, not true zero volatility/Greeks. Treat zero underlying bid/ask as missing.
6. Normalize for contract multiplier/deliverable, moneyness, delta, tenor, underlying ADV/market cap and option liquidity.
7. Use SOD OI only as SOD OI. OI changes are observed from subsequent daily SOD snapshots and cannot be attributed to the same day's opening/closing trades without a valid timing model.
8. Quote-size features must account for the 2026-06-22 methodology change.
9. Preserve missingness and coverage denominators; never turn missing series into zero flow.

Candidate features, if all gates pass:
- signed premium / gross premium and signed contract volume by underlying, call/put, delta bucket and tenor;
- delta- and vega-weighted net flow, normalized by underlying liquidity and option OI;
- buyer/seller aggressor imbalance, with midpoint/ambiguous share as a separate quality feature;
- volume-to-SOD-OI and next-SOD OI change, without calling either an opening/closing position identifier;
- standardized 25-delta put-call skew, 10/25-delta wings and term-structure slopes using liquid, valid quotes;
- rolling flow shocks and persistence, strictly using data received before the decision cutoff.

## 7. Independent validation design

If the source is lawfully acquired and passes coverage/PIT:
- compare reconstructed signed flow with OptionMetrics TradeFlow on overlapping contracts/dates, without assuming either classifier is ground truth;
- use Cboe Open-Close only as a venue-limited complementary check, respecting its exchange scope and historical convention breaks;
- pre-register feature definitions, quote/trade-condition filters, minimum liquidity and missingness thresholds before looking at returns;
- test whether options features add information beyond frozen LTM/F80 after controlling for momentum, realized volatility, liquidity, earnings/event windows, market/sector moves and price/size effects;
- distinguish contemporaneous return-chasing from genuinely forward predictive information;
- use identical universe, entry/exit timing, gross exposure, turnover constraints and costs for baseline and candidate;
- use chronological discovery/validation/OOS, block bootstrap, leave-one-out and multiple-testing control; keep the existing holdout untouched.

No event study, return test, alpha test, OOS, bootstrap or LOO was run in Phase 501.

## 8. Cost, licensing and sample status

The public product pages expose historical and subscription purchase workflows but do not provide a quote for the required all-symbol/history configuration. Business-use, redistribution, derived-data retention and external research rights were not established. No vendor contact, trial, order or purchase was made.

The product page exposes a public sample link, but no sample bytes were successfully acquired in this audit. No sample or raw/derived market rows were committed to GitHub or an Actions artifact. The separate Issue #132 concerns the Open-Close sample and remains unresolved; this phase does not claim that issue applies to Option Trades or resolves its rights.

## 9. Source decision

**CONDITIONAL CANDIDATE — highest-priority independent options tape/quote path for further feasibility work.**

Why it outranks a standalone Open-Close signal:
- OPRA-wide trade prints rather than only Cboe-exchange trades;
- contemporaneous NBBO and millisecond event timestamps;
- optional trade IV/Greeks and companion quote snapshots with OCC SOD OI;
- enough advertised history to overlap the modern F80 period and extend before TradeFlow's advertised January 2016 history.

Why it is not admitted:
- official start-date conflict (2010 vs 2012);
- no 335-name/delisted-symbol coverage census;
- no certified historical vendor first-delivery/vintage clock;
- unresolved cancel/bust/correction and daily-file replacement semantics;
- no effective-dated equity/option security-master bridge;
- unknown price and business-use licensing;
- no sample/schema execution test.

Next gate is a vendor-neutral schema/coverage checklist and, only after business-use terms and cost are approved, a small lawful sample covering old/new dates, liquid/illiquid underlyings, adjusted roots, RTH/GTH and correction conditions. No broad historical purchase should precede that gate.

## 10. Frozen controls

- `F80_TOP20_PARTIAL50_BASELINE_C20`: unchanged and frozen.
- Universe, parameters, capital, exposure, costs, holdout and production: unchanged.
- New signals admitted: 0.
- No vendor purchase, external contact or data redistribution.
