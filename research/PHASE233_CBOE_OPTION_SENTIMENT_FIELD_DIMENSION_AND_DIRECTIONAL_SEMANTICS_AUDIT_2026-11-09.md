# Phase 233 — Cboe Option Sentiment field dimensionality and directional-semantics audit

**Date:** 2026-11-09  
**Status:** Measurement-schema correction; no strict PIT or alpha admission  
**Scope:** Public Cboe DataShop specification v1.4 (05/25), Cboe FAQ, and Cboe's published early-exercise research. No raw Option Sentiment sample was obtained.

## Executive decision

Phase 232 correctly identified Option Sentiment as a potentially rich daily options dataset, but its 80 fields do not provide the cross-tabs needed for two of the proposed secondary hypotheses. In particular, the published schema does **not** expose signed flow by trade size or signed flow by OCC participant category.

The primary net-option-delta candidate also cannot yet be normalized or interpreted safely: the public specification gives a float and a short description, but does not state its units, sign convention, contract-multiplier/deliverable treatment, or complete aggregation rules. The specification also contains inconsistent footnote references for three fields described as directional.

**Decision:** suspend the primary feature definition pending provider clarification; kill the proposed large-size-directional and customer-directional hypotheses as unimplementable from the documented 80-field schema; retain non-ITM put/call volume only as a non-directional activity/composition control. No source, feature, or alpha test is admitted.

## 1. Authoritative source reconciliation

The publicly retrievable product document is:

