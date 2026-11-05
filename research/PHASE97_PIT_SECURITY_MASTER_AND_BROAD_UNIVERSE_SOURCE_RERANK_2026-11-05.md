# Phase 97 — PIT security-master and broad-universe source re-ranking

**Date:** 2026-11-05  
**Scope:** public-documentation re-audit of historical security identity, active/delisted coverage and candidate broad universes. No vendor contact, purchase, sample download, forward returns or strategy test.

## Executive decision

The binding research blocker is the missing historical eligible universe, not a lack of additional candidate signals. A separate broad-universe research line is justified if the original F80 335-name selection rule cannot be recovered. It must remain separate from F80 and use a rule declared before any return inspection.

Updated source ranking:

1. **CRSP US Stock Database — preferred return/delisting benchmark if access is available.** It documents over 32,000 active and inactive US securities, daily/monthly prices, corporate actions, permanent PERMNO/PERMCO, and coverage across NYSE, NYSE American, NYSE Arca, Nasdaq and Cboe BZX.
2. **Databento Security Master — preferred two-clock identity/reference layer.** The current schema exposes `ts_record` (when a record last changed) and `ts_effective` (when the record became effective), plus listing/security/issuer IDs, listing/delisting dates, security type, exchange, CUSIP, FIGI and CIK. Its documentation is unusually explicit about point-in-time identity.
3. **Norgate Platinum/Diamond — strongest index-based alternative/cross-check.** It documents a stable `assetid`, daily exact historical constituent time series for major indices, and listed/delisted coverage. It is not a substitute for the unknown custom F80 universe; it can support a separate index-defined universe.
4. **AlgoSeek ASID Lookup — useful lifecycle crosswalk, but not yet a proven two-clock PIT source.** It documents effective ticker ranges and persistent ASID across security lifecycle, but the inspected public schema does not establish record-known timestamps or archived correction vintages.

No source is approved for purchase. All pricing, license and historical coverage claims require confirmation before acquisition.

## 1. Databento Security Master

Public documentation describes:
- 860,000+ listed and delisted securities across international markets;
- listing-level records with persistent `listing_id`, `security_id` and `issuer_id`;
- `ts_record` and `ts_effective` as distinct UTC timestamps;
- security type, listing status, listing/delisting dates, exchange, CUSIP, FIGI, ISIN and CIK;
- weekly updates and point-in-time retrieval.

The dataset specification says history from 2005-01-01; the product page describes 18 years of PIT history. This is a material documentation discrepancy to resolve for the required period. The documentation also warns that some USNYSE class-share symbols may be normalized without delimiters (e.g. BRKB/HEIA); linkage should use ISIN, CUSIP or FIGI rather than relying on the symbol alone.

**Assessment:** best documented two-clock reference layer, but not a complete investable universe by itself. Need a sample audit of US venue coverage, record revisions, historical security types, delisted/relisted events, listing-level duplicates, class-share symbology and the exact 2016–present history. Price/volume and delisting-return data must be joined separately.

Official sources:
- https://databento.com/docs/schemas/security-master
- https://databento.com/docs/datasets/security-master
- https://databento.com/security-master

## 2. CRSP US Stock Database

CRSP documents:
- over 32,000 active and inactive US securities;
- daily and monthly market data and corporate actions;
- permanent PERMNO/PERMCO identifiers;
- survivor-bias-free history and total-return methodology;
- NYSE, NYSE American, NYSE Arca, Nasdaq and Cboe BZX coverage;
- data access through SAS, ASCII, R, Snowflake, MOVEit, WRDS and SASECRSP.

**Assessment:** preferred benchmark for price/volume, corporate-action and delisting-return validation if access is available. Need a sample to verify the relevant share codes/security types, inactive-security coverage, delisting return treatment, historical market-cap fields and licensing for this project. The public product page does not establish a complete two-clock archive of every historical security-master correction; pair with a PIT reference source if needed.

Official source:
- https://www.crsp.org/research/crsp-us-stock-databases-2025-layout/

## 3. Norgate Data

Current official documentation provides several useful details:
- Platinum/Diamond includes US delisted securities; the free trial is three weeks but limited to two years of history.
- The vendor says US listed/delisted coverage is essentially complete back to late 1992 for the included security types, while its delisted database is explicitly not claimed complete in all periods. It lists 25,222 delisted securities from 1950 through September 2022.
- A stable `assetid` survives ticker/name changes, exchange/OTC moves, delisting and other corporate actions.
- Historical index constituents are daily and show exact membership on each trading day, including intra-period changes.
- Russell 3000 membership starts July 1990; Russell 1000/2000 start July 1990; Nasdaq Composite starts January 1995; Nasdaq-100 starts January 1990.
- Historical index membership does not include index-change announcement dates. Use membership only from its effective date; never anticipate a future change from the effective-date series.
- OTC-only securities that never traded on a major exchange and some short-life/derivative instruments are excluded from the delisted database.

