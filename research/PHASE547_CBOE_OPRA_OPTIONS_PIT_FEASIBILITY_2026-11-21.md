# Phase 547 — Cboe OPRA options data and Open-Close historical PIT feasibility

**Audit cutoff:** 2026-11-21 13:37 UTC  
**Base main:** `cb9aab722f905e2df54e349091e42ae7d9bf243a`  
**Disposition:** Cboe's public product specifications establish a strong conditional data candidate: OPRA-wide Option Trades plus Option Quotes for market-wide trade/NBBO/IV/OI features, with Cboe Open-Close EOD as a participant-capacity/open-close complement. This is a data-feasibility result only. Exact 335-name coverage, historical first-receipt/correction vintages, data pricing and permitted use remain unverified. No purchase, sample download, signal or return test.

## 1. Actions and repository preflight

- Latest 100 Actions runs: **87 success, 12 failure, 1 cancelled**; zero in-progress, queued, waiting, requested or pending.
- Latest overall runs are the Phase 546 PR checks:
  - [44904626254](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44904626254): Phase 460 Form 4 gates, 16/16 tests.
  - [44904626250](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44904626250): Phase 461 Form 4 schema/owner-link gates, 21/21 tests.
- PR [#199](https://github.com/jafelix81/NuevaEstrategia/pull/199) remains Draft, mergeable, five commits ahead and zero behind at this cutoff. It records Phase 546's single SE overlap / Rule 10b5-1 negative control. These CI checks exercise existing Form 4 gates; they are not an options-data test.
- PR [#198](https://github.com/jafelix81/NuevaEstrategia/pull/198) remains Draft; SEC FTD sample access still depends on the repository Actions secret `SEC_USER_AGENT`.
- Latest natural Form 144 run remains [44886726541](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44886726541), created 08:50:10 UTC. At 13:37 UTC the 09:47, 10:47, 11:47 and 12:47 schedule slots were absent; 13:47 had not yet become due. The successful 08:50 poll found its prior accession watermark and reported no feed-window gap, which does not establish scheduler continuity. Issue [#194](https://github.com/jafelix81/NuevaEstrategia/issues/194) remains open.
- Form 4's latest scheduled run remains [44846461134](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134); its workflow is weekday-only, so Saturday absence is not counted as a missed slot.
- FINRA [44860690600](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600) predates the Phase 539 merge and cannot validate the new duplicate diagnostics. CFTC [44860341977](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977) remains the latest prospective TFF capture.
- No workflow was dispatched, rerun, cancelled or duplicated.

## 2. Phase 546 Form 4 negative control — official interpretation

The Phase 546 branch found one exact symbol overlap between the current Form 4 structured ledger and the static 335-symbol snapshot: SE / Sea Ltd. It is one accession with seven sale lines, 1,600 shares in aggregate, approximately USD 109,300.43 gross, and an affirmative `AFF10B5ONE=yes` flag. The owner sidecar is pending; the seven rows are not seven independent events and all transaction rows remain ineligible.

The SEC's current Section 16 interpretations explain that the Form 4 checkbox applies to transactions made pursuant to a contract, instruction or written plan intended to satisfy the affirmative-defense conditions of amended Rule 10b5-1(c). The checkbox therefore supports treating this filing as a **planned-trading negative control**, not discretionary insider flow. It does not establish the owner's identity, role, plan adoption date or economic motive. Keep the conservative first-seen receipt upper bound and next-full-session rule; do not backdate to transaction dates or treat EDGAR acceptance as exact public availability.

Official source: https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/exchange-act-section-16-related-rules-forms (Question 135.04; page last updated October 15, 2026).

## 3. Cboe Option Trades — strongest broad-market transaction candidate

The current Cboe DataShop product page and v1.3 file specification state:

- Historical coverage: January 2012 to present.
- Coverage: listed U.S. stock, ETF and index options disseminated over OPRA, i.e. trade prints across U.S. options exchanges.
- One daily file per date (or monthly/year grouping where available).
- Trade-level fields include underlying symbol, market date, Eastern quote/trade datetime to milliseconds, OPRA sequence number, option root, expiry, strike, call/put, executing exchange, size, price, trade-condition ID, and prevailing NBBO bid/ask prices and sizes.
- Optional Calcs add trade-time implied volatility and Greeks (delta, gamma, vega, theta, rho).

This is a materially better market-wide tape candidate than a single-exchange flow feed. It permits a reproducible quote-relative aggressor hypothesis (trade at/near ask versus bid), but it **does not identify customer/pro-customer/firm/market-maker capacity and does not label opening versus closing**. Trade-condition mapping, complex/multi-leg prints, late/corrected trades, locked/crossed/stale NBBO and midpoint ambiguity must be handled before any signed-flow feature is admitted. A large call print is not evidence of informed buying.

Sources:
- https://datashop.cboe.com/option-trades
- https://datashop.cboe.com/documents/Option_Trades_File_Specification.pdf

## 4. Cboe Option Quotes — IV, Greeks, NBBO and OI companion

The current product page and v1.1 file specification state:

- Historical coverage: January 2012 to present; OPRA-listed U.S. stock, ETF and index options.
- One-minute or custom N-minute interval summaries; a 390-minute interval can target the regular-session close.
- Each interval carries quote-time NBBO and sizes, option OHLC, trade volume, underlying bid/ask where disseminated, and quote datetime at the interval end in U.S. Eastern time.
- Optional Calcs provide IV and Greeks; optional open interest is the **start-of-day (SOD) OI from OCC**.
- Intraday snapshots are delayed 15 minutes after the interval; daily files are delivered overnight or early morning the following day.

Important PIT distinction: SOD OI is not same-day closing OI and does not reveal the direction of positions opened or closed. A candidate net OI change for session t would compare SOD OI on t+1 with SOD OI on t, but it is eligible only after the t+1 file is actually received and its OCC as-of convention is verified. Historical archive rows do not establish historical first-receipt time. The 2026-06-22 change to quote-size capture convention also means historical size fields have a known methodology break that must be versioned.

For a swing-horizon pilot, 60-minute or 390-minute snapshots are preferable to a full 1-minute all-market panel until file sizes and exact 335-name coverage are measured. Cboe's published all-symbol estimates are approximately 2.3 TB compressed/year at 1-minute, 155 GB at 15-minute and 40 GB at 60-minute (with Calcs); targeted 335-name sizes are not published.

Sources:
- https://datashop.cboe.com/option-quote-intervals
- https://datashop.cboe.com/documents/Option_Quotes_Layout.pdf

## 5. Cboe Open-Close EOD — participant-capacity complement, not a market-wide proxy

The current product page and EOD v1.3 specification provide unusually useful fields:

- Participant/origin buckets: Customer, Professional Customer, Broker/Dealer, Firm and Market Maker.
- Buy/sell and open/close position side; customer and professional-customer activity is split into <100, 100–199 and >=200 contract trade-size buckets.
- One final EOD file per exchange per trade date; subscriptions typically deliver preliminary and final files between 00:30 and 01:00 U.S. Eastern the following morning. The final file sources total-industry-volume and OI values from OCC; preliminary values can differ.
- Coverage is only Cboe exchanges (C1, BZX, C2, EDGX), not the full OPRA universe. C1 EOD starts 2005-01-03; BZX/C2/EDGX EOD starts 2018-01-02. A paired four-venue panel therefore cannot start before 2018-01-02 and still requires exact symbol/date coverage.
- The product page states raw data are licensed for internal use only and may not be externally redistributed; derived-data external distribution requires additional licensing fees and approval. Do not put licensed raw or derived observations in this public repository.

**Newly identified historical convention breaks:**
- Open Interest / Previous Open Interest is reported as shifted one day ahead for C1 through 2019-10-04 and C2 through 2018-05-11; BZX and EDGX use a consistent SOD convention.
- C2 Total Industry Volume was doubled through 2018-05-11.
- C1 Total Exchange Volume was calculated as (B + S) / 2 through 2019-10-04; the current convention is B + S.
- Intraday 1-minute/10-minute files gained correction/bust handling and removal of indicative/unsettled trades effective November 8, 2026. Do not assume the same vintage behavior for historical EOD files.

Do not mechanically shift or rescale these fields from prose alone. Obtain stratified actual-file examples and independently reconcile the date grain before constructing a panel. Use final, not preliminary, EOD files for OI/industry-volume features; record actual receipt time prospectively.

Sources:
- https://datashop.cboe.com/cboe-options-open-close-volume-summary
- https://datashop.cboe.com/documents/Open_Close_EOD_Spec_v1.3.pdf
- https://www.govinfo.gov/content/pkg/FR-2024-07-01/pdf/2024-14386.pdf

## 6. Feasibility disposition and next gates

**Priority ranking**
1. **Conditional paired pilot:** OPRA-wide Option Trades + Option Quotes. It offers the broadest historical trade/quote surface and the best route to market-wide signed option flow, IV/skew and SOD OI features.
2. **Complementary conditional pilot:** Cboe Open-Close EOD. It offers capacity and open/close labels but only on Cboe exchanges, with material historical OI/volume convention breaks.
3. Keep Cboe TBT as a separate candidate only if its exchange scope, trade-condition lineage and overlap with Option Trades are shown to add independent information.

**Hard gates before any purchase or signal test**
- Obtain written price, data-license, internal-use, external-derived-data and retention terms. The public repository is not an approved location for licensed raw or derived data.
- Obtain a stratified 335-underlying/date availability matrix, including delisted, renamed, class-share and acquired names; the product pages warn that some symbol/date selections may be unavailable. A static 335-symbol snapshot is not historical F80 membership.
- Request a small, authorized sample across multiple eras (including pre/post 2018, 2019 convention changes and current data) and independently validate OPRA condition IDs, quote alignment, option roots, corporate actions, missingness, OI dates and preliminary/final file differences. No sample was requested or downloaded in this phase.
- Establish prospective first-receipt and correction-vintage logs. Historical trade timestamps are execution times, not proof of when the vendor file was available. Use no same-day signal unless the actual delivery clock is independently verified; otherwise use the first full session after receipt.
- Build effective-dated underlying/security and option-root identity before joining to historical F80. Do not survivorship-filter or treat today's ticker as a historical identifier.
- Keep hypotheses separate: (a) quote-relative signed delta notional from Option Trades; (b) capacity × buy/sell × open/close flow from Open-Close; (c) IV skew/term and SOD OI changes from Option Quotes. Test each independently before testing complementarity. These are market-flow hypotheses, not labels for informed or institutional actors.
- Compare only against frozen LTM/F80 with identical exposure, costs and chronological OOS. Pre-register trade-condition filters, normalization, holding-period selection, event aggregation, multiple-testing controls, block bootstrap and leave-one-symbol-out. Distinguish predictive information from price/volatility chasing.

No vendor account, purchase, license acceptance, sample download, API request, raw data or licensed data was used. No signal, event study, backtest, OOS, bootstrap, LOO or holdout test was run. No universe, capital, exposure, costs, parameters or production changes.

**Frozen control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains unchanged.
