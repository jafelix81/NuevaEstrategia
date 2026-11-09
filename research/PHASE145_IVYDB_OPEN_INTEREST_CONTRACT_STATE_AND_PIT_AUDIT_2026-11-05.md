# Phase 145 — IvyDB US open-interest contract state and PIT audit

**Date:** 2026-11-05  
**Inputs:** Phases 133, 136–144; current OptionMetrics product documentation; IvyDB US Reference Manual v5.0 (2021-01-12); OCC and Options Industry Council documentation.  
**Mode:** Product, schema, clearing-mechanics and point-in-time feasibility audit. No licensed raw data, vendor contact, purchase or forward-return test.

## Decision

**Promote IvyDB US open interest (OI) to a top-tier conditional, long-history contract-state source—not to a directional Smart Money signal.**

OptionMetrics currently advertises US equity and index option history from January 1996, including ETFs and ADRs, daily volume and OI, implied volatility, Greeks, permanent security IDs and historical ticker/name changes. Its daily patch files can revise prior observations. This is materially more useful for long-horizon OI research than OCC's public self-service OI page, which currently exposes only the past 24 months.

The critical semantic distinction is that OI counts outstanding contracts, not buyer direction or participant identity. A daily OI change can indicate net contract creation or elimination, but it cannot identify which side initiated, whether a customer or dealer was involved, or whether a buyer was informed.

Historical IvyDB backfill is **not yet strict PIT-approved**. The 2021 manual documents a morning delivery schedule, but no immutable first-receipt log or historical patch-vintage archive has been verified. A scheduled 09:00 ET delivery must not be substituted for an actual receipt timestamp.

## 1. Coverage and identity

