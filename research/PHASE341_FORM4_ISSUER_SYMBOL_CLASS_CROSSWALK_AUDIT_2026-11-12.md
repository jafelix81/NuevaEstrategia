# Phase 341 — Form 4 issuer-symbol and security-class crosswalk audit

**Status:** completed; hosted reproducibility PASS.  
**Question:** Can the issuer-level `issuerTradingSymbol` in Form 4 be reconciled, without fuzzy ticker matching, to a unique same-CIK SEC XBRL `TradingSymbol` + `Security12bTitle` + `SecurityExchangeName` context from Phase 339?  
**Scope:** the same 72-accession stratified sample and 122 transaction rows audited in Phase 340. No new SEC requests.

## Immutable sources and hosted execution

- Phase 340 source artifact: [13959807159](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43250767148/artifacts/13959807159), ZIP SHA-256 `246fc82c5fa6c9fdb6071a58ad5675e7892bbc389fcb5798e3cc2e27f55c78f5`.
- Phase 339 source artifact: [13959007527](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43249238927/artifacts/13959007527), ZIP SHA-256 `186bd582c8cd0ffff73cda16c7331e5a2bd34e413b6aba3715b5fac430a0a66f`.
- Latest Phase 341 run: [43262590091](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43262590091), SUCCESS.
- Phase 341 output artifact: [13963219558](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43262590091/artifacts/13963219558), ZIP SHA-256 `b15232741016bf39445acd3dde5c010c3aeef013cb59e6997a1ba9a9763e8130`.
- Both input ZIPs and their primary JSON files were SHA-256 verified in the hosted job. All 72 raw Form 4/Form 4/A submissions were re-hashed and reconciled to their Phase 340 accession records. All 12 offline regression tests passed.

## Method

1. Parse the raw Form 4 XML `issuerTradingSymbol`, not a guessed or current ticker.
2. Remove an exchange prefix only when it belongs to a fixed recognized-exchange allowlist. Balanced wrappers may be removed; malformed, multi-symbol, placeholder and unknown-prefix values are quarantined. No fuzzy or punctuation-repair ticker matching.
3. Require exact same-CIK match to exactly one Phase 339 XBRL symbol context with one unique `Security12bTitle`. Preserve exchange values as evidence.
4. Compare the Form 4 transaction title (or derivative `underlyingSecurityTitle`, separately) to the XBRL title. Common stock, ordinary shares, beneficial-interest shares, preferred, debt, depositary shares and warrants are not collapsed. Explicit class/series tokens must match. Debt, warrants, options and other non-common classes require exact title equality.
5. Keep two distinct chronology gates:
   - **Transaction-date identity:** selected prior-periodic anchor strictly before the underlying transaction date.
   - **Event-time identity corroboration:** fresh prior-periodic anchor (age 1–365 days) strictly before the Form 4 filing date. This is relevant to an event study measured after public disclosure, but it is not proof of the security's identity at the earlier transaction date.
6. Reconcile transaction code, direct/indirect ownership, ownership nature, footnotes, reporting-owner count and Rule 10b5-1 checkbox from the original XML.

## Results

### Issuer-symbol crosswalk

| Measure | Result |
|---|---:|
| Form 4 accessions | 72 |
| Raw submissions hash-verified | 72 |
| Phase 339 same-context symbol facts | 61 |
| Single-token Form 4 issuer symbols | 57 |
| Unique exact same-CIK symbol-context matches | 30/72 (41.67%) |
| Design-weighted unique crosswalk coverage | 47.77% |
| No unique crosswalk | 42/72 |

The 42 without a unique match include 27 single-token values not present in the sampled Phase 339 XBRL contexts, plus multi-symbol, malformed, placeholder, missing or unknown-prefix values. They are unresolved, not presumed invalid.

Coverage is highly period-dependent:

| Form 4 filing year | Sampled accessions | Unique symbol crosswalk | Event-time identity candidates |
|---|---:|---:|---:|
| 2006 | 12 | 0 | 0 |
| 2012 | 12 | 0 | 0 |
| 2023 | 24 | 16 | 15 |
| 2025 | 12 | 7 | 6 |
| 2026 | 12 | 7 | 5 |

The zero results in 2006 and 2012 mean the Phase 339 XBRL `TradingSymbol` evidence does not provide coverage for those sampled periods. They do not mean Form 4 itself lacks a symbol.

### Transaction-date versus event-time mapping

| Gate | Equity transaction rows | Accessions | Derivative-underlying rows |
|---|---:|---:|---:|
| Anchor strictly before transaction date | 38 | 23 | 13 |
| Fresh anchor strictly before Form 4 filing date | 41 | 26 | 16 |

The event-time gate adds three rows whose periodic anchor postdates the transaction but predates the Form 4 filing: MNTX (code A), ARKO (code M), and OMEX (code A). These are not transaction-date identity candidates. This distinction prevents us from calling a disclosure-time crosswalk proof of the ticker/class on the earlier transaction date.

Of the 41 event-time equity rows, 5 are exact title matches and 36 use the controlled same-instrument-class rule. Instrument classes remain separated: 36 common stock, 2 beneficial-interest shares, 2 depositary shares and 1 ordinary-share row. These are provisional crosswalk candidates, not an admitted historical security master.

For these 41 rows, the median transaction-to-filing lag is 4 calendar days and the maximum is 7. This describes the selected sample only.

### Purchase-screen disposition

The 122-row sample contains 27 code-P rows across 16 accessions: 15 direct and 12 indirect.

Only four code-P rows across two accessions pass the provisional event-time identity crosswalk. All four are indirect:
- CMRX: two rows held through the Michael A. Sherman Trust.
- MNSB: two rows held through a 401(k) plan.

No direct code-P row obtains a provisional event-time identity crosswalk. All 15 direct code-P rows remain unmapped. Code P itself means open-market **or private** purchase and cannot establish a discretionary open-market buy. Therefore this sample yields zero confirmed discretionary open-market purchase candidates, but it does **not** establish that no such purchases exist in the wider Form 4 population.

## Decision and next gate

- Retain this crosswalk as a **candidate-only identity corroboration method**.
- Do not admit a security master, transaction-level security mapping, strict PIT identity or event study from this sample.
- Do not treat the Form 4 `issuerTradingSymbol` as an ex-ante feature relative to the transaction date. It is in the later disclosure and is available at event time.
- For a disclosure-based event study, the next gate is to test the Phase 271 high-precision Form 4 purchase cohort at event time, map each filing to a contemporaneous traded class, and audit effective-dated listing/corporate-action continuity plus survivorship-aware price coverage. Use a conservative first full exchange session after the filing date until exact first-public timing is independently established.
- If the public historical identity/price coverage remains inadequate, keep the insider line at feasibility status and redirect effort to sources with stronger historical identifiers and timestamps.

## Controls

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No event study, alpha or return test, chronological OOS, bootstrap/LOO or holdout use. No security master or production admission; no universe, capital or parameter changes; no data purchase or vendor contact.
