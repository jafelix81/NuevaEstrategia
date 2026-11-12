# Phase 343 — SEC Form 4 candidate-specific event-time identity audit

**Date:** 2026-11-12 UTC  
**Branch:** \`phase343-form4-candidate-specific-event-time-identity\`  
**Final run:** [43286198150](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43286198150)  
**Artifact:** [13975421281](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43286198150/artifacts/13975421281)  
**Draft PR:** [#32](https://github.com/jafelix81/NuevaEstrategia/pull/32)

## Scope and immutable inputs

Phase 343 re-audited the high-precision 2026Q3 Form 4 purchase cohort from Phase 342 against the original SEC submissions and the latest supported periodic filing strictly before each Form 4 filing date.

- 85 candidate transaction rows
- 59 original Form 4/Form 4-A accessions
- 31 issuer CIKs
- 48 issuer-CIK × Form 4 filing-date event units
- Source archive SHA-256: \`a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3\`
- 59/59 original Form 4 submissions retrieved and hashed
- 31/31 issuer submissions JSON documents available
- 32 unique prior periodic filings retrieved and hashed

This is a deterministic, high-precision candidate cohort, not a random or representative sample. Do not use it to estimate the population prevalence of insider purchases.

## Reconciliation defects found and corrected

Two join defects initially suppressed valid matches:

1. **Compact candidate schema omitted screened fields.** Phase 342's candidate rows intentionally omit transaction code, direct/indirect ownership and acquired/disposed fields because candidates are appended only after the upstream screen requires \`P\`, \`D\` and \`A\`. Phase 343 now restores that explicit cohort contract and fails closed if an input supplies conflicting values.
2. **SEC bulk price precision differs from original XML precision.** \`TRANS_PRICEPERSHARE\` in the quarterly bulk TSV is serialized to cents, while original Form 4 XML can retain four or more decimals. Both sides are now normalized to the bulk field's two-decimal precision using \`ROUND_HALF_UP\`; shares, transaction date, security title, transaction code, ownership and acquired/disposed status remain exact. This is source-precision reconciliation, not a fuzzy price tolerance.

The first run's 0/85 and the intermediate run's 43/85 matches were therefore parser/join defects, not evidence that the underlying filings were missing. The final run corrected both and passed 16/16 offline regressions.

## Final results

| Gate | Result |
|---|---:|
| Original Form 4 accessions retrieved and hashed | 59/59 |
| Bulk symbol reconciled to original Form 4 | 59/59 |
| Candidate transaction rows uniquely matched at SEC bulk price precision | 85/85 |
| Original XML/footnote purchase screen revalidated | 85/85 |
| Issuer submissions JSON available | 31/31 |
| Event units with a prior periodic anchor | 48/48 |
| Prior periodic anchors no more than 365 days old | 48/48 |
| Unique periodic anchors retrieved and hashed | 32 |
| Anchors with same-context XBRL symbol/title/exchange triples | 28 |
| Candidate rows with a unique compatible security-class context | 72/85 (84.71%) |
| Complete issuer-date event units | 41/48 (85.42%) |
| Complete Form 4 accessions | 48/59 (81.36%) |

For all 72 mapped rows, the prior periodic anchor predates both the transaction date and the Form 4 filing date. Anchor age was 3–116 calendar days before the transaction and 5–118 days before Form 4 filing. No same-day or later anchor was admitted.

Thirteen candidate rows remain quarantined:

- 9 lack a supported same-context \`TradingSymbol\` + \`Security12bTitle\` + \`SecurityExchangeName\` triple.
- 4 contain a symbol but do not have a compatible security-class title in the same context.

The seven incomplete event units remain excluded as a whole; no partial issuer-date event is promoted.

## Interpretation and limitations

This closes a meaningful **data-identity feasibility** gate for the 2026Q3 cohort. It does not prove that the mapped ticker/class remained unchanged between the periodic anchor and transaction; an effective-dated corporate-action/listing security master is still required for definitive historical continuity.

The EDGAR acceptance timestamp is captured for event timing, but Phase 343 does not independently establish first public receipt. Any future event study must conservatively use the next full XNYS session after the verified knowledge timestamp, not the transaction date and not a same-session assumption.

No returns, alpha, bootstrap, LOO or chronological OOS tests were run. The 2026Q3 sample alone is too small and too recent to establish predictive value. No holdout was used.

## Cross-source research queue

| Source | Feasibility status | Next decision |
|---|---|---|
| SEC Form 4 | 2026Q3 event-time identity coverage is 84.71% of rows and 85.42% of issuer-date units | Expand the same audit to the other sampled quarters; then require an effective-dated security master and survivorship-aware price panel |
| SEC FTD | Public history begins in 2004; prior audits found 75.5% coverage in 2018 and 94.3% in 2026, with 237/335 names covered in both | Candidate public short-pressure source, but CUSIP-to-security identity and historical universe membership remain unresolved |
| SEC Form 144 | Large 14-quarter event sample; proposed sale notices are not executed sales | Keep as a distinct supply/overhang hypothesis, not proof of insider selling or informed flow |
| SEC N-PORT | Phase 344 raw five-filing sample spans 2020–2025 and contains 327 direct short-equity rows | Fund identity and acceptance metadata now reconcile; broad prevalence is sparse (Phase 316 found direct-short rows in only 2/280 sampled filings), and CUSIP/ISIN-to-security identity remains unresolved |
| SEC 13F | Raw filings extend earlier than structured datasets; quarterly disclosure is delayed and prior worst-quarter CUSIP mapping was 54.8% | Park until deterministic historical security identity materially improves worst-quarter coverage |
| SEC 13D/G | Broad filing retrieval and event-date coverage are strong, but amendments and subject-security/event semantics remain material | Continue only with deterministic subject-issuer/security lineage; no alpha admission |
| FINRA short flow × short interest | Prior standalone OOS test failed; short-volume is not short-interest and combined universe coverage is incomplete | Do not retune or promote the tested feature |
| FINRA ATS/off-exchange | Several aggregates are firm/ATS-level or have revision/grain issues, not a clean ticker-level trade panel | Context only; never sum revisions or infer stock-level flow without a validated security-level archive |
| Cboe Open-Close | Historical EOD source; C1 history is deeper than other Cboe venues; one-date sample covered 85.97% of the current 335 names at the tested 20% C1 subset | Conditional options-flow candidate; not full OPRA, no multi-date PIT/vintage admission |
| OptionMetrics IvyDB US + Signed Volume | Strongest paid options candidate in prior feasibility work: long EOD history, permanent identifiers and signed-volume product from 2016 | Require a sample, full price quote, delisted coverage and first-availability/revision policy before any purchase decision |
| ORATS / IVolatility / Databento OPRA / MIAX | Useful alternative or independent replication sources with different history, timing and coverage limits | Do not combine vendors or buy data before one source passes a multi-date schema/PIT/universe audit |
| CFTC TFF/COT | Weekly futures positioning is broad-market context, not single-stock flow; historical release-calendar gate remains unresolved | Park as a possible regime feature only if exact publication timestamps can be reconstructed |
| SEC MIDAS | Daily security-level aggregates exist, but quarterly archive publication timing is not yet strict PIT | Keep as a delayed market-structure context candidate, not an event-time signal |

No vendor was contacted and no data was purchased.

## Next gates

1. Replicate the candidate-specific identity audit on 2023Q1, 2023Q2, 2025Q3, 2012Q1 and 2006Q1. These six quarters are non-contiguous audit strata, not a continuous or probability sample.
2. Build an effective-dated security master joining issuer CIK, CUSIP/ISIN, ticker, exchange, share class, ADR status, mergers, spin-offs, ticker changes and delistings. Never backfill a current ticker into history.
3. Establish survivorship-aware historical universe membership and price/volume coverage before calculating returns.
4. Only then preregister an insider-event study using conservative next-full-session availability and multiple economically justified horizons; no minimum or maximum holding period is imposed.
5. Compare incremental information against frozen LTM/F80 under identical exposure and costs, chronological validation, bootstrap/LOO and untouched OOS discipline. Preserve the legacy holdout.

## Frozen controls

- \`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen.
- No production, universe, capital, parameter or stop changes.
- No alpha or return test, no bootstrap/LOO, no OOS claim and no holdout use.
- No vendor contact or data purchase.
