# Phase 353 — Cboe daily Open-Close flow + OPRA option-context feasibility

**Date:** 2026-11-13 UTC  
**Scope:** Official Cboe EOD specifications, product-page history/delivery claims, and public sample schema only.  
**Mode:** No paid data, vendor contact, trial, licensing acceptance, return test or alpha test.

## Research question

Can a daily participant-capacity/open-close feature be paired with a broad OPRA option-context file for a swing strategy, avoiding the historical-vintage and correction burden of cumulative intraday snapshots?

## Preregistered source roles

1. **Cboe Open-Close EOD:** participant capacity, buy/sell, open/close volume by option series across C1, C2, BZX and EDGX.
2. **Cboe Option EOD Summary:** broad OPRA option-series context, 15:45 NBBO and optional IV/Greeks, plus EOD quotes, trade volume, VWAP and start-of-day OCC open interest.

These are source roles, not evidence that any capacity group is informed.

## Official-document findings

### Open-Close EOD v1.3

- One historical file per trade date per exchange.
- Subscription delivery has a preliminary and a final file. The specification says they are typically delivered 00:30–01:00 U.S. Eastern the next morning.
- The preliminary file obtains total-industry volume and open interest from OPRA; the final file obtains authoritative values from OCC. Use the final file for these fields and preserve both versions if prospective capture is ever activated.
- Participant buckets include Firm, Broker-Dealer, Market Maker, Customer and Professional Customer. Customer/Professional Customer are further divided by trade size.
- Historical start on the product page: C1 EOD 2005-01-03; BZX/C2/EDGX EOD 2018-01-02.
- The product page says C1 includes RTH and GTH, while the Option EOD Summary specification says its coverage is RTH only. Session alignment must be resolved before normalizing or joining C1 flow to option context.

### Option EOD Summary v1.1

- OPRA-listed U.S. stock, ETF and index options, RTH only; product page says history from January 2012.
- 15:45 ET NBBO snapshot, optional 15:45 IV and Greeks, and EOD quote/volume/VWAP fields.
- open_interest is start-of-day OCC open interest, not end-of-day open interest.
- The specification says IV may be zero when the model lacks sufficient inputs, the option price is below intrinsic value, or IV exceeds its upper limit. Zero IV must be treated as invalid/missing, not as zero volatility.
- On early-close days, the field named 1545 represents 12:45 ET. A calendar-aware timestamp is required.
- The PDF file specification does not include a series-type/deliverable field matching Open-Close EOD's S/N/F series_type. Nonstandard/Flex joins must not be assumed from root/expiry/strike/type alone.

### Point-in-time interpretation

The Open-Close EOD specification's next-morning schedule is useful and more concrete than the 1-minute product's generic "minutes after each interval" wording. However, "typically delivered" is not a per-file first-receipt SLA and historical purchases/backfills do not provide an immutable receipt ledger. Do not admit strict historical PIT on that basis alone.

A prospective archive, if later authorized, must retain:
- preliminary and final files separately;
- first-receipt UTC, exchange, market date, file name, version and SHA-256;
- any later replacement/correction as a new immutable object;
- an execution boundary after the final file's observed receipt.

## Sample audit

The hosted workflow downloads the two public Cboe sample archives and the linked 1-minute sample. It stores only hashes and aggregate metadata in the artifact; raw sample files and symbol-level rows are not uploaded.

The product page labels the 1-minute sample as effective November 8, 2026, but the linked file name is Cboe_OpenClose_2026-09-30_15_20_1.csv.gz. Its market date predates the cutover and therefore cannot validate the post-v1.8 schema/correction regime. This is a source-page/sample-link inconsistency, not proof that the live feed failed to change.

## Candidate daily feature design — not yet authorized for returns

If all remaining gates pass, preserve separate feature families:
- Firm and Broker-Dealer opening net volume;
- Market-Maker buy/sell activity;
- Customer and Professional-Customer opening net volume by size bucket;
- closing activity as a separate unwind/cover hypothesis;
- put and call flow separately;
- option-level flow normalized only with a validated, time-aligned denominator;
- 15:45 IV/Greeks and SOD OI as companion context, not as participant flow.

Before any return test, controls must include prior underlying returns/momentum, volatility, liquidity, earnings, market/sector beta, optionability and dealer-hedging alternatives. Use only the final EOD file after observed availability and execute no earlier than the next eligible session.

## Gates and decision

- Sample schema: to be determined by hosted run.
- Historical universe coverage and inactive/delisted option-root continuity: not established by public samples.
- Historical first-receipt/vintage PIT: not established.
- Prospective capture: not activated.
- Licensing: not confirmed; Cboe raw data is internal-use only and external derived-data distribution requires approval.
- Return/alpha/OOS/holdout: not authorized or used.
- F80_TOP20_PARTIAL50_BASELINE_C20: frozen.

**Decision:** prioritize the daily EOD pair over the 1-minute snapshot route for the next options-flow feasibility gate, because it combines participant opening/closing measures with broad OPRA option context and a documented next-morning delivery process. This is a research-priority decision only, not a source admission or alpha claim.
