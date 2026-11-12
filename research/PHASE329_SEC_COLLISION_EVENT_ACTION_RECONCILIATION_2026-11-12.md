# Phase 329 — event-driven reconciliation of SEC Form 4 ticker mismatches

**Date:** 2026-11-12 UTC  
**Status:** COMPLETED — two explained transitions; one unresolved source conflict  
**Research class:** source-level identity adjudication; no return or alpha test.

## Executive decision

Phase 328 found three apparent mismatches between a Form 4 collision ticker candidate and the latest prior periodic XBRL filing. Reviewing intervening primary-source corporate events explains **two** of the three. The third remains quarantined because its original Form 4 XML is unavailable.

This is a concrete reason not to build an issuer/security crosswalk from periodic 10-K/10-Q snapshots alone. The crosswalk must be event-driven and effective-dated, with mergers, spin-offs, name changes and ticker changes inserted between periodic filings.

## 1. LFCR — stale periodic symbol resolved by a pre-event 8-K

- Phase 328's latest prior 10-Q for CIK 1005286 was filed 2022-10-07 and carried TradingSymbol LNDC.
- SEC Form 8-K accession 0001005286-23-000015 is dated/filed 2023-01-09. Its cover page identifies LIFECORE BIOMEDICAL, INC. and explicitly lists Common Stock / LFCR / Nasdaq.
- The collision/Form 4 date is 2023-01-11. The intervening 8-K is two calendar days earlier.
- The original Form 4, accession 0001628280-23-000899, was retrieved; its XML issuer symbol is LFCR and its acceptance time is 2023-01-11 16:21:39 ET.

**Disposition:** explained pre-event ticker transition. The 2022 periodic symbol LNDC was stale by January 2023; the 8-K and Form 4 agree on LFCR. The Form 4 transaction code is A (award/grant), not an open-market purchase.

Primary source: [SEC Form 8-K, January 9, 2023](https://www.sec.gov/Archives/edgar/data/1005286/000100528623000015/lndc-20230109.htm).

## 2. SAFE — merger and ticker transition between the periodic report and Form 4

- Phase 328's latest prior 10-K/A for iStar CIK 1095651 was filed 2023-03-30 and reported STAR and preferred-series symbols.
- Safehold's official investor-relations release is dated 2023-03-31. It says the merger closed that day, the combined company would operate as Safehold Inc., and common stock would trade as SAFE on the NYSE.
- The relevant Form 4, accession 0001415889-23-005926, was accepted 2023-04-04 at 14:20:07 ET. Its XML issuer symbol is SAFE.
- The related SEC 8-K was filed on April 4; it is not treated as a pre-Form-4 source in this audit. The March 31 company release is the independent date-level source preceding the Form 4.

**Disposition:** explained merger/name/ticker transition. The old STAR value in the March 30 periodic filing was superseded by the March 31 merger and new SAFE listing. The exact intraday publication time of the company release is not established, so this is date-level, not intraday PIT evidence.

Primary source: [Safehold official March 31, 2023 release](https://www.safeholdinc.com/press-releases/safehold-and-istar-close-merger-and-complete-spin-off-of-istars-legacy-assets-to-istar-stockholders/).

## 3. TSBK — likely bulk-symbol misattribution, original Form 4 still missing

- Phase 328's latest prior 10-Q for Riverview Bancorp CIK 1041368 was filed 2026-08-14 and reported RVSB.
- Riverview's SEC 8-K/A accession 0000939057-26-000233 was accepted 2026-09-08 at 11:03:52 ET; its cover page again reports RVSB. This is 17 days before the 2026-09-25 collision date.
- The other side of the collision, Timberland Bancorp CIK 1046050, filed a 10-Q on 2026-08-07 reporting TSBK. Five retrieved Timberland Form 4s on 2026-09-25 also have XML issuer symbol TSBK.
- The single Riverview Form 4 accession 0000939057-26-000239 is the one unresolved Phase 327 source-availability exception. Its bulk-index candidate is TSBK, but its original XML/header could not be recovered after twelve archive path/layout attempts.

**Disposition:** likely bulk-index symbol misattribution for the Riverview row, but not definitively adjudicated. Keep the Riverview accession quarantined. Do not overwrite the missing XML with the prior 8-K/A or a third-party record.

Primary sources: [Riverview SEC 8-K/A, September 8, 2026](https://www.sec.gov/Archives/edgar/data/1041368/000093905726000233/rvsb-20260904.htm); [Riverview 8-K/A filing detail](https://www.sec.gov/Archives/edgar/data/1041368/000093905726000233/0000939057-26-000233-index.htm).

## 4. Co-filer duplicates are not independent identity evidence

Phase 328 found three pairs whose two CIKs point to the same accession and byte-identical primary document:

| Pair | CIKs | Shared accession | Same document SHA-256 |
|---|---|---|---|
| DLR | 1297996 / 1494877 | 0001104659-26-054255 | Yes |
| LQI | 313749 / 314661 | 0000950134-05-019932 | Yes |
| PCG | 1004980 / 75488 | 0001004980-22-000133 | Yes |

For DLR and PCG, both CIK observations repeat the same filing's symbol facts. They are co-filer observations, not two independent confirmations of a listed security. The 39 unique document hashes among 42 retrieved documents reflect this duplication.

## 5. Research implications

1. A periodic-report-only crosswalk is stale across ticker changes and corporate actions. Search the intervening filing sequence, not just the latest 10-K/10-Q.
2. Treat 8-K/8-K/A cover pages, merger and spin-off releases, exchange listing/delisting notices, Form 25, registration statements and name-change filings as event evidence. Preserve each source's filing/acceptance/publication date separately.
3. Do not use an SEC 8-K filed after a Form 4 as though it were known before that Form 4. For SAFE, the dated company release is the pre-event date-level evidence; the later 8-K is corroborative only.
4. Model co-filers, parents, operating partnerships, plans and subsidiaries as relationships, not as separate listings by default.
5. Keep the missing Riverview Form 4 quarantined. The official 8-K/A and 10-Q make the bulk TSBK label suspect, but they do not replace the missing transaction document.
6. Transaction codes must be classified before any event study. The retrieved LFCR example is code A; the five retrieved Timberland Form 4s on the collision date use code F. Neither is an open-market purchase sample.

## Decision

- Two mismatches explained by pre-event corporate actions.
- One likely metadata error remains unresolved due missing primary Form 4.
- Three co-filer duplicate accessions identified.
- No crosswalk admission, alpha test, return test, bootstrap/LOO, chronological OOS or holdout use.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; production, universe, capital and parameters unchanged.
- No vendor contacted, no data purchased, no email sent and no raw SEC bytes uploaded.

Structured records: [event-action reconciliation CSV](phase329_event_action_reconciliation.csv) · [co-filer duplicate accession CSV](phase329_cofiler_duplicate_accessions.csv).
