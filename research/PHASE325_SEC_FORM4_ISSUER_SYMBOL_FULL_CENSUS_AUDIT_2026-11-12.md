# Phase 325 — SEC Form 4/4-A six-quarter issuer-symbol full-census audit

**Date:** 2026-11-12 UTC  
**Status:** COMPLETED — issuer-label feasibility passed; permanent security identity and strict PIT remain closed.  
**Research class:** source/schema and identity-quality audit; no return or alpha test.

## Executive decision

Phase 325 expands the two-quarter issuer-symbol feasibility result from Phase 150 to the immutable six-quarter Form 4/4-A census built in Phase 321. The SEC bulk `ISSUERTRADINGSYMBOL` field is present as a conservative single-symbol candidate on **311,245 of 317,267 accessions (98.1019%)**.

That is useful filing-time issuer-label coverage. It is **not** a permanent security identifier, share-class key, or proof of target-universe coverage. The audit finds **637 ticker candidates reused across more than one issuer CIK** in the sparse six-quarter sample and **28 exact same-filing-date issuer-CIK collision pairs**. The same-day examples include related operating/holding entities, funds, and apparently distinct issuers. Ticker-only joins are therefore rejected.

**Decision:** preserve issuer CIK as the primary issuer key and the SEC symbol exactly as filed as a descriptive, accession-vintage label. Do not map transactions to securities or returns using the symbol alone. Build an effective-dated listing/security/share-class crosswalk before any event study.

## 1. Immutable source and reproducibility

- Source: Phase 321 six-quarter full census, run [43177940904](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43177940904), artifact [13925636412](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43177940904/artifacts/13925636412).
- Source ZIP SHA-256: `e45cab68d1ebe15248cc76bad70b015c8f0bd2052689c0690478bbca4526965c`.
- The Phase 325 workflow downloaded that exact artifact and rechecked the ZIP hash before parsing.
- The source contains 317,267 unique Form 4/4-A accessions from six selected quarters: 2006Q1, 2012Q1, 2023Q1, 2023Q2, 2025Q3 and 2026Q3.
- The audit rejects unexpected forms, malformed CIK/accession/filing-date fields, duplicate accessions, a mismatched total row count, or changed quarter populations.
- Only parsed metadata, period summaries and the 28-row same-day collision diagnostic were uploaded. Raw SEC source bytes were not uploaded.

Final GitHub Actions run [43196055022](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43196055022) passed **7/7 offline regression tests**, immutable source-hash validation, the full census, and all frozen-baseline controls. Artifact [13931894766](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43196055022/artifacts/13931894766), ZIP SHA-256 `6d7930230a60036931857520df07b28087720d54ae9d3bee8f4b1cfe2fbcefa3`.

## 2. Method

The SEC `ISSUERTRADINGSYMBOL` value was normalized conservatively:

- `SINGLE_TOKEN`: one ticker-like token;
- `EXCHANGE_PREFIXED_SINGLE`: one token after an exchange prefix, while retaining the original raw value;
- `MISSING_OR_PLACEHOLDER`;
- `MULTI_OR_FREEFORM`: values containing multiple tokens or delimiters; never split into guessed symbols; and
- `OTHER_NONCANONICAL`.

Only the first two classes count as a **canonical symbol candidate**. This is an audit label created by this project, not an SEC quality flag. It does not assert that the ticker is unique, class-specific, currently active, or the correct security for a particular transaction.

The new collision diagnostic requires the same normalized candidate ticker to appear under two distinct issuer CIKs on at least one **exact same filing date**. This is stricter than overlapping min/max date ranges. It remains a diagnostic, not proof of simultaneous exchange listings or economic identity.

## 3. Full-census results

| Metric | Result |
|---|---:|
| Form 4/4-A accessions | 317,267 |
| Unique issuer CIKs | 11,637 |
| Canonical symbol-candidate rows | 311,245 (98.1019%) |
| Missing/placeholder rows | 2,937 |
| Multi/free-form rows | 1,837 |
| Other noncanonical rows | 1,248 |
| Unique canonical ticker candidates | 11,958 |
| Issuer CIKs with no canonical candidate across sampled quarters | 474 (4.07%) |
| Issuer CIKs with multiple canonical candidates across sampled quarters | 1,293 (11.11%) |
| Issuer CIKs with multiple raw symbol values across sampled quarters | 1,495 (12.85%) |
| Ticker candidates reused across multiple issuer CIKs | 637 (5.33% of candidates) |
| Maximum issuer CIKs observed for one candidate | 4 |
| Exact same-day ticker/issuer-CIK pairs | **28** |
| Shared filing dates across those pairs | 42 |

The row-level candidate rate is high, but the issuer-level result is different: 11,163 of 11,637 issuer CIKs (95.93%) have at least one canonical candidate somewhere in the six sampled quarters. These two coverage measures must not be conflated.

### By sampled quarter

