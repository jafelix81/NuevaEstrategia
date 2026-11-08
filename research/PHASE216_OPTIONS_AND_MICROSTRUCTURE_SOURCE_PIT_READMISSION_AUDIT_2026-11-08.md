# Phase 216 — Options and market-microstructure source PIT re-admission audit
**Audit date:** 2026-11-08  
**Status:** `NO_OPTION_OR_MICROSTRUCTURE_SOURCE_STRICT_PIT_ADMITTED`  
**Control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Executive decision

The latest hosted evidence does not admit any options-flow, open-interest, volatility-surface, venue microstructure, or short/lending source for a historical alpha test. Several products have useful schemas or substantial retrospective history, but none currently satisfies the combined requirements for actual first availability, immutable correction vintages, effective-dated contract/security identity, representative historical universe coverage, and usable licensing.

This is an evidence/readiness decision, not a claim that the underlying economic hypotheses are false. No source is labelled “smart money” merely because its fields are described as institutional, customer, or participant flow.

No return test, feature selection, holdout use, vendor contact, data purchase, or production change was made.

## 1. Latest hosted evidence reviewed

All runs below were inspected at job/log/artifact level. The artifact digests are GitHub's uploaded ZIP SHA-256 digests.

| Audit | Run / artifact | Hosted result relevant to admission |
|---|---|---|
| Phase 183 cross-source gate matrix | [42491346373](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42491346373) / 13622055678 | 13-source baseline; 0 PIT-admitted, 0 alpha-admitted |
| Phase 185 Cboe Open-Close chronology | [42491346732](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42491346732) / 13621239943 | 8 venue/interval rows; 0 strict-PIT rows |
| Phase 186 Nasdaq Trade Outline | [42491346553](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42491346553) / 13621552535 | 6 venues; 0 strict-PIT-admitted venues |
| Phase 187 ORATS Near-EOD | [42491346636](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42491346636) / 13620554871 | 716,822 rows; 5,787 underlyings; no row-level updated-at field; first receipt unverified |
| Phase 188 ORATS Time & Sales | [42491346275](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42491346275) / 13621985907 | 351,324 estimated requests for 335 names over the advertised history; 24.4 continuous days at the documented rate cap |
| Phase 189 Form SHO / SLATE | [42491346621](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42491346621) / 13621955977 | Future prospective candidates only |
| Phase 173 Cboe Option EOD OI semantics | [42491346719](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42491346719) / 13620988850 | OI is prior-night OCC EOD at the start of quote date; PIT and broad coverage remain blocked |
| Phase 174 Cboe Option Quotes | [42491346684](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42491346684) / 13620644478 | 115,617 populated rows; 94,607 failed strict contract-schema validation; only one variant passed on one underlying |
| Phase 197 Cboe CALCS Greek-normalized sample | [42491346268](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42491346268) / 13621886153 | 74,999 rows, one underlying, 308 contracts; measurement diagnostic only |

## 2. Source-by-source disposition

### A. Cboe Options Open-Close — best public position-side construct, still conditional

Phase 185 corrected a material historical interpretation:

- The current archive start date is not the live-product start date.
- The conservative documented live floor for 10-minute Open-Close is 2020-08-03.
- The conservative legal floor for the one-minute product is 2025-07-13; the first possible regular session is 2025-07-14.
- Earlier archive rows are retrospective backfill unless actual historical subscriber-receipt logs prove otherwise.
- Intraday files are cumulative day-to-date snapshots. First differences are changes in published state and can reflect late trades, corrections, busts, or cancellations; they are not automatically clock-interval trade volume.
- Published latency envelopes (10-minute: 0–5 minutes; one-minute: 2–5 minutes) do not replace actual first-receipt timestamps.
- Cboe EOD files are typically delivered next day around 00:05–03:00 ET but can be delayed until after the market opens. A nominal schedule is not per-file receipt evidence.

**Decision:** retain as a conditional participant-capacity/open-close research candidate. Do not backdate pre-launch archives, do not infer beneficial-owner identity, and do not admit any row without actual first receipt, immutable vintages, correction lineage, and effective-dated contract/underlying identity.

### B. Nasdaq Trade Outline — do not procure on current evidence

Phase 186 covers six venue products. The audit found:

- No venue passes strict PIT because actual first receipt, immutable revisions, effective-dated identity, and historical universe coverage remain unverified.
- Orders routed away are included and no routed-away flag is supplied. Cross-venue sums therefore cannot be represented as a consolidated OPRA panel.
- NTX one-minute snapshots are not trade-by-trade directional flow and do not disclose buy/sell side or trade count.
- Published intraday pricing is USD 12,000/month; the discounted 36-month intraday history quote is USD 57,000 for current subscribers (USD 171,000 ad hoc).

