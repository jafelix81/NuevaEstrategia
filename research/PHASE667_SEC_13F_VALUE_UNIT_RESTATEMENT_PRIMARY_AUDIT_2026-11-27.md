# Phase 667 — SEC 13F value-unit restatement: primary-source audit

**Audit cutoff:** 2026-11-27 17:12 UTC  
**Parent:** Phase 666 branch `aa224aba02bf7f04273a18e3f7d6c8cf6bc5ddc0`  
**Disposition:** PASS for the four primary documents reviewed; **value-unit correction only / no signal promotion**.

## 1. Preflight and source run

- Reviewed the latest 40 Actions runs, their statuses, the open Phase 666 PR, branches and current main head before continuing.
- No queued, in-progress, waiting, requested or pending run was present.
- Phase 666's source capture remains [run 46026323554](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46026323554), with both jobs successful and artifact [15212890251](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46026323554/artifacts/15212890251).
- The capture produced 15 new 13F-HR/A metadata events: 14 with unverified path-CIK candidate 0001778131 and one with candidate 0001046192. All remain metadata-only in the repository ledger.
- Phase 666 PR [#255](https://github.com/jafelix81/NuevaEstrategia/pull/255) remains open as a draft, based on main `6919a03ca2da8da4b6a428c29e088531cba300f9`. This follow-up is stacked on its head; no main or ledger changes were made.

## 2. Four primary SEC documents independently establish the same correction

The SEC primary `primary_doc.xml` documents below identify CIK 0001778131, BI Asset Management Fondsmaeglerselskab A/S, Form 13F-HR/A, amendment number 1 and amendment type RESTATEMENT. Each states that the entire report is restated to correct Column 4 (Value) and the Information Table Value Total from thousands of dollars to nearest-dollar values, and that **no other report information has changed**.

| Accession | Report period | Table entries | Corrected value total (USD) |
|---|---:|---:|---:|
| [0001778131-26-000018](https://www.sec.gov/Archives/edgar/data/1778131/000177813126000018/primary_doc.xml) | 2025-03-31 | 909 | $8,880,262,178 |
| [0001778131-26-000021](https://www.sec.gov/Archives/edgar/data/1778131/000177813126000021/primary_doc.xml) | 2025-12-31 | 654 | $11,329,049,373 |
| [0001778131-26-000022](https://www.sec.gov/Archives/edgar/data/1778131/000177813126000022/primary_doc.xml) | 2026-06-30 | 706 | $12,608,161,670 |
| [0001778131-26-000023](https://www.sec.gov/Archives/edgar/data/1778131/000177813126000023/primary_doc.xml) | 2026-09-30 | 746 | $13,148,604,808 |

This is primary-source evidence for four of the 14 accessions in the candidate cohort (4/14, 28.57%). The other ten candidate-CIK accessions have not been individually adjudicated from their primary SEC documents in this phase. The separate accession `0001046192-26-000018` remains unverified. Do not extrapolate the four-document result to all 15 events.

The filings' statement that no other report information changed supports treating the corrected rows as value-field restatements rather than new position decisions. I did not perform a byte-for-byte comparison of every original and amended information-table row; that remains a separate reproducibility task.

## 3. Why the unit error matters

[SEC EDGAR Release 22.4.1](https://www.sec.gov/filergroup/announcements-old/edgar-release-2241), dated December 30, 2022, states that the January 3, 2023 release changed the Form 13F Appendix B value unit from thousands to the nearest dollar.

The older [SEC Form 13F FAQ](https://www.sec.gov/files/divisions/investment/13ffaq.htm) still displays the legacy “Value (x1000)” convention. This is a documentation-version conflict, not a reason to ignore the dated schema/release change. A reproducible parser must version its unit rule by filing date/schema, preserve the raw filed value, and record the normalization basis.

A concrete Q3 2026 example is informative. The original filing `0001778131-26-000008` shows 746 table entries and a summary value total of 13,148,608 under the legacy thousands convention; the later restatement `0001778131-26-000023` shows the same 746 entries and a nearest-dollar total of 13,148,604,808. The amendment's own statement says no other report information changed. The original-parent mapping is still secondary-index-only in this audit, and the totals are not a substitute for a row-level comparison.

## 4. Quantitative interpretation

- Four primary-verified amendments are value-unit restatements, not four new trades, not four independent managers and not a new holdings signal.
- The 14-accession batch should be treated as a candidate single-filer reporting-remediation event, not 14 independent institutional observations.
- The corrected dollar values must not be backdated to the original filing's public-availability timestamp.
- Position counts/share quantities may remain usable from the original vintage only after preserving the source's actual fields and validating the filing's “no other information changed” assertion; market-value fields require explicit unit/version treatment.
- Do not infer that every `RESTATEMENT` is value-only. Other SEC amendments can add or change holdings. The amendment checkbox, narrative, original filing and information-table diff must be adjudicated together.

**Decision:** `CLASSIFY_AS_VALUE_UNIT_RESTATEMENT_NOT_NEW_POSITION_SIGNAL` for the four verified filings. Keep all 15 current feed events metadata-only; research-eligible = 0; signal-eligible = 0.

## 5. Next gates

1. Primary-verify the remaining ten candidate-CIK filings and `0001046192-26-000018`.
2. Retrieve original and amended information tables and diff by CUSIP, class, put/call, share or principal amount, discretion, manager and value.
3. Build a general amendment taxonomy: value-unit-only, restatement with position changes, add-only, other/unclear.
4. Preserve filing vintages, accepted/first-seen bounds and schema-versioned value units; never overwrite the historical public state with a later correction.
5. Scan other managers' post-2023 amendments for the same legacy-thousands error before relying on 13F market-value weights.

No prices or post-event returns were inspected. No event study, OOS, bootstrap or LOO test was run. Holdout untouched. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No data purchased; spend USD 0.

## 6. Repository records

- Machine-readable audit: `PHASE667_SEC_13F_VALUE_UNIT_RESTATEMENT_PRIMARY_AUDIT_2026-11-27.json`
- State addendum: `SMART_MONEY_RESEARCH_STATE_ADDENDUM_2026-11-27_PHASE667.md`
- Parent Phase 666 audit remains immutable in PR #255.

## 7. Source-run logs and artifact contents

I downloaded and inspected artifact [15212890251](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46026323554/artifacts/15212890251). The 873-byte ZIP contains exactly one file, `poll_summary.json` (3,456 uncompressed bytes). The live job log confirms all four feeds completed with full-snapshot boundaries, zero page errors, zero same-feed or cross-feed duplicates, and a successful append-only metadata write.

The artifact reports 15 new accessions and 15 bounded metadata observations, but research eligible = 0 and signal eligible = 0. It explicitly records `filing_xml_or_text_downloaded=false`, `holdings_rows_downloaded=false`, `raw_transaction_rows_persisted=false`, and `public_availability_certified=false`. Thus the capture artifact itself does not contain the primary filings or holdings; the four primary XML verifications in this phase came from separate SEC filing-document sources. This distinction is retained in the audit.
