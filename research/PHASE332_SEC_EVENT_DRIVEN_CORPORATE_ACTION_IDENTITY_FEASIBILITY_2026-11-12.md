# Phase 332 — SEC event-driven corporate-action identity feasibility

**Date:** 2026-11-12 UTC  
**Status:** completed; source remains supplementary and not admitted as a security master.  
**Run:** [43222287571](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43222287571)  
**Artifact:** [13945213682](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43222287571/artifacts/13945213682) — SHA-256 `c093a63c5c4a12799eb37661fff87f1786768a382d4af4e977e7c97a2d597025`  
**Review:** [PR #21](https://github.com/jafelix81/NuevaEstrategia/pull/21), draft, based on Phase 328.

## Question

Can SEC corporate-action/listing-related filings provide additional, reproducible issuer-symbol evidence between a supported periodic filing and a Form 4 collision date?

## Method

- Both issuer CIK sides of all 28 purposive Phase 325 same-day ticker-collision pairs: 56 issuer-date observations.
- Retrieve each CIK's SEC Submissions JSON and select the latest supported periodic filing strictly before the collision date.
- Search exact event forms (8-K/8-K/A, 6-K/6-K/A, Form 25, 15-12B/G, 10-12B/G, 8-A, S-4/F-4, 425, merger/offer forms, S-1/S-3 and amendments) strictly after that periodic anchor and strictly before the Form 4 collision date.
- Same-day filings are excluded because intraday acceptance/publication ordering was not independently established.
- Retrieve primary XBRL instance/inline HTML and retain document hashes. Only explicit TradingSymbol facts count; issuer names, exchange names, security titles and bulk-index labels are not substituted.
- Maximum 25 event filings per observation; truncation is explicit.

## Results

| Measure | Result |
|---|---:|
| CIK submissions responses | 56/56 |
| Supported prior-periodic anchors | 44/56 |
| Event-filing candidates | 182 |
| Event filings retrieved | 178 |
| Retrieved documents with target TradingSymbol facts | 35 rows / 26 unique accessions |
| Latest pre-event symbol evidence | 11 observations |
| Latest evidence matches to candidate | 10 observations |
| Latest evidence mismatches | 1 observation |

The 10 match observations are not 10 independent documents: Digital Realty (DLR) and PG&E (PCG) each have one shared accession appearing under two co-filer CIKs. After deduplicating those shared accessions, the 11 latest-evidence observations represent **8 unique matching documents and 1 unique mismatch document**.

### Anchor-freshness adjudication

The raw pilot used the latest periodic filing even when it was unusually old. A post-run audit of the 44 anchors found:

- **38 fresh anchors:** age no more than 365 calendar days.
- **6 stale anchors:** older than 365 days.
- **12 observations:** no supported periodic anchor.

All 11 latest-symbol-evidence observations are within the 38 fresh-anchor observations. All 35 fact-bearing document rows are also within fresh windows. The stale windows contributed no target-symbol facts; one stale CSAN window had 29 candidates and was truncated at 25. Two 1997 OKE 8-K entries had no primary document or XBRL instance and therefore no document hash.

For coverage interpretation, the stale 6 and the 12 unanchored observations are excluded. Among the 38 fresh anchored observations, 11 (28.9%) had a latest explicit pre-event TradingSymbol fact; 10 matched and 1 mismatched. The 365-day rule is a conservative annual-reporting freshness screen, not a claim that older filings are false. Future runs should encode this screen directly rather than relying on post-hoc adjudication.

## Evidence by issuer

- DLR, FTAI, LFCR, NWLI, NWN, PCG, SAFE and STR have latest pre-event symbol evidence matching the candidate.
- DLR and PCG evidence is co-filed across two CIKs and is not independent confirmation.
- FTAI, DLR, PCG and STR report multiple symbols in one filing; Phase 332 alone cannot safely map each symbol to a class.
- **TSBK/Riverview:** four pre-event filings, including the 2026-09-08 8-K/A, report `RVSB`, not the bulk candidate `TSBK`. This strengthens the suspected bulk-index misattribution. The original Form 4 XML remains unavailable, so the underlying Form 4 event itself is still quarantined.

## Interpretation

SEC event filings are a useful **supplementary, dated issuer-symbol evidence source**, but not a complete historical security master. Only 11/38 fresh anchored observations had a latest explicit symbol fact. The result is purposive and conditional on the 28 collision pairs; it is not universe prevalence.

Phase 333 follows up on the nine unique latest-evidence documents to test whether each TradingSymbol fact itself carries a share-class dimension. No alpha or return test is justified by Phase 332.

## Controls

- Strict daily chronology: event filing date is strictly before Form 4 collision date; same-day evidence excluded.
- No security master, share-class crosswalk, or universe coverage admitted by Phase 332.
- No alpha/return/OOS/bootstrap/LOO test; no holdout use.
- F80_TOP20_PARTIAL50_BASELINE_C20 frozen; production, universe, capital and parameters unchanged.
- No vendor contact, purchase, account creation or email.