- [Cboe DataShop Option Sentiment Specification, v1.4 (05/25)](https://datashop.cboe.com/Documents/Cboe_OptionSentiment_Specs.pdf)
- [Cboe DataShop FAQ](https://datashop.cboe.com/faqs)
- [Cboe: How Early Exercise Order Flow Impacts Equity Option Put/Call Ratios, 2022-12-29](https://www.cboe.com/insights/posts/how-early-exercise-order-flow-impacts-equity-option-put-call-ratios)

The PDF lists 80 fields. Phase 232's source pointer used a different Cboe CDN URL; that URL did not resolve in the current public retrieval, so this audit pins the DataShop Documents URL above as the inspected source. This is a source-pointer correction, not evidence that the alternate URL is permanently unavailable.

Cboe describes the product as using proprietary systems to identify the initiating side of nearly five million executions daily. That is a vendor description of its classification process, not an independently validated accuracy result. No raw Option Sentiment sample was found in the public documentation reviewed and no sample was downloaded.

## 2. Field dimensionality: what can and cannot be observed

The 80-field schema reports several separate marginal aggregates. It does not provide a general multi-dimensional cross-tab.

| Field family | Published fields | What is measured | What is not available in the documented schema |
|---|---|---|---|
| Directional aggregate | net_option_delta; call/put premium bought/sold; calls/puts bought/sold; directional_pct | Vendor-classified directional aggregate by selected option-side fields | Beneficial owner, verified account, complete contract-level signed flow, or all cross-tabs |
| OCC participant category | cust_volume, firm_volume, mkt_mkr_volume | Total option volume by OCC clearing category | Customer/firm/market-maker buy/sell, call/put, or net-delta cross-tab |
| Trade size | size1 through size1001up | Total volume by contract-size bucket | Signed volume or net delta within each size bucket |
| Days to expiration | dtx1 through dtx360up | Total volume by DTX bucket | Signed volume or net delta within each DTX bucket |
| Moneyness | ITM/ATM/OTM calls and puts | Total call/put volume by moneyness | Buy/sell side within each moneyness bucket |
| Open interest | call/put OI and OTM call/put OI | Aggregate contract-state context | Same-day opening flow or owner identity |
| Volatility / borrow | IV30, IV90, HV20, 25-delta skew, vega, implied borrow | Risk-pricing and borrow context | A standalone directional institutional-flow measure |
| Exchange | exchange volume fields | Venue-level total volume | Aggressor side or beneficial-owner identity by venue |

Consequences:

1. **Large-size directional flow is not constructible** from the published size buckets. They are total volume by size, not signed volume by size.
2. **Customer net directional flow is not constructible** from cust_volume. Customer, firm, and market-maker fields are separate total-volume aggregates; they are not cross-tabbed by call/put or buy/sell.
3. A customer-volume share may be studied as a participant-mix descriptor only. “Customer” is an OCC clearing category, not proof of retail status, sophistication, or beneficial ownership.
4. A non-ITM put/call ratio can be computed from total ATM+OTM call and put volumes, but it remains a non-directional volume-composition measure.
5. DTX and moneyness buckets can be controls for activity composition, not signed directional tenor/moneyness signals.
6. OI is a position-state measure, not a same-day opening/closing indicator.

## 3. Directional-field and footnote inconsistency

The PDF's table marks:

- net_option_delta with footnote 2;
- calls_sold and puts_sold with footnote 2;
- call_premium_bought/sold, put_premium_bought/sold, calls_bought, and puts_bought with footnote 3.

But the PDF's note 2 is a list of fields that may be blank when no value exists. That list includes avg_call_size, avg_put_size, cust_volume, firm_volume, mkt_mkr_volume, and the size buckets; it does not include net_option_delta, calls_sold, or puts_sold.

Note 3 describes the midpoint-based directional rule: above midpoint is classified as a buy, below midpoint as a sell, with spread, late, and tied trades excluded. That rule is the relevant directional-methodology note, yet three fields described as directional point to note 2 rather than note 3.

This is a documentation cross-reference inconsistency. It does not prove the underlying data are wrong, but it prevents us from silently assuming that the same classification/filtering rules apply identically to every field. Cboe should confirm the intended footnote mapping and field-specific inclusion rules.

The specification also says cancelled trades are backed out from “the totals” without enumerating every affected field. The scope should be confirmed before reconciling aggregates.

## 4. Primary net-option-delta measurement is not yet defined well enough

The field is typed as float and described as net option delta for directional trades. The public specification does not state:

- whether the unit is share-equivalent delta, contract delta, dollar delta, or another scaled quantity;
- the exact positive/negative sign convention;
- whether standard 100-share multipliers are applied;
- how adjusted contracts and non-standard deliverables are handled;
- whether delta is computed at execution-time underlying/option prices or another snapshot;
- how multi-leg/complex executions, corrections, cancels, and late reports affect the field;
- whether all directionally classified fields use the exact same trade-condition filters.

Therefore the Phase 232 proposal to scale net_option_delta by underlying share volume is **suspended**. It would be dimensionally invalid if the field is not already a share-equivalent exposure, and potentially misleading if contract multipliers or adjusted deliverables are handled differently from our assumptions.

The bought/sold premium fields are dollar-premium aggregates, not delta-equivalent stock exposure. Contract-count fields also omit delta magnitude. They may be separate candidate measurements after clarification, but must not be substituted for net delta without a pre-registered economic rationale.

## 5. Cboe's early-exercise evidence changes the controls, not the alpha conclusion

Cboe's 2022-12-29 research documents large deep-ITM option volume associated with early-exercise/assignment mechanics. It gives an example in which very large ITM put volume was followed by little change in next-day OI, and explains why this can distort ordinary put/call interpretation.

This supports the following controls:

- report ITM, ATM, and OTM activity separately;
- treat non-ITM put/call volume as a composition control, not signed flow;
- do not interpret volume exceeding OI as proof of opening positions;
- do not interpret next-day OI stability as proof of no economically meaningful activity;
- separate event/dividend/expiration mechanics from directional hypotheses.

Cboe's example is a market-mechanics explanation, not evidence that any Option Sentiment field predicts subsequent equity returns.

## 6. Revised hypothesis disposition

| Hypothesis | Phase 233 decision | Reason |
|---|---|---|
| Net option delta adds residual-return information | **Suspended pending provider clarification** | Units, sign, multiplier/deliverable and field-specific methodology are unspecified |
| Large-size directional flow | **Killed as unimplementable with current schema** | Size buckets are total volume, not side-specific |
| Customer net directional flow | **Killed as unimplementable with current schema** | OCC participant volumes are not cross-tabbed by call/put or buy/sell |
| Non-ITM put/call volume | Retain as non-directional control candidate | Moneyness fields are call/put totals without direction |
| Participant mix | Context-only candidate | Clearing categories do not identify beneficial owners or informed investors |
| IV, skew, implied borrow | Separate risk-state hypotheses | Do not presume equity-direction alpha |
| OI | Prior-night position-state context | Cboe FAQ says previous-night OCC EOD OI is used at the start of the trading day and remains static intraday |

No economic hypothesis was tested in this phase. “Killed” above means the proposed measurement cannot be constructed from the published schema; it does not mean the underlying economic mechanism has been empirically disproven.

## 7. Availability and strict-PIT decision

Cboe's product specification states:

- subscription preliminary file: after the trade-date close, target 8–9 p.m. ET;
- subscription complete file: next morning, target 5–6 a.m. ET;
- first subscription day: preliminary and complete may be generated around the same time and contain the same content;
- historical orders: complete files are delivered at the end of the order-processing day.

The general FAQ says daily equity/option files are typically uploaded the following day between 00:05 and 03:00 ET, but delays can push delivery until after the next market opens.

These are delivery targets/general operating guidance, not historical per-file first-receipt logs. A historical backfill delivered today cannot be assigned its original knowledge time from trade_date. Strict historical PIT remains blocked until original receipt timestamps and immutable correction/replacement vintages are evidenced.

A future live subscription could establish a prospective PIT panel only if every received file is archived with filename, SHA-256, server timestamp, first successful receipt timestamp, schema/version, and each later replacement as a separate vintage. No subscription or purchase was made.

## 8. Required provider clarification before any data order

If access is later authorized, request written answers and a representative raw sample covering early, middle, and recent dates:

1. Exact unit, sign, contract multiplier, deliverable, and aggregation formula for net_option_delta.
2. Intended footnote mapping for net_option_delta, calls_sold, and puts_sold.
3. Exact midpoint, spread, late, tied, complex, multi-leg, and condition filters for every directional field.
4. Whether participant, size, DTX, and moneyness fields are available in directional cross-tabs outside this 80-field file.
5. Denominator and null semantics for directional_pct.
6. Field-specific scope of cancelled-trade back-outs.
7. Whether historical files are byte-identical to original complete deliveries and how corrections/replacements are versioned.
8. Historical first-receipt logs, symbol coverage including delisted names, and effective-dated underlying identity.
9. Price, license, retention, and bulk-research rights.

Do not purchase or accept terms before these gates are answered and reviewed.

## 9. Reproducibility and controls

- Phase 232 field inventory is reused and checked for exactly 80 unique field names.
- The auditor emits the footnote mismatch list, field-dimension capability matrix, hypothesis dispositions, and PIT gates.
- Tests cover the three footnote mismatches, unavailable cross-tabs, OI timing, delivery limitations, and frozen controls.
- No raw sample was downloaded; no vendor was contacted; no data was purchased.
- No forward-return test, feature selection, bootstrap/LOO, chronological OOS, or final holdout was used.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; no production or universe change.

**Final disposition:** Option Sentiment remains a high-potential but unadmitted data-source candidate. Phase 232's broad secondary hypotheses are narrowed: two are not implementable with the published 80-field schema, the non-ITM ratio is non-directional, and the primary net-delta feature is suspended until its units and methodology are clarified.
