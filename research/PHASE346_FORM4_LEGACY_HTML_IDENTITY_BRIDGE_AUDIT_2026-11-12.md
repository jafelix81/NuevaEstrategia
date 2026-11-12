# Phase 346 — SEC Form 4 legacy HTML identity bridge audit

**Date:** 2026-11-12 UTC  
**Status:** COMPLETED_LEGACY_FORM4_HTML_IDENTITY_BRIDGE_AUDIT  
**Disposition:** partial salvage only; no universal legacy HTML crosswalk admitted.

## Executive decision

Phase 346 tested whether older SEC periodic filings can supplement the missing XBRL TradingSymbol / class / exchange facts in the 2006Q1 and 2012Q1 Form 4 candidate cohorts.

The answer is **yes for a small, explicitly evidenced subset, but not at a coverage level that supports a universal historical security master**. The parser preserves four distinct evidence types: same-row class/exchange tables, Section 12(g) class-only statements, issuer-specific ticker prose, and exchange-only prose. It does not turn a missing exchange field into a listing, and it does not join a class and an exchange found in separate table rows.

## 1. Reproducible input and temporal controls

- Source: Phase 345 immutable artifact 13978077938, produced by run [43290739469](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43290739469).
- Source artifact SHA-256: 7f8fe1191661be514cb2bc4c9551d07644516cfe9a4b9d52fa44dd59b950dcfd.
- Phase 346 re-used the Phase 345 raw SEC responses; it made **no new SEC request**.
- 112 candidate transaction rows were examined: 10 from 2006Q1 and 102 from 2012Q1.
- 18 unique periodic anchor documents were recovered from the immutable manifest and independently re-hashed: **18/18 SHA-256 matches**.
- 96/112 candidate rows (85.71%) had an anchor strictly before the transaction and no more than 365 calendar days old.
- Five candidate rows had an anchor after the transaction; one used a stale anchor older than 365 days; ten had no selected anchor. These remain excluded from transaction-date identity.

The sample is purposively selected and non-contiguous. These percentages are sample diagnostics, not market-wide coverage estimates.

## 2. What the legacy documents actually establish

| Evidence class | 2006Q1 | 2012Q1 | Interpretation |
|---|---:|---:|---|
| Unique same-row class + exchange table | 0 anchors | 2 anchors | Only one of the two anchors was strictly pre-transaction |
| Issuer-specific ticker prose matching Form 4 | 1 row | 52 rows | Exact textual corroboration, but not automatically a national-exchange listing |
| Exchange prose without direct ticker match | 3 rows | 1 row | Does not by itself link the Form 4 symbol to the exchange |
| Pre-transaction ticker mismatch | 1 row | 0 rows | Quarantine; do not silently normalize the symbol |
| No direct legacy bridge among PIT-eligible rows | 1 row | 37 rows | No inferred mapping |

Across both cohorts, 53/96 PIT-eligible candidate rows had an issuer-specific ticker mention matching the Form 4 symbol (55.21%). Only **one anchor group** had a usable, unique same-row class/exchange table and was strictly pre-transaction; it contributed two candidate rows. This is far below the 95% identity gate and is not a universal bridge.

## 3. High-value case adjudications

### 2006Q1

- **BMHC (CIK 1046356):** the 2006-02-27 10-K identifies Common Stock under Section 12(g), and the issuer's own equity-market discussion explicitly says its common shares trade on NASDAQ under symbol BMHC. The 2006-03-09 Form 4 candidate is pre-anchor and the symbol matches. This is strong issuer/class/ticker prose corroboration, but not a same-row Section 12(b) exchange-table match.
- **ZRAN (CIK 1003022):** the 2005-11-09 10-Q discusses the common-stock closing price as reported on the Nasdaq National Market. Three Form 4 candidate rows carry ZRAN, but the periodic filing does not explicitly name ZRAN. Keep as exchange-prose-only; do not promote the ticker link automatically.
- **FEIC (CIK 914329):** the 2005-10-09 10-Q did not provide a direct ticker/class/exchange bridge for the candidate row.
- **AVN (CIK 858803):** the 2006-02-09 10-Q states that the issuer's common stock began trading on a split-adjusted basis on 2006-01-18 under the **new ticker AVN.R**. The Form 4 candidate uses AVN for a 2006-02-14 transaction. This is a pre-event, issuer-specific ticker conflict. The candidate is quarantined; no suffix stripping or alias merge is allowed.
- **RSMI:** the selected periodic anchor is 749 days before the transaction and therefore stale. Its old ticker text is not used for PIT identity.

### 2012Q1

