# Phase 168 — Cboe Open-Close EOD public sample and PIT audit

**Date:** 2026-11-06  
**Status:** offline parser and regression suite complete; hosted public-sample retrieval pending.  
**Research role:** complementary Cboe-venue opening/closing and capacity data; schema feasibility only, not a Smart Money signal.

## 1. Why EOD is the next useful Cboe check

Phase 167 validated one public 1-minute C1 sample. Intraday files deliberately leave fields 10–17 empty, including open interest and total industry volume. The EOD product is materially different: it includes prior close, OHLC, exchange/industry volume and open interest, as well as the same capacity × buy/sell × open/close buckets.

The official product page advertises EOD history from 2005-01-03 for C1 and 2018-01-02 for BZX, C2 and EDGX. These are advertised product start dates, not proof of complete daily/security coverage, immutable first delivery or delisted-universe coverage.

## 2. Source semantics that must be preserved

The current EOD specification (v1.3, 2025-11-10) describes one file per trade date and exchange for historical orders. Subscriptions deliver a preliminary and a final file each day, typically between 00:30 and 01:00 U.S. Eastern the next morning.

- Preliminary total_industry_vol and open_interest are sourced from OPRA.
- Final total_industry_vol and open_interest are sourced from OCC and are described as authoritative; the values may differ from preliminary.
- The parser compares preliminary/final versions only when both are actually present in the sample. It never assumes the preliminary and final values are identical.
- Capacity/origin buckets are operational clearing-origin categories: F/L/J = Firm, B = Broker-Dealer, M/N = Market Maker, C = Customer, U/W = Professional Customer. They are not named beneficial owners or proof of informed trading.
- Customer and Professional Customer buckets are split by trade size. Do not add them to any separate overlapping category unless the source explicitly defines the categories as disjoint.

The EOD file has 86 columns: 18 contract/price/volume/OI fields and 68 capacity/action quantity/volume fields. The new Phase 168 parser validates the complete EOD schema separately from Phase 167's 88-column intraday schema.

## 3. Historical convention breaks

Cboe documents historical conventions that prevent blind splicing across the entire advertised history:

| Field / venue | Documented historical convention |
|---|---|
| C1 OI and previous OI | Values shifted one day ahead through 2019-10-04 |
| C2 OI and previous OI | Values shifted one day ahead through 2018-05-11 |
| C2 total industry volume | Values doubled through 2018-05-11 |
| C1 total exchange volume | (B + S) / 2 through 2019-10-04; current convention is B + S |
| C1 previous close | C1-exchange last trade only through 2019-10-04 |
| C2 previous close | C2-exchange last trade only through 2018-05-11 |
| C1 Global Trading Hours | Available from 2023-12-11 |

These are documented regime breaks, not corrections applied by this phase. Any future historical panel must carry venue × date convention flags and validate each transformation against raw files before normalizing.

## 4. Point-in-time ruling

The subscription schedule is a typical delivery window, not a verified first-receipt timestamp for any historical file. The public sample's HTTP Date, Last-Modified or ETag cannot substitute for the original subscriber receipt log.

For a future daily signal:

1. Store preliminary and final files as immutable versions with SHA-256, exchange, quote date, source version and actual first-received timestamp.
2. At each decision time, select only the latest version received strictly before the decision.
3. A later final file or correction may update the state only from its own receipt time; never backdate it.
4. Treat the next-morning schedule as an operational expectation only until actual delivery logs are available.
5. Keep Cboe venue scope separate from all-OPRA volume; do not call the fields whole-market flow.
6. Resolve effective-dated option-series terms and underlying identity, including adjusted/nonstandard/Flex contracts and delisted underlyings, before joining to equity returns.

The public page states that raw data are licensed for internal use only and may not be redistributed; external distribution of derived data requires additional licensing and approval. This phase writes only aggregate metadata and does not retain sample rows or symbols.

## 5. Phase 168 implementation and live gate

The new auditor downloads the public DataShop sample ZIP in GitHub Actions, parses CSV members in memory, validates the 86-column EOD schema, checks filename/date/exchange identity, contract keys, nonnegative integer fields and duplicate series, and compares preliminary/final OI and volume only if both versions occur in the sample. It stores only counts, hashes, source metadata and validation diagnostics.

Offline tests cover schema width, file naming, preliminary/final differences, date mismatch, invalid OI/price values, duplicate series, nested ZIPs, malformed archives and raw-symbol privacy. The suite was run locally before commit.

Hosted sample retrieval is pending. If the public endpoint is unavailable or the returned archive is not the documented EOD sample, the workflow uploads a metadata-only blocked result and fails the live gate rather than silently treating the sample as valid.

## 6. Decision and remaining gates

**Current decision: EOD is a higher-value complementary Cboe feasibility target than another isolated intraday schema check, because it carries open/close state and OI. It is not yet approved for feature construction.**

Even a successful public sample only establishes schema/sample feasibility. Before any return test, require:

- multiple dates and exchanges, including preliminary/final pairs;
- actual receipt timestamps and immutable correction lineage;
- complete historical date/security coverage and missing-file diagnostics;
- documented normalization of the venue/date convention breaks above;
- effective-dated option contract and underlying identity, including inactive/delisted names;
- licensing review and a cost model;
- comparison against IvyDB OI/IV and, if licensed, all-venue TradeFlow without assuming category labels identify informed accounts.

No features, forward returns, bootstrap/LOO, OOS, final holdout, vendor purchase/contact or production change are part of Phase 168. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Official sources

- Cboe product page: https://datashop.cboe.com/cboe-options-open-close-volume-summary
- EOD specification v1.3: https://datashop.cboe.com/documents/Open_Close_EOD_Spec_v1.3.pdf
- Phase 167 intraday sample audit: research/PHASE167_CBOE_OPENCLOSE_V18_PUBLIC_SAMPLE_AND_CUTOVER_AUDIT_2026-11-06.md


## 7. Hosted preflight correction

The first hosted run (42290524336) passed the initial 17 offline tests and successfully retrieved a ZIP, but the parser stopped because the CSV member basename did not match the assumed exchange/date filename pattern. This was a parser identity assumption, not an HTTP/network failure. The metadata-only artifact 13538813954 recorded the unrecognized-member-filename error; no raw rows or underlying symbols were retained.

The correction now:
- keeps the member basename for audit;
- permits schema-only parsing when a public sample uses a generic member name, while explicitly setting exchange and preliminary/final identity to UNKNOWN;
- derives quote date from CSV rows only when exactly one date occurs;
- detects an intraday-like header and refuses to label it EOD;
- leaves preliminary/final comparisons disabled when the member name does not identify those versions.

The corrected parser and 19 offline tests pass locally. A second hosted run is still required before the sample's actual schema and identity can be reported.

**Additional historical boundary:** the EOD specification states that C1 has a format change beginning 2011-01-02; pre-2011 C1 history requires the separate legacy EOD specification. Therefore the 86-column parser in this phase cannot be applied to all advertised C1 history back to 2005. That older period requires a separately audited parser and convention bridge.
