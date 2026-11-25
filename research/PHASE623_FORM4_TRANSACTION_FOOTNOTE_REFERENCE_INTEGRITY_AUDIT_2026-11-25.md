# Phase 623 — Form 4 transaction-to-footnote reference integrity

**Cutoff:** 2026-11-25 19:32 UTC  
**Implementation branch:** `phase620-sec-form4-entity-aware-feed-dedup`  
**Parent PR:** [#237](https://github.com/jafelix81/NuevaEstrategia/pull/237)  
**Mainline baseline:** `074e3596b6982308889ed33e614ec4e169005ee5`

## Finding

The Phase 510 parser preserves a sorted list of footnote IDs and a separately sorted list of SHA-256 hashes. Sorting each collection independently destroys the one-to-one correspondence between a transaction's footnote ID and its source text hash. The current row-level keyword flags also discard the XML field that carried each reference.

This is a provenance defect, not evidence that the underlying SEC transaction rows are wrong. The UPST Form 4 review identified:
- Gu Paul: F1 is the weighted-average price range; F2 describes the Gu Qiao Family Trust.
- Dave Girouard: F3 is the weighted-average price range; F4 describes the revocable trust; F5 describes a separate no-consideration trust transfer.

The existing normalized ledger cannot reliably reconstruct those ID-to-hash and field-to-reference relationships from the two sorted JSON arrays alone.

## Implementation

The Phase 623 change adds an append-only `footnote_references.csv` sidecar without changing the legacy `transaction_details.csv` schema or parser fingerprint.

Each reference row stores:
- accession and exact transaction `detail_row_key`;
- table type and transaction row index;
- footnote ID and its XML field path/reference path;
- normalized footnote text and its SHA-256 hash;
- submission/XML hashes, XML source, acceptance timestamp and conservative first-seen upper bound;
- parser version and explicit non-eligibility flags.

An accession marker records successful parsing even when no footnote references exist. A schedule-only backfill can therefore enrich previously parsed transactions without re-appending or rewriting their transaction-detail rows. New transaction-detail backfills write the sidecar from the same fetched XML, avoiding an extra fetch for new documents.

The scheduled workflow runs the bounded sidecar backfill after the transaction-detail backfill, then persists it with the existing append-only data directory. Manual mode performs no fetch or persistence.

## Regression coverage

New tests cover:
- F3/F4/F5 reference ordering and XML field paths;
- exact ID-to-text-hash mapping;
- linkage to the existing transaction detail key;
- append idempotency and accession completion markers;
- sidecar backfill of already-parsed accessions without changing the transaction ledger;
- manual-mode no-fetch behavior and schema-mismatch fail-closed behavior.

## Validation result

- Final PR check [Run 45687169039](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45687169039) passed **75/75 offline regression tests**.
- The live-capture job was skipped as designed for pull-request validation; no SEC feed or filing was fetched by CI.
- The first attempt [Run 45687060727](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45687060727) failed one test-only XML field-path assertion (`transactionPricePerShare` spelling); the assertion was corrected in commit `907bef37`, and the full suite then passed.

## Research disposition

- Footnote provenance: **implementation added; 75/75 offline tests passed**.
- Existing UPST/Form 144 crosswalk matches: descriptive only.
- Historical F80 membership, exact public availability and transaction venue remain unresolved.
- No transaction is promoted to research-observation or signal eligibility.
- No event study, forward-return, alpha, OOS, bootstrap or LOO test is run by this parser correction.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No capital, exposure, universe, cost, parameter or production changes. No options data purchase or vendor contact; the authorized options-data budget remains USD 0.