- **CLSN / Celsion (CIK 749647):** the 2012-03-15 10-K/A contains a same-row COMMON STOCK, PAR VALUE $.01 PER SHARE / NASDAQ CAPITAL MARKET table entry. The same filing explicitly states that its common stock trades under symbol CLSN. Both candidate Form 4 transactions (2012-03-19 and 2012-03-21) occur after the anchor. This is the one clean same-row class/exchange + issuer-ticker bridge in the sample.
- **AGN / Allergan (CIK 850693):** the 2012-02-28 10-K contains a Common Stock / New York Stock Exchange row and explicit AGN ticker text. However, the candidate transaction occurred on 2011-03-14, nearly a year before the anchor. The evidence is post-transaction and is excluded.
- **ONTC / Onteco (CIK 1427352):** the 2011-11-17 10-Q identifies Common Stock under Section 12(g) and states that the issuer's trading symbol is ONTC. The filing also discusses the OTC Markets name change. The 48 pre-transaction candidate rows have exact ticker-text corroboration, but this is an OTC context, not a national-exchange listing; preserve the venue class and do not treat it as interchangeable with NYSE/Nasdaq securities.
- **NLN (CIK 1387713):** the 2012-03-16 10-K identifies Common Stock and states that the principal public market is the Toronto Stock Exchange, with symbol NLN. The two candidate rows have a direct ticker match, but the filing says there is no established public trading market for the common stock in the United States. Keep this as foreign-listed; exclude it from a U.S.-listed universe unless that universe is deliberately broadened.
- **TKOI / TKOI.OB:** both symbol forms occur in Form 4 rows for the same CIK, but the selected periodic filing does not directly reconcile them. Preserve both exact source strings; do not strip .OB or collapse the pair.
- **PCSV (CIK 1122020):** the 2011-11-14 10-Q contains historical OTC Bulletin Board common-stock price references in note disclosures, but no direct issuer ticker statement. Keep as weak exchange-prose-only context, not a ticker crosswalk. **CBIN, AHC, ONP, SHOR, TPI and WTM:** the selected anchors do not supply a direct ticker/class/exchange bridge. Four ONP rows have post-transaction anchors and are excluded.

## 4. Binding rules after Phase 346

1. A same-row class/exchange table is a distinct evidence grade; do not synthesize a row from separate table sections.
2. A Section 12(g) class statement does not establish a national exchange.
3. Issuer-specific ticker prose can corroborate a Form 4 symbol, but venue must remain separately classified (national exchange, foreign exchange, OTC, or unknown).
4. Exchange-only prose is not a ticker crosswalk.
5. Any pre-event symbol conflict (AVN versus AVN.R) is quarantined. Never remove suffixes or infer aliases without effective-dated evidence.
6. Same-day, post-transaction, stale and missing anchors are not PIT identity evidence.
7. Do not admit this legacy HTML method as a universal security master. Retain the evidence rows for candidate-level review only.

## 5. Research decision and next work

- Stop expanding the same-row HTML parser as a universal solution; its coverage is too sparse.
- Retain the candidate-level evidence for BMHC and CLSN, keep ONTC/OTC and NLN/TSX in separate venue classes, and quarantine AVN.
- Do not run an insider return study from this sample. It is selected, incomplete and not a survivorship-aware price panel.
- The next research priority is the independent SEC 13D activist-disclosure line: complete initial/amendment lineage and effective-dated CUSIP/security identity before any event study. Options, N-PORT, CFTC and FINRA remain separate hypotheses with their existing admission gates.

## 6. Validation and artifacts

- GitHub Actions [run 43307873506](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43307873506): SUCCESS.
- 11/11 offline regression tests passed; cross-run source artifact download, hash checks, audit and artifact upload all succeeded.
- Artifact [13985120745](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43307873506/artifacts/13985120745).
- Phase 346 output artifact SHA-256: b526112713cc4942db3c4a9050000e2da4190a17c1fe1f9cc6ded962693b6e9c.
- Auditor: research/phase346_form4_legacy_html_identity_bridge_audit.py.
- Tests: research/test_phase346_form4_legacy_html_identity_bridge_audit.py.
- Workflow: .github/workflows/phase346_form4_legacy_html_identity_bridge.yml.

## Guardrails

No returns, alpha, forward-label, bootstrap, LOO, chronological OOS or holdout test was run. No source was PIT-admitted. F80_TOP20_PARTIAL50_BASELINE_C20, production, universe, capital and parameters remain unchanged. No vendor was contacted, no paid data was purchased, and no new terms or credentials were accepted.