**Decision:** not procurement-priority. The measurement and PIT gaps are unresolved, and the quoted historical spend is not justified by current evidence.

### C. ORATS Near-EOD — broad sample, no verified historical knowledge clock

Phase 187's 2024-01-03 public sample contained 716,822 rows and 5,787 underlyings. The schema/row diagnostics passed, but:

- The sample has no row-level `updatedAt` field (716,822/716,822 absent).
- Historical archive first receipt and immutable vintages remain unverified.
- A partial ticker/expiration/strike key produced 1,590 collisions; these are not proven duplicate contracts because the sample lacks the full contract identity fields needed to adjudicate them.
- The `cOpra`/`pOpra` fields remain opaque pending semantic and uniqueness validation.
- The underlying reference price is put-call-parity-derived, not an independent stock price.

**Decision:** keep only as a conditional volatility/OI/quote-context sample. Do not treat it as signed flow or strict PIT. A future sample must resolve full contract identity, first receipt, revisions, delisted coverage, and professional-use terms.

### D. ORATS Time & Sales — prospective capture only, not a full-universe backfill plan

The documented event feed has useful NEW/CANCEL, event-time, NBBO, condition, and inferred aggressor-side fields, but the Phase 188 acquisition calculation is operationally material:

- 335 symbols × the advertised history implies approximately 351,324 requests.
- At 10 requests/minute this is about 24.4 continuous days, excluding retries, storage, and validation.
- A 335-name sweep takes about 33.5 minutes at the documented rate limit, so it cannot meet a 30-second refresh bucket.
- Historical first-live date, first-receipt vintages, classifier accuracy, correction/replay behavior, and inactive-name coverage remain unverified.

**Decision:** conditional prospective microstructure candidate only. Do not purchase or launch a full-universe backfill until a narrow licensed sample demonstrates the missing gates and the intended decision cadence is revised.

### E. Cboe Option Trades CALCS — useful measurement diagnostic, not an admitted flow feature

The Phase 197 sample has 74,999 rows for one underlying and 308 contracts. Only 52,346 rows (69.8%) were classifiable exactly at the NBBO ask or bid; 149,838 of 531,227 contracts by volume (28.2%) remained unclassified.

The same sample produced materially different directional summaries:

- Ask-minus-bid contract volume: **−36,763**.
- Delta-weighted underlying imbalance: **−8.39%**.
- Option-demand delta imbalance: **+0.285%**.
- Vega imbalance: **−6.95%**.

This divergence is a warning against treating raw call/put or contract-count imbalance as underlying directional exposure. It is not predictive evidence: the sample is one day/one underlying, no contract multiplier was applied, adjusted deliverables were not verified, quote datetime was not used, and trade-condition filters were not applied.

**Decision:** retain the parser/measurement diagnostic. No signed-flow feature or alpha admission.

### F. Cboe Option EOD Summary / open interest

Phase 173 confirms that the OI field is previous-night OCC EOD at the start of the quote date, not same-day closing OI. The audited public sample contains two variants of 32,672 rows across SPX, SPY, TSLA, and VIX; only one underlying overlaps the legacy 335-name list.

First-receipt vintages, broad universe coverage, and licensing remain unverified. OI is a contract-state measure, not buyer direction or participant identity.

**Decision:** conditional state/volatility context only. No same-day-close interpretation and no alpha test.

### G. IvyDB US Open Interest — best long-history contract-state candidate, not directional flow

Phases 145–147 provide a careful measurement contract:

- Vendor documentation advertises history from 1996 and permanent security/option identifiers, with historical ticker/name changes.
- The separate morning `Open_Interest` file contains prior-session OI and is described as provided by 09:00 ET; that schedule is not an actual historical first-receipt ledger.
- The `Option_Price` OI field has a timing regime break after 2000-11-28.
- Daily corrections/patches must be preserved as immutable receipt-time vintages. The Phase 147 append-only as-of ledger passed 25 hosted tests, but no actual licensed patch chain or first-receipt archive has been validated.
- OI changes are not buyer direction, gross opening volume, or a replication of buyer-initiated-to-open flow.

**Decision:** keep as the leading long-history contract-state/risk-context candidate if a sample is later authorized. Do not call it Smart Money and do not test until a raw multi-year sample, patch chain, optionable-universe coverage, effective contract identity, actual receipts, and license are verified.

### H. IvyDB TradeFlow / IVolatility / other signed-flow vendors

IvyDB TradeFlow advertises 2016 history but launched on 2026-09-30. Its one-session 99.9% direction-assignment example is a coverage statistic from one SPY FOMC session, not independent accuracy validation. “Institutional 2” is an aggressive-liquidity-demand proxy, not all institutional activity or beneficial-owner identity; “Institutional 1” is nested inside “Institutional 2.” Participant/lot-size field history, classifier-version history, first receipts, corrections, raw samples, and licensing remain unresolved.

