# Phase 658 — SEC Form 4 live-ledger integrity and amendment-state audit

**Audit cutoff:** 2026-11-27 05:22 UTC  
**Mainline source:** 642045a8177e514ea700857b00a5e38c90d90609  
**Input:** research/data/sec_form4_first_seen/transaction_details.csv · Git blob a314421b76333f050a3228071025e448ac8ca840  
**Disposition:** data-integrity and event-lineage audit only; no signal or alpha admitted.

## Executive finding

The current live ledger contains **140 filing headers and 276 transaction rows**. A new source-level inconsistency appears in one Form 4 purchase row for SHMD: the filing header says the period of report and earliest transaction are in November 2026, but its Table I row reports a transaction date in November 2006 and a price per share of **USD 1,731,429** for 60,000 shares. The SEC-rendered primary document displays those same values, so this is not a date or decimal transformation introduced by the repository parser. The row must be quarantined from transaction-value aggregation and signal review while preserving the source unchanged. [SEC primary document](https://www.sec.gov/Archives/edgar/data/1987240/000212566726000005/xslF345X06/primary_doc.xml)

A second issue is event lineage: the ledger has two Form 4/A accessions, five transaction rows, and no stored original-accession link for either amendment. The filings show why amendments cannot be counted as new trades merely because they carry transaction rows.

## 1. Current ledger census

| Measure | Result |
|---|---:|
| Filing headers | 140 |
| Transaction rows | 276 |
| Form 4 | 138 |
| Form 4/A | 2 |
| Distinct normalized issuer-symbol strings | 98 |
| Single-owner filing-grain rows | 261 |
| Multi-owner rows quarantined from line attribution | 15 |

Transaction-code rows:

| Code | Rows | Distinct accessions | 10b5-1 affirmative rows | 10b5-1 negative rows |
|---|---:|---:|---:|---:|
| P | 86 | 56 | 11 | 75 |
| S | 63 | 33 | 30 | 33 |
| A | 66 | 29 | 0 | 66 |
| M | 30 | 11 | 4 | 26 |
| F | 7 | 7 | 0 | 7 |
| G | 7 | 6 | 0 | 7 |
| J | 9 | 8 | 0 | 9 |
| X | 2 | 1 | 0 | 2 |
| C | 6 | 3 | 0 | 6 |

The 10b5-1 counts above are transaction-row counts carrying a filing-level flag, not independent owners or trades. SEC code P means **open-market or private purchase**, and S means **open-market or private sale**; neither code alone establishes execution venue. A means grant/award or other Rule 16b-3(d) acquisition, M means exercise/conversion, and F can represent exercise-price or tax-liability payment. These codes must not be collapsed into a generic bullish/bearish insider-flow variable. [SEC transaction-code definitions](https://www.sec.gov/edgar/searchedgar/ownershipformcodes.html)

## 2. Source-level chronology and price anomaly: SHMD

Accession **0002125667-26-000005**:

- SEC filing date: 2026-11-25.
- Period of report: 2026-11-24.
- Header's earliest transaction date: 11/24/2026.
- Table I row: 11/25/2006, code P, 60,000 shares acquired.
- Table I price field: USD 1,731,429 per share.

The transaction date is **7,304 days before** the period-of-report date; the filing date is 7,305 days after the reported transaction date. The price field also crosses the USD 10,000-per-share manual-review threshold. Both checks point to the same row.

The filing itself is internally inconsistent. The collector parser faithfully recorded the source row; changing the parser's date or price would conceal the source defect. The audit therefore preserves the raw row, flags it, and excludes it from any derived dollar-value calculation until the issuer's filing is corrected or independently reconciled. No correction is inferred.

## 3. Amendments are state updates, not automatically new trades

Both Form 4/A accessions have is_amendment=true, but the current transaction ledger's previous_accession field is blank. The five repeated transaction rows are not sufficient evidence of five new economic events.

### Crescent Private Credit Income Corp — accession 0001104659-26-130067

Filed 2026-11-19; period of report 2026-09-01; original filing date stated as 2026-09-03; five reporting persons; issuer symbol shown as N/A.

The amended filing reports 207,178.32 Class I shares at USD 26.47 and explains that the final share count and price could not be determined at the original filing because the issuer's NAV calculation was not final. It reports a combined additional investment of USD 5,484,010. This is a final-value update to the September 1 investment, not a second purchase on November 19. The five-person filing remains quarantined at filing grain. [SEC primary document](https://www.sec.gov/Archives/edgar/data/1626970/000110465926130067/xslF345X06/tm2630207-1_4aseq1.xml)

### Tron Inc. — accession 0001493152-26-053612

Filed 2026-11-23; period of report 2025-08-27; original filing date stated as 2026-04-08; two reporting persons; four repeated A/M transaction rows.

The amendment expressly says it is filed solely to add Bravemorning as a joint reporting person and that no other changes are made to the original Form 4. The repeated rows are an ownership-reporting update, not new trades. [SEC primary document](https://www.sec.gov/Archives/edgar/data/1956744/000149315226053612/xslF345X06/ownership.xml)

The current ledger correctly marks both filings as amendments and quarantines their multi-owner transaction rows, but it does not persist the original accession link. Future event construction must compare the amended state to its original filing and only emit a new economic event when a verified transaction-state delta exists.

## 4. Stale disclosure rows

Ten transaction rows across four accessions have more than 30 calendar days between the reported transaction date and the filing date:

- Crescent: one P/A row, 79 days; the amendment finalizes the NAV-based values of an earlier investment.
- BNAI: four A/M rows, 560, 485, 192 and 192 days. The SEC filing describes incentive-plan grants and an option exercise, not discretionary P/S trades. [SEC primary document](https://www.sec.gov/Archives/edgar/data/1838163/000149315226053593/xslF345X06/ownership.xml)
- TRON: four A/M rows, 453 and 235 days; an amendment-only ownership update.
- SHMD: one P row, 7,305 days; source-level date/price inconsistency.

The 30-day threshold is a stale-disclosure diagnostic, not a legal conclusion about filing timeliness. These rows must be timestamped by the conservative public/first-seen availability clock, never backdated to the transaction date for a tradable signal.

## 5. Eligibility and research decision

All **276/276** transaction rows remain ineligible under the current ledger flags for research observation, signal use, public-availability certification, same-day intraday use, security identity, historical F80 membership, owner attribution, transaction semantics and authorization as a new economic trade.

- No transaction was promoted.
- No incremental alpha was demonstrated.
- No market price series or forward returns were inspected.
- No event study, OOS, bootstrap, LOO or holdout test was run.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- No source rows were deleted or rewritten.

## 6. Next implementation gates

1. Add an append-only Form 4/A lineage sidecar with original filing date, original accession where independently verified, amendment purpose, and transaction-level before/after fingerprints including date, code, shares, price, ownership form and footnote references.
2. Keep amendments at state-update grain. Do not emit a new trade from repeated transaction rows unless the original-to-amended comparison proves a new or corrected economic event.
3. Add persistent review flags for transaction dates earlier than the period-of-report date and extreme per-share values. Preserve source values; never silently normalize or drop them.
4. Keep stale disclosures separate from contemporaneous transaction events and use the filing's conservative first-seen clock.
5. Continue the historical issuer/security-class/F80 membership and rights-cleared price gates before any event study.

## Reproduction

    python -m unittest -v research.test_phase658_form4_transaction_integrity_audit
    python -m research.phase658_form4_transaction_integrity_audit --transactions research/data/sec_form4_first_seen/transaction_details.csv --output-dir phase658_output

The Phase 658 workflow is offline-only. It makes no SEC requests and downloads no market data.