**Assessment:** strongest practical index-defined universe alternative. A Russell 3000 or Nasdaq Composite universe can be a separate research benchmark, with security type and assetid controls. It cannot recreate the custom 335 list, and the two-year trial is insufficient for a full 2016–2026 OOS study. Norgate's plugin/Windows delivery also requires an ingestion and reproducibility plan before it can feed GitHub Actions.

Official sources:
- https://norgatedata.com/data-package-faq.php
- https://norgatedata.com/data-content-tables.php
- https://norgatedata.com/ndu-faq.php

## 4. AlgoSeek ASID Lookup

The official marketplace description covers listed and delisted US equity securities from 2007, including common stocks, ETFs/ETNs, ADRs, preferreds and warrants. It documents ticker effective-date ranges, a SecId that remains stable across name/ticker changes, and a persistent ASID that links related SecIds across a security's economic life.

**Assessment:** useful as a lifecycle crosswalk and as a secondary check against Databento/CRSP. The public page does not prove that every historical correction has a record-known timestamp or archived vintage. Effective dates alone are not sufficient to reconstruct what the data provider knew at each historical point. Do not pass this source as a standalone two-clock PIT master without further evidence.

Official source:
- https://console.algoseek.com/marketplace/datasets/eq_secid_chains_lookup

## 5. Separate broad-universe research design

If the original F80 rule cannot be recovered, test a **new, independently named broad-universe model**. Do not replace the F80 list silently.

Two candidate universe definitions are worth preregistering after sample feasibility:

### A. Index-defined universe
- Russell 3000 / 3000E (or Nasdaq Composite as a separate sensitivity).
- Use daily effective membership and permanent security identifiers.
- Exclude non-equity instruments according to a fixed security-type rule.
- Do not use future index additions before their effective date.
- Apply price/liquidity eligibility using only information available before the formation/execution boundary.
- Retain delisted securities and terminal/delisting returns.

### B. Exchange-listed common-equity universe
- All eligible US primary listings on a fixed set of major exchanges, using PIT listing status and security type.
- Define common-equity/ADR/REIT/BDC/closed-end-fund treatment explicitly; do not mix ETFs/ETNs with operating equities by default.
- Use permanent listing/security IDs rather than ticker strings.
- Apply any price, market-cap or dollar-volume thresholds using lagged data only.
- Include inactive securities, corporate actions, mergers, bankruptcies and delisting outcomes.

These are alternatives, not an invitation to choose the universe that produces the best historical returns. Freeze the definition before evaluating model performance.

## 6. Minimum sample acceptance gate

Before any broad-universe return test, require:
1. 2016-01-01 through the last complete date of usable US listing history, with documented gaps and exchange coverage.
2. Listing/security/issuer identifiers and effective dates; record-known timestamps or a documented conservative availability rule for every mutable field.
3. Active and inactive securities, delisted/relisted names, corporate actions and terminal-return handling.
4. Historical security type and exchange classification, including share classes, ADRs, REITs, BDCs, funds/ETPs, warrants and OTC transitions.
5. No ticker-only joins; explicit treatment of multiple listings and multiple share classes.
6. Historical universe membership and lagged liquidity/price filters reconstructed without future information.
7. Cross-check a stratified sample of IPOs, ticker changes, mergers, delistings, relistings, share classes and symbol reuse across two independent sources.
8. Freeze the universe rule and a chronological development/validation/final-OOS protocol before running returns.

A PIT security master cannot recover omitted names if the original universe-selection rule is unknown. The new broad-universe line must therefore define its own universe from source data, not attempt to infer F80's historical membership from the current 335.

## 7. Decision and next step

- Keep F80 frozen and conditional on its present-day curated 335-name set.
- Finish the already-running Phase 69 Form 144 extension; do not start duplicate SEC work.
- Next, perform a non-purchase sample feasibility comparison of Databento's PIT reference layer and CRSP/Norgate's historical universe/return coverage, subject to explicit user authorization for any vendor contact or acquisition.
- If no accessible source passes the PIT and delisting gates, stop making broad OOS claims and retain fixed-335 results only as conditional diagnostics.
- No forward returns, feature selection, alpha tests, vendor contacts or purchases occurred in Phase 97.
