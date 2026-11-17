# Phase 453 — SEC Form 345 as-filed issuer-symbol and security-class crosswalk audit

**Audit time:** 2026-11-17 12:32 UTC  
**Disposition:** DIRECT AS-FILED ISSUER SYMBOL FIELD CONFIRMED IN BOTH HISTORICAL ENDPOINT ARCHIVES; FIELD IS NOT A SECURITY-LEVEL MASTER. Re-open the Form 4 identity path using this field as primary issuer evidence, but retain class/listing ambiguity quarantines. No return or alpha test authorized.

## 1. Immutable evidence

Phase 439 showed that the legacy HTML identity bridge's 53/96 exact ticker matches were transaction-row weighted and concentrated in one issuer. That correctly rejected the legacy bridge as a general identity classifier, but did not establish that the official SEC bulk archive lacked a better as-filed issuer-symbol field.

Re-audited the existing Phase 39 actual-file artifact; no new SEC request was made:

- [Workflow run 40606706518](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40606706518)
- [Artifact 12781850078](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40606706518/artifacts/12781850078)
- Outer ZIP SHA-256: `203d7b1d2e29c999da318456af72e621cb30ef9a470d8f1610d088f9bebecb66`
- 2012Q1 inner ZIP SHA-256: `0cac6f943813dae94c20ecc8bca63fda692e2b8ac6d02ce2c322ab411f45c357`
- 2026Q3 inner ZIP SHA-256: `a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3`

Both actual `SUBMISSION.tsv` files contain `ISSUERTRADINGSYMBOL`; both `NONDERIV_TRANS.tsv` files contain transaction-level `SECURITY_TITLE`. The symbol is stored at submission/accession grain, not on each transaction row.

## 2. Results

| Diagnostic | 2012Q1 | 2026Q3 |
|---|---:|---:|
| Form 4 / 4-A submissions | 63,678 | 34,148 |
| Distinct issuer CIKs | 4,630 | 4,260 |
| Non-derivative Form 4 / 4-A rows | 101,473 | 59,834 |
| Distinct accessions with non-derivative rows | 50,931 | 28,955 |
| Sentinel issuer-symbol submissions | 492 (0.773%) | 429 (1.256%) |
| Non-derivative rows with sentinel issuer symbol | 591 (0.582%) | 474 (0.792%) |
| Comma-delimited issuer-symbol fields | 204 | 67 |
| Exchange-prefixed symbol fields | 246 | 79 |
| Numeric-only symbol fields | 2 | 18 |
| Exact raw symbol values linked to multiple issuer CIKs | 15 | 6 |
| Issuers with multiple distinct non-sentinel raw symbol values in quarter | 99 | 28 |
| Accessions with multiple common-stock/share class or series tokens | 51 | 85 |
| Multi-class accessions with only one issuer-symbol string | 48 | 84 |

Sentinel values include `NONE`, `N/A`, `NA` and `[NONE]`. They are not converted to zero or a valid ticker. Exchange prefixes and comma-delimited strings are retained verbatim; the audit does not strip or split them into guessed security assignments.

## 3. Interpretation

**Positive finding:** the official bulk dataset has a direct as-filed issuer trading-symbol field in both 2012Q1 and 2026Q3. This is materially better evidence than relying on the Phase 346 legacy-HTML ticker-prose bridge alone. Therefore Phase 439's 53/96 result is not a ceiling on what the bulk dataset may support.

**Binding limitation:** `ISSUERTRADINGSYMBOL` is submission-level, while one accession can contain transactions in multiple securities/classes. In these archives, 48/51 (2012Q1) and 84/85 (2026Q3) multi-class accessions had only one issuer-symbol string. A single issuer ticker cannot safely identify every class-specific transaction. The archive also contains sentinel values, exchange-prefixed strings, comma-delimited symbols, multiple symbols for an issuer within a quarter, and raw symbol values associated with more than one issuer CIK.

