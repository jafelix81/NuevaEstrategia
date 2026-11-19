# Phase 497 — SEC Form 4 P/A transaction-row context census

**Audit date:** 2026-11-19 UTC  
**Source cohort:** Phase 476 run [44440313382](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44440313382), 637 immutable accessions  
**Audit run:** [44487183018](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44487183018)  
**Artifact:** [14511206505](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44487183018/artifacts/14511206505)  
**Artifact ZIP SHA-256:** `91582dc70925e0c3d9571a2eec246404eb6941c602301ac8d16afdf6bf50a8c5`  
**Disposition:** TRANSACTION-ROW CONTEXT CENSUS ONLY. No event study, alpha test or signal admission.

## Executive finding

The live audit re-fetched and parsed all 637 ownership XML payloads in the immutable Phase 476 cohort. It found 145 non-derivative Table I rows coded P/A. Of those, 81 satisfy a narrow *structural completeness screen*: one reporting owner in the filing, direct ownership, filing-level Rule 10b5-1 box = no, positive numeric price and share fields, and transaction date no later than filing date.

**Important correction to the workflow's output label:** the artifact field is named `high_specificity_manual_review_rows`, but the 81 rows are not high-specificity evidence of discretionary or exchange-traded purchases. The screen does not require an explicit open-market footnote, and SEC code P also includes private purchases. Treat 81 only as a completeness-based manual-review queue, not as an open-market cohort or signal.

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

The audit did not produce the cross-tab of footnote language against the 81-row structural screen. In particular, it does **not** establish that all 81 rows have open-market language. A follow-up must compute row-level aggregate intersections and preserve ambiguous/private wording as separate categories before any manual-review priority is assigned.

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
1. Correct the misleading `high_specificity_manual_review_rows` label in a follow-up code change; the current 81 is a structural-completeness queue only.
2. Add aggregate cross-tabs for explicit open-market, private-purchase, trust, compensation/vesting, plan and unresolved footnote language within the structural screen.
3. Reconcile the 321 issuer/as-filed-symbol pairs to an effective-dated security-class/listing source and the exact frozen-universe membership by date. The existing Phase 97 ranking remains: Databento PIT Security Master for a possible two-clock reference layer; CRSP for inactive-security/return validation; Norgate for a separate index-defined universe. No vendor is approved or purchased.
4. Only after identity, historical membership and conservative public-availability gates pass, preregister a discretionary-purchase hypothesis and test incremental information versus frozen LTM/F80, controlling prior returns, momentum, liquidity and volatility, with identical exposure/costs, chronological OOS, block bootstrap and LOO.

No forward returns, event study, backtest, OOS, bootstrap, LOO or holdout was used. No signal was admitted. `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, capital, exposure, costs, holdout and production remain unchanged.

## 7. Validation and reproduction

Run [44487183018](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44487183018) completed:
- `offline-regression`: success;
- `live-audit`: success;
- 637/637 submissions retrieved and XML parsed;
- no-promotion and no-persistence gates passed;
- aggregate-only artifact uploaded.

Reproduction:
```bash
python -m unittest -v research.test_phase497_form4_purchase_row_context_census
python -m research.phase497_form4_purchase_row_context_census \
  --events research/data/sec_form4_first_seen/events.csv \
  --expected-count 637 \
  --output phase497_output
```