The current [IvyDB US product page](https://optionmetrics.com/united-states/) advertises:
- Complete historical EOD records for US-listed equity and index options from January 1996, including options on ETFs and ADRs.
- Daily option volume and open interest, closing bid/ask, implied volatility and Greeks.
- A permanent security ID and historical security-name/ticker history, including securities that no longer trade.
- Daily updates and a separate daily patch file for corrections to earlier prices/calculations.

This is broad options-market coverage, not a complete equity universe. Only securities with listed options enter the option panel. We still need to measure optionable-name coverage against a survivorship-aware historical stock universe and preserve inactive/delisted names. The old manually selected 335-name list remains a diagnostic, not the research-universe boundary.

The IvyDB v5.0 manual says Security ID is unique over the security lifetime and is not recycled; Option ID uniquely identifies an option contract. The Security_Name history records effective-dated ticker, issuer, issue and CUSIP changes; a blank current ticker denotes a delisted security. These identifiers are preferable to ticker-only joins, subject to validation of adjusted contracts and historical mappings.

## 2. OI timing and the historical regime break

The [IvyDB US Reference Manual v5.0](https://lib.tsinghua.edu.cn/PDF/OptionMetricsshiyongzhinan.pdf), revised 2021-01-12, documents the following:

- IvyDB files are produced nightly from raw 15:59 ET option-price information.
- The Option_Price OI field is lagged by one day after 2000-11-28; earlier records use a different timing convention. This is a structural timing break. Do not splice pre- and post-break OI as if their knowledge times were identical.
- A separate Open_Interest file contains the previous day's OI, is not part of the standard release files, and is described as being provided each morning by 09:00 ET to clients who need it earlier than the OI field in Option_Price.
- The Open_Interest file's Date is the morning on which it was created. It contains Security ID, date, option symbol, symbol flag and OI.
- The manual's revision history says historical patching was enabled in the October 2019 release. The current product page confirms daily patch files for corrections.

Implications:
1. The 09:00 ET statement is a delivery schedule, not proof that every historical file was first received at 09:00 ET.
2. A latest corrected backfill can contain information unavailable in the original release. Do not backdate patches.
3. Strict PIT requires immutable raw files, cryptographic hashes, actual first_received_at timestamps, source/version metadata and separately timestamped patches.
4. Until those records exist, the long historical panel is descriptive/exploratory only. A prospective capture can become strict PIT after the actual files and receipts are archived.
5. For a conservative historical design, exclude the pre-2000-11-28 timing regime unless the exact source-file semantics and publication times are separately established.

## 3. What OI can and cannot identify

The [Options Industry Council](https://www.optionseducation.org/news/open-interest-why-it-matters) explains the clearing mechanics:

- Both counterparties opening creates new OI.
- Both counterparties closing reduces OI.
- One side opening while the other closes transfers an existing position and leaves OI unchanged.
- OCC consolidates exchange trade reports and also accounts for exercises/assignments.

Therefore:
- Positive ΔOI is not buyer-initiated demand; every open contract has both a long and a short side.
- Negative ΔOI is not necessarily informed selling or bearish flow.
- Zero ΔOI does not mean no new positions were opened; transfers can leave OI unchanged.
- ΔOI is net contract-state change, not gross opening volume, aggressor direction, beneficial-owner identity or dealer/customer classification.
- Expiration, exercise/assignment, corporate actions and adjusted deliverables can change OI independently of the directional hypothesis.

This source cannot reproduce Pan–Poteshman's buyer-initiated-to-open measure. It can complement signed flow by measuring whether outstanding contract inventory grew or shrank after clearing.

## 4. Candidate features (preregistered semantics; no alpha test)

Only after the identity, receipt and coverage gates pass, evaluate a small set of contract-level state variables:

1. **Net OI change:** current OI minus prior-session OI for the same Option ID, only across consecutive exchange sessions and unchanged contract terms.
2. **OI change / prior OI:** normalized state change where prior OI is positive.
3. **OI change / session volume:** net clearing-state change relative to activity; not the fraction of trades that opened.
4. **Session volume / prior OI:** turnover proxy, not direction.
5. **Call/put and tenor/moneyness partitions:** preserve separate contract groups; never treat calls as automatically bullish or puts as automatically bearish.
6. **Risk-weighted OI state:** only if the Greek used was already known at the feature's knowledge time and the deliverable/multiplier mapping is valid.

Contract/session rules:
- Canonical key: Security ID + Option ID, with a date-effective contract-terms fingerprint.
- The morning Open_Interest file does not list Option ID. Map its Security ID + symbol + symbol flag + effective date to Option_Price/Option_Info and Option ID only through an exact, unique, date-valid crosswalk. No fuzzy ticker or OSI reconstruction.
- Include contract size, adjustment factor, deliverable, AM/PM settlement, expiration, call/put and strike in the terms fingerprint.
- Do not compute ΔOI across missing sessions, new listings without a prior observation, contract-term changes, expirations or unresolved corporate-action transitions.
- Keep negative changes; never clip or convert them into directional buying/selling.

Every feature's knowledge time is the actual first receipt of the file containing the OI observation. The research helper added in this phase fails closed on missing/naive receipt timestamps, duplicate contract-session rows, non-consecutive sessions, changed contract terms and expiry sessions.

## 5. Public OCC alternative

The current [OCC Open Interest page](https://www.theocc.com/market-data/market-data-reports/volume-and-open-interest/open-interest) says data are available for the past 24 months. OCC Flex Reports and other self-service daily reports also show a 24-month window. Phase 133 independently found the Flex OI path unsuitable for long OOS history.

Decision: retain OCC for recent cross-checks and public validation, but do not treat the current self-service history as a long-history substitute for IvyDB US.

## 6. Source ranking after Phase 145

| Source | Role | Gate |
|---|---|---|
| IvyDB US OI / IV / Greeks | **Top conditional long-history contract-state and risk-context source** | Licensed sample, actual first-receipt/patch vintages, Option ID crosswalk and historical optionable-universe coverage |
| IvyDB TradeFlow | Top conditional all-venue signed-flow source | Raw sample, interval reconciliation, version lineage and first-receipt PIT |
| Cboe Open-Close | Complementary venue-specific capacity × buy/sell × open/close state | Broad contract identity, archive and historical first-receipt PIT |
| OCC public OI | Recent independent/public cross-check | 24-month self-service history; insufficient alone for long OOS |
| Cboe TBT / GRK | C1 execution diagnostic | Capacity-specific OPEN_CLOSE missingness and event-time join restrictions |

No cross-vendor agreement is counted as independent raw-market validation when the vendors derive from the same OPRA inputs.

## 7. Reproducible implementation and status

Added:
- **research/phase145_ivydb_open_interest_pit.py**: pure-Python strict receipt-aware OI state helper.
- **research/test_phase145_ivydb_open_interest_pit.py**: 15 offline tests covering signed changes, no-prior/gap handling, contract-term breaks, expiration, duplicate rows, actual receipt timestamps, source provenance, zero denominators and input-order invariance.
- **.github/workflows/phase145_ivydb_open_interest_pit.yml**: PR-only offline regression workflow; no data downloads or vendor credentials.

Local regression: **15/15 passed** before commit. The hosted workflow is the final repository validation gate.

## 8. Final status and next gate

No raw IvyDB sample was available, no optionable-universe coverage percentage was measured, and no historical first-receipt/patch-vintage archive was verified. No forward-return or alpha test was run; no final holdout was touched; no vendor contact, trial, purchase or terms acceptance occurred; no production strategy changed.

If authorized data later become available, the first task is not a return backtest. It is a same-date audit of the morning OI file, Option_Price/Option_Info crosswalk, contract terms, patch vintages, actual receipt timestamps and coverage against the historical equity universe. Only then can OI features be tested incrementally against frozen LTM/F80 and the separate options-flow hypotheses.

**F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.**

## References

- [OptionMetrics IvyDB US product page](https://optionmetrics.com/united-states/)
- [OptionMetrics IvyDB US Reference Manual v5.0 (2021-01-12)](https://lib.tsinghua.edu.cn/PDF/OptionMetricsshiyongzhinan.pdf)
- [OCC Open Interest self-service page](https://www.theocc.com/market-data/market-data-reports/volume-and-open-interest/open-interest)
- [Options Industry Council — Open Interest: Why It Matters](https://www.optionseducation.org/news/open-interest-why-it-matters)
