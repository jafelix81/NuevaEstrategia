# Phase 455 — SEC Form 4 high-precision cohort vs frozen 335-symbol snapshot

**Audit time:** 2026-11-17 12:50 UTC  
**Disposition:** DESCRIPTIVE OVERLAP ONLY. The six-quarter candidate sample contains five issuer-filing events with an exact ticker match to the frozen 335-symbol snapshot, but the snapshot has no effective dates and is not a historical security master. No event study or alpha test is authorized.

## 1. Immutable inputs

- SEC Form 345 six-archive artifact: [Phase 342 run 43265704634](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43265704634), [artifact 13965917386](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43265704634/artifacts/13965917386).
- Artifact ZIP SHA-256: `16614b404f007b78f47951ef84604660ea6612f0c86f1b2ba5a6fa7b7d52d80c`.
- All six nested SEC ZIP hashes were reverified against Phase 342: 2006Q1, 2012Q1, 2023Q1, 2023Q2, 2025Q3 and 2026Q3.
- Frozen universe snapshot: `research/phase44_frozen_universe_335_tickers.csv`, recovered from commit `1aa1b91f383ce9cef375a43e775c736a27356a5f`; Git blob SHA-1 `7edbd62b4fb34a6123276e4ce45cb3c1c62479c7`; SHA-256 `f850655a22a8843dad90e9562b3152b9ca064560586109022b5bfd205a003dda`. It contains 335 unique tickers.

## 2. Exact-match rule

Only outer whitespace is trimmed and the symbol is uppercased. A match requires exact equality to one ticker in the 335-symbol file. Exchange prefixes are not stripped; comma-delimited values are not split; ticker changes are not inferred. Sentinels remain unknown. This is deliberately a strict issuer-symbol overlap test, not a security-master join.

## 3. Results

| SEC archive | Candidate rows | Accessions | Issuer CIKs | Issuer × filing-date events | Exact rows | Exact accessions | Exact issuer-events |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2006Q1 | 10 | 8 | 7 | 8 | 0 | 0 | 0 |
| 2012Q1 | 102 | 47 | 16 | 43 | 0 | 0 | 0 |
| 2023Q1 | 59 | 41 | 19 | 32 | 0 | 0 | 0 |
| 2023Q2 | 92 | 63 | 27 | 57 | 0 | 0 | 0 |
| 2025Q3 | 65 | 44 | 25 | 36 | 8 | 5 | 4 |
| 2026Q3 | 85 | 59 | 31 | 48 | 1 | 1 | 1 |
| **Total** | **413** | **262** | **109 unique** | **224** | **9** | **6** | **5** |

The five exact issuer-filing events are:

- VRTX — 2025-08-07 (4 candidate transaction rows across 2 accessions, one issuer/date event).
- CRSP — 2025-08-08.
- NTLA — 2025-08-22.
- OPEN — 2025-08-28 (2 transaction rows, one accession/event).
- OPEN — 2026-08-14.

Across the complete six-quarter candidate sample, 4 distinct issuer CIKs and 4 distinct symbols match the snapshot. Two other issuer CIKs have multiple as-filed symbols across sampled quarters (TKOI.OB → TKOI; AULT → GPUS), reinforcing the need for effective dating. No raw symbol mapped to multiple CIKs in this candidate sample. There were no blank/sentinel or formatted-ambiguous candidate symbols; 404 transaction rows had a valid as-filed symbol outside this static snapshot.

## 4. Interpretation

The 335 file is a frozen ticker snapshot, not a point-in-time active-universe or listing/class master. Therefore:

- Zero matches in 2006Q1–2023Q2 do **not** establish zero historical membership or a source failure; ticker changes, listing history and universe membership by date are unresolved.
- Five matched issuer-filing events are a small descriptive yield in two widely spaced recent quarters, not an estimate of signal frequency or power.
- `ISSUERTRADINGSYMBOL` is accession/issuer-level. It does not resolve every transaction security/class. A same-issuer multi-class filing can still be ambiguous.
- The high-precision Phase 342 screen is a candidate screen, not proof of discretionary intent or exchange execution. Code P can mean open-market or private purchase; footnote wording and AFF10B5ONE=false do not prove the trade was discretionary.
- Bulk `FILING_DATE` is date-only, not exact first-public receipt. The prior conservative next-full-XNYS-session rule remains necessary; it was not tested here.

## 5. Decision and next gate

Retain Form 4 as a conditional research source; do not run an event study yet. The next gate is a full quarterly census and effective-dated issuer/ticker/security-class/listing crosswalk for the exact frozen universe. Preserve unknown, changed-ticker, multi-class and inactive/not-yet-listed states separately. Only after that gate should we assess whether enough independent issuer-event observations exist for a preregistered test against frozen LTM/F80 with identical exposure/costs, chronological OOS, bootstrap and LOO.

No forward returns, alpha, bootstrap/LOO, OOS or holdout test was run. No signal was admitted. `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, capital, exposure, holdout and production remain unchanged. No raw SEC archives or transaction-level rows are committed.

## 6. Reproduction

```bash
python -m unittest -v research.test_phase455_form4_universe_overlap_audit
python -m research.phase455_form4_universe_overlap_audit --artifact phase342-six-archive.zip --universe phase44_frozen_universe_335_tickers.csv --output phase455_result.json
```
