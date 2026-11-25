# Smart Money Research — state addendum, Phase 623

**Cutoff:** 2026-11-25 19:32 UTC  
**Implementation branch:** `phase620-sec-form4-entity-aware-feed-dedup`  
**Parent PR:** [#237](https://github.com/jafelix81/NuevaEstrategia/pull/237)

## New integrity control

Phase 623 adds a transaction-linked Form 4 footnote sidecar. The legacy transaction ledger schema and transaction fingerprint remain unchanged. The sidecar preserves accession, transaction detail key, XML field/reference path, footnote ID, text, text hash, source hashes, and conservative availability metadata. It is append-only and schedule-only.

The bounded backfill targets previously parsed transaction accessions lacking a sidecar completion marker. New transaction-detail parses write their footnote sidecar from the same XML fetch. No extra fetch is required for newly parsed documents.

## Validation status

- Offline regression: pending GitHub Actions.
- Live capture: must remain skipped on pull-request events.
- Historical sidecar backfill: not executed in this PR validation.
- Existing transaction rows: not rewritten.
- Signal eligibility: zero.

## Source and strategy disposition

The UPST purchase cluster remains one issuer-level descriptive observation. Transaction-specific footnotes improve classification but do not establish open-market venue, discretion, historical F80 membership or exact public availability. No event return or alpha test is authorized.

FINRA Reg SHO remains quarantined; CFTC TFF remains awaiting additional vintages; options remain subject to the existing zero-budget constraint. Continue independent data-feasibility audits for SEC 13F/13D/G, options and consolidated short interest rather than treating any one source as the definition of smart money.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No capital, exposure, universe, cost, parameter, holdout or production changes. No paid data, quote request or vendor contact; options-data budget remains USD 0.
