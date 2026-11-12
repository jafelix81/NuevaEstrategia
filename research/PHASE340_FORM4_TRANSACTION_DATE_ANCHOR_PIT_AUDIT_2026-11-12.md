# Phase 340 — Form 4 transaction-date identity-anchor PIT audit

**Status:** completed; hosted retrieval and reconciliation PASS.  
**Source population:** exact 72 issuer-quarter Form 4 / Form 4/A accessions selected in Phase 338.  
**Identity source:** 42 byte-verified prior-periodic XBRL instances from Phase 339.

## Question and method

Phase 338 selected a prior periodic filing strictly before each Form 4 filing date. That does not prove the identity anchor predates the underlying transaction date. Phase 340 retrieved the exact 72 original submissions, verified accession/form/filing date/XML issuer CIK, hashed every source, parsed non-derivative and derivative transaction rows, and compared every transaction date with the Phase 338 periodic anchor.

Security-title matching was intentionally conservative: normalized exact Form 4 `securityTitle` to Phase 339 `Security12bTitle` within the same issuer CIK. Derivative `underlyingSecurityTitle` was assessed separately. No fuzzy mapping was admitted.

## Hosted execution and immutable evidence

- Latest completed run: [43250767148](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43250767148), PASS.
- Earlier same-branch run: [43250702857](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43250702857), PASS. The later run is the final artifact used below.
- Final artifact: [13959807159](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43250767148/artifacts/13959807159).
- Artifact ZIP SHA-256: `246fc82c5fa6c9fdb6071a58ad5675e7892bbc389fcb5798e3cc2e27f55c78f5`.
- 72/72 raw submissions retrieved; 71 Form 4 and 1 Form 4/A; zero retrieval failures. Accession, form, filed date and XML issuer identity reconciled in all 72. Every raw source has a SHA-256 and the artifact preserves the original submission text.
- Eight offline regression tests passed in the hosted job.

## Results

### Transaction-date chronology

| Gate | Result |
|---|---:|
| Total transaction rows | 122 |
| Anchor strictly before transaction | 95 |
| Anchor after transaction (look-ahead) | 9 |
| No usable prior anchor | 18 |
| Same-day anchor | 0 |
| Missing transaction date | 0 |
| Accessions whose anchor predates every transaction | 56/72 |
| Accessions with at least one look-ahead transaction | 6/72 |
| Accessions without a usable prior anchor | 8/72 |
| Accessions with no transaction rows | 2/72 |

The 18 rows classified as lacking an anchor have transaction dates; the missing item is the prior-periodic identity anchor, not the transaction date. The 95/122 chronology rate is descriptive of this stratified sample, not a population estimate.

### Security identity

- Exact normalized `securityTitle` match to one unique symbol: 5/122 rows (4.10%).
- Exact title plus strictly prior anchor: 4/122 rows (3.28%).
- Ambiguous exact title matches: zero.
- 117 rows did not obtain an exact title-to-symbol match. This is an unresolved mapping, not proof that the securities are different.

The four time-valid rows occur in three accessions:
- SVC: one 7,000-share code-A award/grant.
- MNSB: two code-P acquisitions (241 and 153 shares), both indirect through a 401(k) plan; the reporting owner is a director and CFO, and `aff10b5One=0`.
- SCS: one 2,287-share code-A award/grant.

The fifth exact title match is OMEX, but its selected periodic anchor is after the 2026-06-30 transaction and is therefore look-ahead.

Across all 122 rows, 27 use transaction code P. Only the two MNSB rows among them received an exact title match in this audit, and both are indirect 401(k)-plan transactions. The remaining P rows are not identity-mapped here; code P itself means open-market **or private** purchase and is not sufficient to establish a discretionary open-market buy. This sample therefore contains **zero confirmed discretionary open-market purchase candidates** under the current strict identity and ownership evidence. This is a sample-level disposition, not a claim that the wider Form 4 population contains none.

## Decision

**Do not admit this 72-accession sample to an event study.** The strict identity mapping rate is too low, and the four time-valid identity rows do not yield a confirmed discretionary purchase event. The Phase 271 high-precision purchase screen remains a separate candidate-generation method; it is not validated by this result.

Next research gate: test a separate, fail-closed crosswalk between Form 4 `issuerTradingSymbol` and the Phase 339 same-issuer XBRL `TradingSymbol` facts, then require an instrument-class-compatible transaction title, unique symbol context, and transaction-date chronology. The issuer-level symbol must not be mistaken for transaction-specific share-class identity. Any extension must preserve ambiguous/multi-symbol cases and must not use fuzzy ticker normalization.

## Interpretation limits

A periodic filing date before a transaction date is a necessary chronology gate, not proof that the listing/class remained effective on that date. EDGAR acceptance datetime is captured but is not treated as exact first-public receipt. Exact-title mismatch is not proof of different securities. Phase 340 is a data-feasibility audit, not an alpha/event-return test.

## Controls

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No transaction-level security mapping, security master, event study, alpha/return/OOS, bootstrap/LOO or holdout admission. No production, universe, capital or parameter changes; no data purchase or vendor contact.
