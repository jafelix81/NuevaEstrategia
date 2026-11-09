# Phase 212 — Form 144 intermediary-field and route-identifiability audit

**Date:** 2026-11-08  
**Disposition:** The broker-order versus direct-market-maker route is **NOT IDENTIFIABLE from the current public Form 144 fields**. Route-specific hypotheses are not testable from this panel alone. A mixed Form 144 notice-event hypothesis remains conditional on full-panel PIT and security-identity admission.  
**Control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Executive decision

Phase 211 correctly separated two legal mechanisms under Rule 144: filing concurrently with (a) placing a sell order with a broker, or (b) executing directly with a market maker. The remaining assumption was that the named intermediary could identify which route applied.

A direct review of all five Form 144 primary documents in the Phase 211 acceptance-clock pilot shows that the rendered Securities Information table has the same field label in every filing: **“Name and Address of the Broker.”** The SEC's current electronic-filing guide describes the entry more broadly as the broker or market maker expected to participate, with a separate entry for each intermediary and each security. Neither the five documents nor the guide provides a transaction-level route flag.

Therefore, resolving a name to a registered broker-dealer is not enough to identify the legal route. A broker-dealer may be named as the intermediary, but its registration record does not prove whether that specific transaction was handled as an agency broker order, directly executed against the firm as a market maker, or handled through another permitted manner. Market-maker status is security- and time-specific; firm identity alone is not execution evidence.

**Correction to Phase 211:** H1 (broker order placement) and H2 (direct market-maker execution) remain legally distinct, but they must not be assigned to observations using the Form 144 intermediary name. The route-specific split is unobservable in the current public panel.

## 1. Governing source semantics

1. Current eCFR 17 CFR 230.144(f)(1) permits broker transactions, transactions directly with a market maker, and qualifying riskless-principal transactions. Paragraph (h)(3) requires Form 144 to be transmitted concurrently with either placing a broker order or executing directly with a market maker. These are legal alternatives, not separate public fields in the five audited filings.
2. The SEC's electronic Form 144 guide says the Securities Information section identifies each broker or market maker expected to participate in the sale, with a separate entry for each broker/market maker and each security. The guide does not say that the named firm's registration type reveals which Rule 144(h)(3) route occurred.
3. The same SEC guide distinguishes the reporting person, the filing agent, and the issuer. A broker-dealer may also act as the authorized filing agent. Do not confuse the filer CIK, filing-agent identity, issuer CIK, and named intermediary.
4. Rule 144(h) notice filing is threshold-selected: for a reporting issuer, the notice threshold is more than 5,000 shares/units or aggregate sale price above $50,000 during a three-month period. The Form 144 panel is therefore not a census of all insider sales.