The field is a strong **issuer-level identity anchor**, not a complete effective-dated listing/security master. `SECURITY_TITLE` must be joined to a class/listing crosswalk, and unresolved rows must remain unknown.

## 4. Revised disposition

- Retain Phase 439's correction: 53/96 is row-weighted legacy-HTML evidence, not independent issuer or accession coverage.
- Use `ISSUERCIK + ACCESSION_NUMBER + ISSUERTRADINGSYMBOL` from the as-filed bulk archive as primary issuer-level evidence.
- Preserve raw symbol, filing accession and original transaction security title. Do not split comma lists or strip exchange prefixes without a verified rule.
- Quarantine sentinel symbols, ambiguous multi-class accessions, issuer-symbol collisions and ticker changes until resolved by an effective-dated listing/security source.
- Use original filing EDGAR `ACCEPTANCE-DATETIME` as the public-information clock; quarterly bulk publication date and transaction date are not substitutes.
- Reconstruct and validate the frozen-universe crosswalk using the exact historical F80 constituent file. Do not recreate the 335-name list from current tickers or a present-day SEC ticker file.

The 2012Q1 and 2026Q3 samples are endpoint feasibility checks, not a full quarterly census or a random population sample. Do not extrapolate these counts to all Form 4 filings or to the frozen universe.

## 5. Next gate

1. Recover the exact frozen F80 universe/security list from its immutable source artifact.
2. Run the issuer-symbol parser over all available quarterly Form 345 archives, preserving each quarter's as-filed values.
3. Reconcile each accession's raw issuer symbol and transaction `SECURITY_TITLE` to an effective-dated listing/class identity; preserve ambiguity and collision states.
4. Validate accession acceptance timestamps and amendment lineage independently of the bulk file's quarter-posting clock.
5. Report event-level identity resolution and eligible-universe coverage separately. Do not require an issuer to have an insider transaction in every quarter; absence of an event is not a mapping failure when the complete filing census is available.
6. Only after identity and historical-universe gates pass, preregister discretionary-purchase and multi-insider-clustering hypotheses. Exclude mechanical/plan-based transactions conservatively, control prior returns/volume/volatility, and compare incremental information with frozen LTM/F80 under identical exposure, costs, chronological OOS, bootstrap and LOO.

**No forward returns, alpha, OOS, bootstrap, LOO or holdout test was run. No signal was admitted.** `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, capital, exposure, holdout and production remain frozen.

## 6. Operational preflight

- Main HEAD: `cfe97c971cceb027a50f924ce9984ba6489492d5` (Phase 452 state update).
- Latest overall Actions run [44009082677](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44009082677): Phase 448 PR CI, offline 18/18; live capture skipped; no artifact. Latest main push [44007937167](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44007937167): Phase 447, 14/14 synthetic tests; no artifact.
- Explicit Actions queries returned zero in-progress and zero queued. The latest-run page reports 7,691 total runs.
- Branch API pagination returned 185 branches (100 + 85; page 3 empty), not the 285 recorded in Phase 452. Open PRs remain 56; workflow files 69. The earlier 285 count is not reproducible and is corrected here.
- Latest SEC Form 144 scheduled run remains [43970444015](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43970444015), failed on the 144/A read timeout; no later scheduled run is present after the :47 UTC re-arm.
- CFTC Phase 384 remains scheduled for 22:25 UTC weekdays; the 2026-11-17 slot is still in the future at this audit. Latest known run [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200) is a push/bootstrap with 3,035 warm-up rows and zero eligible prospective observations.
- FINRA live Short Interest remains blocked by missing OAuth secrets; no live request was made.

## 7. Reproduction

```bash
python research/phase453_form4_bulk_symbol_crosswalk_audit.py --input phase39_form345_actual_file_audit.zip --output phase453_summary.json
python -m unittest -v research.test_phase453_form4_bulk_symbol_crosswalk_audit
```

The parser verifies the outer and both nested ZIP SHA-256 hashes before producing aggregate diagnostics. It writes no raw filing rows or raw SEC data.
