# Phase 659 — SEC Form 4/A original-accession lineage resolution

**Audit date:** 2026-11-27  
**Mainline input:** `642045a8177e514ea700857b00a5e38c90d90609`  
**Inputs:** `research/data/sec_form4_first_seen/transaction_details.csv` and `reporting_owners.csv`  
**Disposition:** two original-accession links resolved from SEC primary filings; no new economic event or signal admitted.

## Executive finding

Phase 658 identified two Form 4/A accessions whose `previous_accession` field was blank. The original filings are now resolved from the SEC primary filing indexes and ownership XMLs:

| Issuer | Amendment accession | Original accession | Filing dates | Rows in amendment |
|---|---|---|---|---:|
| Crescent Private Credit Income Corp. | `0001104659-26-130067` | `0001104659-26-105049` | 2026-11-19 / 2026-09-03 | 1 |
| Tron Inc. | `0001493152-26-053612` | `0001493152-26-015786` | 2026-11-23 / 2026-04-08 | 4 |

The five rows in the two amendments are **not five new economic events**. Crescent is a final-NAV update to the same September 1 investment; TRON adds a joint reporting person and repeats four previously reported award/exercise/conversion rows.

## 1. Crescent: final NAV values, same September 1 investment

The original Form 4 reports one P/A transaction on 2026-09-01 with 208,279.91 shares at USD 26.33. Its footnote says those figures were estimates because the issuer's NAV calculation was not final. The Form 4/A reports 207,178.32 shares at USD 26.47 and states that the final transaction information is supplied after definitive NAV calculation.

| Field | Original Form 4 | Form 4/A |
|---|---:|---:|
| Transaction date | 2026-09-01 | 2026-09-01 |
| Code / acquired-disposed | P / A | P / A |
| Shares | 208,279.91 | 207,178.32 |
| Price per share | USD 26.33 | USD 26.47 |
| Implied row value | USD 5,484,010.03 | USD 5,484,010.13 |
| Reported combined investment | USD 5,484,010 | USD 5,484,010 |

The implied values differ by USD 0.10 because the share count and price were finalized. Both round to the same reported combined investment. This is a state/value update, not a second purchase. Code P remains ambiguous between open-market and private purchase. The issuer's symbol is N/A, so this record is not an F80 equity event in any case.

Primary sources:
- [Original SEC filing index — 0001104659-26-105049](https://www.sec.gov/Archives/edgar/data/2097963/000110465926105049/0001104659-26-105049-index.htm)
- [Original SEC ownership XML](https://www.sec.gov/Archives/edgar/data/2097963/000110465926105049/tm2624773-2_4seq1.xml)
- [Amended SEC ownership XML](https://www.sec.gov/Archives/edgar/data/2098163/000110465926130067/tm2630207-1_4aseq1.xml)

## 2. TRON: joint-owner addition, no transaction changes

The original Form 4 was filed on 2026-04-08 by Sun Weike (CIK 0002075156). The Form 4/A was filed on 2026-11-23 and adds Bravemorning Ltd (CIK 0002075159) as a joint reporting person. The amendment expressly states it is filed solely to add Bravemorning and that no other changes are made.

All four transaction rows are identical between the original and amended documents:

| Table | Date | Code | Security | Shares | Price | Acquired/disposed |
|---|---|---|---|---:|---:|---|
| Non-derivative | 2025-08-27 | A | Common Stock | 220,000,000 | USD 0.50 | A |
| Non-derivative | 2026-04-02 | A | Common Stock | 200,000,000 | USD 0.50 | A |
| Derivative | 2025-08-27 | M | Common Stock Purchase Warrants | 220,000,000 | USD 0.00 | D |
| Derivative | 2026-04-02 | M | Series B Convertible Preferred Stock | 200,000,000 | USD 0.00 | D |

The filing footnotes tie these rows to the June 2025 PIPE, warrant exercise and preferred-stock conversion, with consideration paid in TRX. Codes A and M describe award/acquisition and exercise/conversion—not open-market purchases. Counting the four repeated amendment rows as new bullish insider flow would be a material event-construction error.

Primary sources:
- [Original SEC filing index — 0001493152-26-015786](https://www.sec.gov/Archives/edgar/data/2075156/000149315226015786/0001493152-26-015786-index.htm)
- [Original SEC ownership XML](https://www.sec.gov/Archives/edgar/data/2075156/000149315226015786/ownership.xml)
- [Amended SEC ownership XML](https://www.sec.gov/Archives/edgar/data/2075156/000149315226053612/ownership.xml)

## 3. Reproducible result

The offline audit checks the two amendment headers, all five current transaction rows, the amendment reporting-owner CIK sets, and the source-level lineage adjudications. It does not mutate the source ledger.

| Measure | Result |
|---|---:|
| Current Form 4 filing headers | 140 |
| Current transaction rows | 276 |
| Original-accession links resolved | 2 |
| Amendment rows reviewed | 5 |
| New economic events created | **0** |
| Signal-eligible rows | **0** |

The append-only resolution sidecar is `research/data/sec_form4_first_seen/amendment_lineage_resolutions.json`. The source ledger's blank `previous_accession` fields remain unchanged; the resolved links live in the sidecar until a separately reviewed schema migration is justified.

## 4. Point-in-time and strategy controls

- The original filings predate the current collector's first-seen coverage and are not present as original accessions in the 140-header ledger.
- SEC index acceptance metadata is not treated as exact public availability. No historical first-seen timestamp is backfilled from filing date or acceptance time.
- Neither amendment is promoted as a new event; the Crescent P code does not establish execution venue, and TRON's A/M rows are not market buys.
- No prices or forward returns were inspected. No event study, OOS, bootstrap, LOO or holdout test was run.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No SEC network requests were made by the offline audit, no paid data or vendor contact occurred, and the data budget remains USD 0.

## Reproduction

```bash
python -m unittest -v research.test_phase659_form4_amendment_lineage_resolution
python -m research.phase659_form4_amendment_lineage_resolution \
  --transactions research/data/sec_form4_first_seen/transaction_details.csv \
  --owners research/data/sec_form4_first_seen/reporting_owners.csv \
  --sidecar research/data/sec_form4_first_seen/amendment_lineage_resolutions.json \
  --output phase659_output/summary.json
```