Sources:
- [17 CFR 230.144, current eCFR](https://www.ecfr.gov/current/title-17/chapter-II/part-230/section-230.144), especially paragraphs (f) and (h)(1)–(3).
- [SEC — File Form 144 Electronically](https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/file-form-144-electronically).
- [FINRA BrokerCheck — Charles Schwab & Co., Inc., CRD 5393](https://files.brokercheck.finra.org/firm/firm_5393.pdf).
- [FINRA BrokerCheck — Fidelity Brokerage Services LLC, CRD 7784](https://brokercheck.finra.org/firm/summary/7784).

## 2. Five-document primary-source audit

| Ticker | Form 144 accession | Rendered intermediary field | Named intermediary | Entity-resolution result |
|---|---|---|---|---|
| PINS | 0001921094-26-000697 | Name and Address of the Broker | Charles Schwab & Co., Inc. | Current FINRA firm identity candidate: CRD 5393 |
| SCHW | 0001949846-26-000451 | Name and Address of the Broker | THE CHARLES SCHWAB CORPORATION | Exact string unresolved; same name as the issuer, not automatically mapped to its broker-dealer subsidiary |
| SNOW | 0001959173-26-005295 | Name and Address of the Broker | Fidelity Brokerage Services LLC | Current FINRA firm identity candidate: CRD 7784 |
| ANET | 0001959173-26-006426 | Name and Address of the Broker | Fidelity Brokerage Services LLC | Current FINRA firm identity candidate: CRD 7784 |
| RUN | 0001921094-26-000789 | Name and Address of the Broker | Charles Schwab & Co., Inc. | Current FINRA firm identity candidate: CRD 5393 |

### Observed counts

- Primary documents inspected: **5/5**.
- Same rendered intermediary-field label: **5/5**.
- Explicit broker-order versus direct-market-maker route flag in the audited Securities Information rows: **0/5**.
- Distinct normalized intermediary strings: **3**.
- Rows mapping to two current FINRA BrokerCheck firm identities: **4/5**.
- Unresolved exact intermediary string: **1/5** (SCHW).
- Transaction routes identified from Form 144 alone: **0/5**.

The SCHW filing names “THE CHARLES SCHWAB CORPORATION” in the broker column even though that same entity is the issuer. This is an entity-normalization warning, not proof that the field is wrong. Do not silently rewrite it to “Charles Schwab & Co., Inc.” or infer a market-maker route.

The BrokerCheck references establish current firm identity for the two normalized names. They do not establish historical registration status at every event date, security-specific market-maker status, or the role actually performed in a particular transaction.

### Official primary documents inspected

- [PINS Form 144 primary document](https://www.sec.gov/Archives/edgar/data/1506293/000192109426000697/xsl144X01/primary_doc.xml)
- [SCHW Form 144 primary document](https://www.sec.gov/Archives/edgar/data/316709/000194984626000451/xsl144X01/primary_doc.xml)
- [SNOW Form 144 primary document](https://www.sec.gov/Archives/edgar/data/1640147/000195917326005295/xsl144X01/primary_doc.xml)
- [ANET Form 144 primary document](https://www.sec.gov/Archives/edgar/data/1596532/000195917326006426/xsl144X01/primary_doc.xml)
- [RUN Form 144 primary document](https://www.sec.gov/Archives/edgar/data/1469367/000192109426000789/xsl144X01/primary_doc.xml)

## 3. Revised event definition and test design

Retain one observable event definition:

`FORM144_RULE144_DISPOSITION_NOTICE_MIXED_ROUTE`

It means a public Form 144 notice associated with a Rule 144 disposition process. The notice is transmitted concurrently with one of the statutory mechanisms, but the public filing does not identify which mechanism occurred.

Permitted future research, only after full-panel PIT admission:

- Use the EDGAR acceptance timestamp and the first regular-session open strictly after acceptance as the conservative daily execution boundary.
- Treat the named intermediary as an entity/context field only. Do not use its BrokerCheck registration to infer transaction route.
- Keep route as `UNKNOWN_NOT_ENCODED` for all observations unless independent order/execution evidence becomes available.
- Use Form 4 only as ex-post validation. Never backfill Form 4 transaction details into the Form 144 event feature.
- Keep 10b5-1 adoption date as historical context, not event availability.
- Use independent PIT ADV/float/shares outstanding; do not use the anomalous Form 144 shares-outstanding field.
- Explicitly model threshold censoring and distinguish proposed quantity from completed sale quantity.
- Control for prior returns, volatility, volume, compensation/option exercise context, seller role and repeat notices.
- Compare against frozen LTM/F80 with identical exposure, costs and turnover. Use chronological validation, date-block bootstrap, LOO and a new prospective holdout after all choices are frozen.

A route-specific H1/H2 test is **not authorized** from Form 144 alone. If route-specific economics are essential, the data requirement is order/execution-level evidence or an independently verified transaction-route field; a firm-name lookup is not a substitute.

The combined notice-event hypothesis remains conditional. Because the observed cohort may mix order-placement notices with direct-execution notices, post-event effects can be diluted or have different signs. Any future estimate must state this mixture explicitly.

## 4. Admission decision

| Gate | Decision |
|---|---|
| Filing-level acceptance clock | Feasible in the five-pair Phase 211 pilot |
| Full-panel acceptance headers and amendment vintages | Not admitted |
| Intermediary entity normalization | Partial; 2 current firm identities, 1 unresolved name |
| Broker-order vs direct-market-maker route | Not identifiable from current Form 144 fields |
| Route-specific feature/alpha | Not authorized |
| Mixed Form 144 notice-event feature | Conditional only; not admitted |
| Forward-return/alpha test | Not run |
| Holdout | Not used; legacy holdout remains CONSUMED_NOT_PRISTINE |
| Production / universe / baseline | Unchanged |

## 5. Next steps

1. Bulk-recover and hash all Form 144 acceptance headers after the authorized `SEC_CONTACT_EMAIL` secret is configured.
2. Complete amendment-chain, issuer/class identity and point-in-time universe coverage.
3. Keep route unknown; do not spend cycles trying to infer it from current BrokerCheck firm registration.
4. If the composite notice cohort passes PIT and coverage gates, preregister a single mixed-route event study with route-unknown sensitivity explicitly disclosed. Do not run it on the current five-row pilot.
5. Continue options-flow and microstructure source audits in parallel; Form 144 is not a replacement for participant-identified options data.

## Reproducibility and controls

- Evidence manifest: `research/phase212_form144_route_identifiability_audit_result.json`
- Auditor: `research/phase212_form144_route_identifiability_audit.py`
- Tests: `research/test_phase212_form144_route_identifiability_audit.py`
- Local deterministic invariants: **9/9 passed**.
- This is a purposive five-filing semantic pilot, not a representative prevalence estimate.
- No SEC bulk requests were sent; no data were purchased; no vendor was contacted.
- No forward-return, alpha, bootstrap/LOO or OOS test was run.
- No holdout was used; no production, universe or portfolio change was made.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
