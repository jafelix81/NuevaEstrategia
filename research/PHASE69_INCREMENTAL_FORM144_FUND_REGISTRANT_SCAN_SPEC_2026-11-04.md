# Phase 69 — Incremental Form 144 scan for newly mapped fund registrants

**Date:** 2026-11-04  
**Status:** Preregistered incremental identity scan; waits for Phase 67 artifact before reconciliation.

## 1. Reason

Phase 68 corrected the SEC mutual-fund map parser and resolved 27 formerly unmapped universe tickers. These 27 symbols map to ten additional registrant CIKs beyond the 309-CIK set used by Phase 67:
- 0001579982 — ARKF, ARKG, ARKK, ARKQ, ARKW
- 0001174610 — BITO
- 0001100663 — IEFA, IWM, SOXX
- 0001540305 — JETS
- 0001064642 — KRE, XBI
- 0001137360 — OIH, SMH
- 0000923202 — VEA
- 0000734383 — VNQ
- 0000857489 — VWO
- 0001064641 — XLB, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY

The full Phase 67 run uses the pre-Phase-68 309-CIK set. Its results must not be described as covering the corrected 319-CIK set.

## 2. Incremental scan

After Phase 67 completes:
1. Read the same 14 master indexes (2023Q2–2026Q3).
2. Select every Form 144/144-A accession whose two-CIK master-index pair contains any of the ten new fund registrant CIKs.
3. Fetch primary XML and reconcile both distinct XML issuer/filer CIKs to the pair and form.
4. Classify the new fund CIK as issuer, filer-only, both-candidate ambiguous, or unresolved.
5. Preserve all accessions where a new CIK co-occurs with an old candidate CIK; these may have been misclassified by Phase 67's narrower candidate set and must be reconciled by accession.
6. Compare the incremental accession set with Phase 67's complete candidate output; deduplicate by accession and retain the more complete expanded-CIK classification.
7. Preserve proposed-sale, acquisition-lot and prior-realized-sale groups separately.

## 3. Security-level fund attribution

The SEC mutual-fund file provides registrant CIK, seriesId, classId and symbol. A trust/registrant CIK can cover several ETF tickers. A Form 144 XML issuerCik match alone therefore establishes only registrant-level identity.

Do not assign an event to every ticker sharing a CIK. Retain the candidate ticker/series/class set and compare the XML security-class description, issuer name and filing details against official series/class metadata. If no unique match is supported, label the event registrant-level / security-series unresolved and exclude it from ticker-level tests.

## 4. Gates and limitations

- Every selected accession has explicit issuer/filer role classification or an unresolved reason.
- Both XML CIKs are distinct and reconcile to the master-index pair.
- XML form matches the index.
- Zero filer-only rows enter the issuer event panel.
- Accession-level reconciliation with Phase 67 has no duplicates.
- Current series/class map is not historical PIT membership. Ticker reuse, fund liquidation, series changes and registrant reorganizations require effective-date evidence.
- No accepted-time or forward-return test is performed in this phase.

## 5. Decision

Phase 69 only expands current fund-registrant candidate coverage and resolves accession identity. It does not establish historical F80 membership or security-level ETF attribution. Do not calculate forward returns until those PIT gates and the amendment/seller/security lineage gate pass.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
