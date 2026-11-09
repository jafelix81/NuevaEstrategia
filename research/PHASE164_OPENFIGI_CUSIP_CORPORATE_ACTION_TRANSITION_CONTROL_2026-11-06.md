# Phase 164 — OpenFIGI cross-CUSIP link: effective-dated corporate-action control

**Date:** 2026-11-06  
**Status:** COMPLETED — one manually verified corporate-action bridge; not a universe-wide security master  
**Input:** Phase 149 OpenFIGI audit, 553 CUSIPs from the targeted 13D/G sample.

## Executive result

Phase 149 returned one cross-CUSIP shared-share-class link in the 553-CUSIP sample:

- Old CUSIP: **349915108** — Fortuna Silver Mines Inc.
- New CUSIP: **349942102** — Fortuna Mining Corp.
- Current OpenFIGI shareClassFIGI for both: **BBG001S982M0**.

This is a real corporate name/CUSIP transition, not evidence that two unrelated securities should be merged. The issuer announced its legal name change effective 20 June 2024; the TSX notice reported the new common-share CUSIP 349942102 effective at the open on 27 June 2024, while the TSX ticker FVI remained unchanged. The issuer announcement also says the NYSE ticker FSM remained unchanged. The exact NYSE CUSIP-effective timestamp is not independently established in this source set.

## Effective dates must remain separate

| Attribute | Effective date | Evidence | PIT treatment |
|---|---|---|---|
| Legal issuer name | 2024-06-20 | Issuer announcement and SEC certificate | New legal name from 20 June |
| TSX common-share CUSIP | 2024-06-27 at open | TSX notice republished 25 June | Old CUSIP through 26 June; new CUSIP from 27 June |
| TSX ticker | FVI, unchanged | Issuer announcement / TSX notice | Do not create a ticker-change event |
| NYSE ticker | FSM, unchanged | Issuer announcement | Ticker continuity only; NYSE CUSIP-effective date not separately adjudicated |

The SEC-filed certificate records the legal name change as effective on 20 June 2024 at 11:46 a.m. Pacific time. The issuer's June 20 announcement states the legal name change was effective that day and that FVI (TSX) and FSM (NYSE) would remain the common-share ticker symbols. The TSX notice states the new common-share CUSIP 349942102 would be effective at the open on June 27.

## What OpenFIGI contributes — and what it does not

The completed Phase 149 audit returned:
- 553 input CUSIPs.
- 438 primary mappings to at least one FIGI result; 430 mapped to one share class.
- 115 primary no-matches.
- 115 fallback attempts; six unique identities recovered, 109 remained no-match.
- One cross-CUSIP shareClassFIGI link containing the two Fortuna CUSIPs.
- Zero API errors in primary and fallback requests.

For both Fortuna CUSIPs, the current API response assigns shareClassFIGI BBG001S982M0. The old CUSIP maps to the current name/ticker aliases Fortuna Silver Mines / FVI/FVIG; the new CUSIP maps to Fortuna Mining and a wider set of venue/currency ticker aliases including FVI and FSM.

OpenFIGI provides no effective-from/effective-to dates, no historical listing-status dates and no issuer CIK in the response. Its current name/ticker fields must not be backdated. The corporate-action documents supply the date for this one pair; they do not solve the remaining 115 no-matches or establish a complete historical security master.

## Conservative manual bridge

For the confirmed TSX listing only:

- 349915108 is valid through 2024-06-26.
- 349942102 is valid from 2024-06-27.
- Both map to the same current shareClassFIGI BBG001S982M0.
- Issuer CIK: 0001341335.
- Legal issuer name changes from Fortuna Silver Mines Inc. to Fortuna Mining Corp. on 2024-06-20.
- TSX ticker remains FVI.
- NYSE ticker remains FSM, but this phase does not independently assert the exact NYSE identifier-effective date.

This is a manually sourced corporate-action bridge, not a rule that every same-shareClassFIGI pair is a valid historical CUSIP transition. Require independent issuer/exchange evidence for each pair.

## Research decision

**PASS for this single effective-dated identity bridge.** Preserve it as a security-master test fixture. Do not use OpenFIGI's current ticker list as a historical ticker series. Do not generalize the pair to other CUSIPs or venues without source-specific dates.

This improves historical identity handling but creates no Smart Money feature and no alpha evidence. No returns, feature panel, bootstrap/LOO, OOS test or final holdout were used. No vendor was contacted or purchased. No production or F80 change.

## Official and contemporaneous references

- SEC-filed certificate of name change, accession 0001104659-24-073576: https://www.sec.gov/Archives/edgar/data/1341335/000110465924073576/tm2417718d1_ex99-3.htm
- Fortuna issuer announcement, 20 June 2024: https://fortunamining.com/news/fortuna-reports-results-of-annual-and-special-meeting/
- TSX name/CUSIP notice, republished 25 June 2024: https://www.stockwatch.com/News/Item/Z-C!FVI-3570525/C/FVI
- BMV current issuer profile / current ISIN: https://www.bmv.com.mx/es/emisoras/perfil/FVI-7476
- Phase 149 OpenFIGI audit run 42274313824, artifact 13531523894: https://github.com/jafelix81/NuevaEstrategia/actions/runs/42274313824/artifacts/13531523894

