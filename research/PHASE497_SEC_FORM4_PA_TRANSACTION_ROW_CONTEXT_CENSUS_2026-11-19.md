# Phase 497 — SEC Form 4 P/A transaction-row context census

**Audit date:** 2026-11-19 UTC  
**Source cohort:** Phase 476 run [44440313382](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44440313382), 637 immutable accessions  
**Audit run:** [44487183018](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44487183018)  
**Artifact:** [14511206505](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44487183018/artifacts/14511206505)  
**Artifact ZIP SHA-256:** `91582dc70925e0c3d9571a2eec246404eb6941c602301ac8d16afdf6bf50a8c5`  
**Disposition:** TRANSACTION-ROW CONTEXT CENSUS ONLY. No event study, alpha test or signal admission.

## Executive finding

The live audit re-fetched and parsed all 637 ownership XML payloads in the immutable Phase 476 cohort. It found 145 non-derivative Table I rows coded P/A. Of those, 81 satisfy a narrow *structural completeness screen*: one reporting owner in the filing, direct ownership, filing-level Rule 10b5-1 box = no, positive numeric price and share fields, and transaction date no later than filing date.

**Naming correction:** the current parser and aggregate output use `structural_completeness_queue_rows`. An earlier draft used the overclaiming label `high_specificity_manual_review_rows`; that name is retired. The 81 rows are not high-specificity evidence of discretionary or exchange-traded purchases. The screen does not require explicit open-market evidence, and SEC code P also includes private purchases. Treat 81 only as a completeness-based review queue, not as an open-market cohort or signal.

## 1. Retrieval and integrity

| Control | Result |
|---|---:|
| Immutable source accessions | 637 |
| Complete submissions retrieved | 637 |
| Ownership XML parsed | 637 |
| XML parse errors | 0 |
| Filing dates | 637 on 2026-11-18 |
| Raw payloads persisted | No |
| Transaction-level rows persisted | No |

The prior successful poll lower bound was 2026-11-18 19:26:08 UTC. Local first-seen upper bounds span 2026-11-19 01:54:11–01:54:34 UTC. These are collector observation bounds, not exact public-availability timestamps. The acceptance/feed clocks reconciled in Phase 496, but neither acceptance nor Atom `updated` proves the exact instant a market participant could retrieve the filing.

## 2. P/A transaction-row context

| Diagnostic | Count |
|---|---:|
| Non-derivative Table I P/A rows | 145 |
| Single-owner filing rows | 133 |
| Multiple-owner filing rows | 12 |
| Direct ownership rows | 81 |
| Indirect ownership rows | 64 |
| Filing-level 10b5-1 = no | 136 |
| Filing-level 10b5-1 = yes | 9 |
| Positive numeric price fields | 145 |
| Positive numeric share fields | 145 |
| Transaction date before filing date | 122 |
| Transaction date same as filing date | 23 |

The filing-owner/directness/plan matrix is:

| Filing owner bucket | Ownership | Filing-level 10b5-1 flag | P/A rows |
|---|---|---|---:|
| Single | Direct | No | 81 |
| Single | Indirect | No | 43 |
| Single | Indirect | Yes | 9 |
| Multiple | Indirect | No | 12 |

The 12 rows in multiple-owner filings remain at filing grain. They are not expanded into owner-level trades. The 10b5-1 flag remains a filing-level field and is not attributed to individual owners or rows.

## 3. Footnote diagnostics

- 93 P/A rows referenced at least one footnote; all 93 had their referenced text resolved.
- 52 P/A rows had no footnote reference.
- No unresolved footnote references were counted.
- Keyword diagnostics across the 145 P/A rows: `open_market` 5; `trust` 28; Rule 10b5-1 mention 9; compensation/vesting 2; employee-plan wording 3.
- These keyword counts are non-exclusive, based on referenced footnote text, and are not adjudications of transaction intent or execution venue.

### Repeat verification and structural-queue cross-tab

A later repeat run, [44492496082](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44492496082), attempted the same immutable 637-accession cohort. It retrieved and parsed 636/637 ownership XML payloads; one submission was unavailable in that run. The repeat run reproduced the aggregate counts of 145 P/A rows and 81 structural-queue rows, but it is **not** a complete independent replication. The artifact does not identify the failed accession, so targeted recovery is not possible from that artifact alone.

Within the 636 payloads parsed by the repeat run, the structural queue had:
- 34 rows with a referenced footnote and 47 without a reference;
- 2 rows with an explicit `open_market` keyword and no private-purchase keyword;
- 79 rows with neither keyword;
- no rows classified as private-purchase-only or both by this narrow keyword screen.

This cross-tab is provisional because one of the 637 filings was unavailable in the repeat run. Keyword absence is not evidence of a private purchase, nor does an `open_market` mention independently prove exchange execution. The complete 637/637 run 44487183018 did not emit this cross-tab. Do not promote the provisional 2/81 result into a transaction classification.