| Quarter | Accessions | Unique issuer CIKs | Canonical candidate rows | Row coverage | CIKs with no candidate | CIKs with multiple candidates |
|---|---:|---:|---:|---:|---:|---:|
| 2006Q1 | 71,679 | 5,866 | 69,239 | 96.5959% | 263 | 188 |
| 2012Q1 | 63,678 | 4,630 | 62,717 | 98.4908% | 126 | 75 |
| 2023Q1 | 63,844 | 4,579 | 63,086 | 98.8127% | 101 | 36 |
| 2023Q2 | 51,791 | 4,438 | 51,165 | 98.7913% | 91 | 27 |
| 2025Q3 | 32,127 | 3,866 | 31,462 | 97.9301% | 125 | 37 |
| 2026Q3 | 34,148 | 4,260 | 33,576 | 98.3249% | 126 | 24 |

The six periods are deliberately selected archive quarters, not a continuous quarterly panel. Multiple candidate symbols for one CIK across these distant snapshots may reflect symbol changes, multiple listed classes, corporate actions or inconsistent as-filed values. The counts do not adjudicate which explanation applies.

## 4. Exact same-day collision examples

The 28-pair CSV is retained in the Phase 325 artifact. Illustrative examples:

| Candidate | Issuer CIK A | Issuer CIK B | Shared filing date(s) | Caution |
|---|---:|---:|---|---|
| DLR | 1297996 | 1494877 | 12 dates, 2023–2026 | Digital Realty Trust, Inc. and Digital Realty Trust, L.P.; related entities, not interchangeable security keys |
| CHI | 1171471 | 1222719 | 2025-08-11 | Two distinct Calamos funds |
| CSAN | 1402902 | 1430162 | 2026-09-15 | Cosan Ltd. and Cosan S.A. |
| FTAI | 1590364 | 1942420 | 2023-01-05 | FTAI Aviation and FTAI Finance Holdco |
| SAFE | 1095651 | 1688852 | 2023-04-04 | Same issuer name under two CIKs; identity requires source-level adjudication |

Some pairs may represent related entities, fund structures, successor/predecessor relationships or other filing conventions. The collision list is not an adjudicated corporate-action map. Its direct implication is narrower and robust: a ticker string cannot serve as the sole issuer or security join key.

## 5. Interpretation and limitations

1. **The symbol is an issuer-level label.** It is not guaranteed to identify the specific class, ADR, derivative, or security referenced by every transaction row.
2. **Issuer CIK is the primary filing identity.** CIK itself is not a fungible security identifier; one issuer may have multiple listed securities and classes.
3. **Sparse-quarter symbol changes are not simultaneous conflicts.** The 1,293 multi-candidate CIKs across sampled quarters require effective-dated history before interpretation.
4. **Same-day collisions are a real join hazard.** The 28 exact-date pairs demonstrate that symbol-only matching can merge different CIKs even on the same filing date.
5. **The audit does not measure broad investable-universe coverage.** It describes Form 4/4-A filers in six SEC archive quarters. It does not establish coverage of the frozen strategy universe, delisted names, or every historical security.
6. **Quarterly archive availability is not event-level PIT.** The bulk data are published as a quarterly compilation. The symbol's presence in a retrospective archive does not establish when the underlying filing first became public. The Phase 320–324 accession/index work remains date-level only, with three exceptions quarantined.
7. **No permanent security master is admitted.** Phase 262's Databento security master remains conditional: its effective/record/created clocks are not customer first-receipt proof, and license/coverage remain unverified. No data were purchased or vendor contacted.

## 6. Decision and next gates

- Keep `ISSUERCIK` as the primary issuer key and preserve the raw `ISSUERTRADINGSYMBOL` per accession.
- Never split multi/free-form symbols or use a ticker-only join.
- Build an effective-dated issuer → listing → security → share-class crosswalk using permanent identifiers where independently verified (e.g. CUSIP/ISIN/FIGI and listing/security IDs), while preserving spin-offs, mergers, delistings, relistings, ADRs and symbol reuse as distinct lineage events.
- Adjudicate the 28 same-day collisions and the 1,293 multi-candidate issuer CIKs against original filings and independent corporate-action/security-master evidence.
- Measure transaction-level mapping and survivorship-aware coverage against the actual broad historical investable universe before creating event features.
- Keep Form 4 amendments as separate disclosure vintages and use the Phase 271 footnote/transaction screen; P code alone remains open-market **or private**, not proof of public-market execution.
- Only after identity, coverage and PIT gates pass should clustered issuer × disclosure-batch events be tested incrementally against frozen LTM/F80 with identical exposure/costs, chronological OOS, bootstrap and LOO.

**No return/alpha test, bootstrap/LOO, chronological OOS or holdout test was run.** No vendor was contacted, no data were purchased, and no production, universe, capital or parameter changes were made. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Files

- Auditor: [phase325_form4_issuer_symbol_full_census_audit.py](phase325_form4_issuer_symbol_full_census_audit.py)
- Regression tests: [test_phase325_form4_issuer_symbol_full_census_audit.py](test_phase325_form4_issuer_symbol_full_census_audit.py)
- Workflow: [phase325_sec_form4_issuer_symbol_full_census.yml](../.github/workflows/phase325_sec_form4_issuer_symbol_full_census.yml)
- Period summary and exact same-day collision rows: [Phase 325 artifact](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43196055022/artifacts/13931894766)