IVolatility Signed Flow has no endpoint-specific raw sample, historical receipt ledger, correction policy, or effective-dated identity validation in the repository.

**Decision:** both remain conditional candidates, not features. Do not interpret vendor participant proxies as verified accounts or institutions.

### I. Future short/lending disclosures

Phase 189 confirms these are not historical rescue sources:

- Form SHO's first reporting period is 2028-01, with the first filing due 2028-02-14; manager filings are confidential and public aggregates are threshold-censored.
- FINRA SLATE public dissemination is required from 2029-03-29; lender/borrower identities are not public and loan amount is delayed T+20 business days.

**Decision:** prospective research only after implementation and actual first-publication/vintage capture. Keep separate from FINRA short volume and settlement short interest.

### J. Reference and context sources

- Databento Security Master is reference infrastructure, not alpha. Its advertised history starts in 2005, but first customer receipt is not provided; update cadence, instrument-count scope, pricing, US common-equity coverage, and sample access remain unresolved.
- SEC MIDAS has long daily history but quarterly publication; exact first-publication timestamps for historical archives remain absent. Hidden volume is on-exchange hidden-order activity, not dark-pool flow.
- FINRA ATS/OTC aggregates are revised and do not identify counterparties; short-volume selection failed the prior economic gate.
- CFTC TFF/COT is broad index-regime context, not stock-level flow; its complete historical release calendar is unavailable from the public archive alone.
- SEC FTD remains blocked by historical active-universe/security identity. Form SHO/SLATE do not supply a pre-compliance history.

## 3. Updated research sequencing

This is a sequence for resolving evidence gaps, not an expected-alpha ranking:

1. If a licensed sample is later authorized, request a bounded IvyDB US OI sample with original delivery receipts and all patch vintages; measure optionable coverage against a historically defined universe, not only the legacy 335 list.
2. In parallel, require an IvyDB TradeFlow sample/dictionary that identifies exact interval semantics, field-specific backfill start dates, classifier versions, correction rules, and actual receipt times.
3. For Cboe Open-Close, seek historical first-subscriber receipts and immutable cumulative snapshots before using any archive row; preserve changes in published state separately from interval flow.
4. Keep ORATS Near-EOD as a lower-cost quote/IV/OI context candidate only after full contract identity, first receipt, and revision semantics are proven.
5. Do not spend on Nasdaq Trade Outline's 36-month archive or full Cboe trade-by-trade history under the current evidence.

No vendor was contacted and no purchase, trial, account, API key, or terms acceptance was made.

## 4. Repository and validation controls

- Source baseline: `research/phase183_options_smart_money_source_gate_matrix.json`.
- Hosted Phase 183 artifact SHA-256: `e44b1a3620f046016ba1cbe114e343ae3840f02391c639ef56bc65c448d4c672`.
- Phase 185 artifact SHA-256: `d9575f5e9df29fce61eaef81955105b1d4f88827f65980f4630acaecd9e1efc9`.
- Phase 186 artifact SHA-256: `ec3cccda54b691e875db067b0b3057a6fb4c0671b9401e9fa71b770dd04fe352`.
- Phase 187 artifact SHA-256: `b41a5237b4899a7a801a11c4675ff1a153324ed92506b250d7eab67a29b3b376`.
- Phase 188 artifact SHA-256: `59a206de7d8885be4b50946190e0f12e7e455a33430ada159fbff8610c5c1696`.
- Phase 189 artifact SHA-256: `de1530738ae29c27f1da0db333eaf301cfe1940e9f724878e73417e60841e9b0`.
- Phase 173 artifact SHA-256: `e7f396122d18685b98bd303e54fd394c33573215a5f87d2c308b9790fe4554df`.
- Phase 174 artifact SHA-256: `231166d4bbb00e621b9debe9697290e715337d6411d3d43cac29256030186793`.
- Phase 197 artifact SHA-256: `111a9e7f397099a7430bba32b406227f2f1bb9889738fe940b3762581af7933e`.

At preflight, the latest 100 repository Actions runs were all completed: 98 success, one failure (the initial Phase 214 attempt, later fixed), and one cancelled/superseded Phase 214 attempt. The current PR head uses `[skip ci]`, so these runs are on the preceding PR head, not on the current head. Separate status-filtered checks returned zero in-progress, queued, waiting, or requested runs. No workflow was duplicated.

Branch inventory: 130. PR #13 remains open, unmerged, and mergeable. This phase adds no workflow to avoid another broad PR path-filter fan-out.

## 5. Final controls

- No option/microstructure source is strict-PIT admitted.
- No forward-return, alpha, bootstrap/LOO, or chronological OOS test was run.
- No holdout was used; the legacy holdout remains `CONSUMED_NOT_PRISTINE`.
- No production or universe changes.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