## 4. Interpretation

1. Code P is not an exchange-only code: it includes open-market **or private** purchases. P/A is not proof of a discretionary personal buy.
2. Direct ownership, a filing-level 10b5-1 “no” flag, price/shares, and transaction date improve context completeness but do not establish motive, execution venue, or absence of other pre-arranged arrangements.
3. A footnote keyword match is a diagnostic only. It requires human/contextual interpretation and cannot be converted automatically into a trade classification.
4. The 145 rows are not 145 independent insiders, filings, or issuer-events. Multiple transaction rows can share a filing, issuer, date, or reporting person.
5. All 637 filings are from one filing date. This cohort is a parser/context census, not a historical sample with statistical power.

## 5. Historical identity and universe gate remains binding

Phase 453 confirmed that SEC bulk Form 345 has an as-filed issuer trading-symbol field, but it is submission-level rather than a complete transaction-security master; multi-class accessions often contain only one issuer symbol. Phase 455 found only five exact issuer-filing-event overlaps in its six-quarter candidate sample against a static 335-symbol snapshot (5/224 issuer-filing events). That snapshot has no effective dates and cannot prove historical F80 membership.

Accordingly, the 637 current-cohort issuer/symbol pairs and the 81-row structural screen cannot be joined to historical F80 by ticker alone. The next identity gate must preserve issuer CIK, accession, raw as-filed symbol, transaction security title, share class, listing, effective interval, inactive/delisted state and historical universe membership separately. Unknowns remain unknown.

## 6. Decision and next gate

**Decision: P_A_ROW_CONTEXT_SCREEN_ONLY; NO PROMOTION.**

Next work:
1. Keep the corrected `structural_completeness_queue_rows` name; do not restore the retired `high_specificity_manual_review_rows` label.
2. Preserve the repeat-run limitation and add failed-accession identifiers to a future diagnostic artifact before any targeted recovery; the current 636/637 cross-tab remains provisional.
3. Reconcile the 321 issuer/as-filed-symbol pairs to an effective-dated security-class/listing source and the exact frozen-universe membership by date. The existing Phase 97 ranking remains: Databento PIT Security Master for a possible two-clock reference layer; CRSP for inactive-security/return validation; Norgate for a separate index-defined universe. No vendor is approved or purchased.
4. Only after identity, historical membership and conservative public-availability gates pass, preregister a discretionary-purchase hypothesis and test incremental information versus frozen LTM/F80, controlling prior returns, momentum, liquidity and volatility, with identical exposure/costs, chronological OOS, block bootstrap and LOO.

No forward returns, event study, backtest, OOS, bootstrap, LOO or holdout was used. No signal was admitted. `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, capital, exposure, costs, holdout and production remain unchanged.

## 7. Validation and reproduction

Run [44487183018](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44487183018) completed with `offline-regression` and `live-audit` successful; 637/637 submissions were retrieved and parsed. Its aggregate-only artifact is [14511206505](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44487183018/artifacts/14511206505).

Repeat run [44492496082](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44492496082) also passed offline and live jobs, but retrieved/parsed 636/637 submissions (one unavailable). It emitted the provisional queue cross-tab above in artifact [14513398607](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44492496082/artifacts/14513398607), ZIP SHA-256 `cb74b4a47ab551737774ccd6e50eb8fcdcbaa101879fed231776e6d1e82d141b`. The no-promotion/no-persistence controls passed; do not describe the repeat run as 637/637.

Reproduction:
```bash
python -m unittest -v research.test_phase497_form4_purchase_row_context_census
python -m research.phase497_form4_purchase_row_context_census \
  --events research/data/sec_form4_first_seen/events.csv \
  --expected-count 637 \
  --output phase497_output
```


## 8. Subsequent prospective metadata capture

The later scheduled Phase 476 poll [44505739718](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44505739718) completed at 2026-11-19 10:27:06 UTC and added 18 new canonical Form 4 events to the main append-only ledger. The poll recorded 37 new accession occurrences, 19 within-feed duplicate occurrences, zero cross-feed duplicates, and 18 bounded metadata events. It downloaded no filing XML and admitted zero research observations or signals. These 18 newer events are a separate, unaudited cohort and are not part of the fixed 637-accession Phase 497 sample.


## 9. Integration

PR [#153](https://github.com/jafelix81/NuevaEstrategia/pull/153) was merged on 2026-11-19 at 10:52:49 UTC after PR CI [44509660064](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44509660064) passed offline regression; the live-audit job was skipped as intended. Squash merge / main HEAD: `2a1e66ab9b65096eaa1f95472716117ef33328bf`. The latest Actions API count at merge was 7,886 total runs; no active/queued run appeared in the latest 20 records.