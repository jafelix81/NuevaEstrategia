# Phase 195 — Cboe Option Trades condition and exchange reference mapping audit

**Audit date:** 2026-11-07  
**Disposition at commit:** hosted mapping retrieval pending  
**Scope:** official current reference mappings reconciled to the one-day 2026-01-07 public sample.

## Why this gate is necessary

Phase 194 established that the public sample can be parsed into daily NBBO-side measurements, but trade-condition IDs were counted without interpretation. A trade print at bid/ask is not automatically eligible for a signed-flow feature: late, out-of-sequence, auction, complex, correction and other special-condition trades can have different economic meaning.

Cboe DataShop exposes public reference files for LiveVol trade-condition IDs and exchange IDs. LiveVol's API documentation describes a message-condition reference mapping numeric IDs to a condition name, message type and applicable security types; the API endpoint itself requires OAuth authorization, so this phase uses only the public DataShop reference files and does not create an account or request credentials.

## Method

- Download the official trade-condition XLSX, exchange-ID CSV and the same public sample archive.
- Hash each downloaded file and retain response metadata.
- Parse XLSX shared strings, workbook relationships and all readable sheets using Python standard library only.
- Identify the mapping header by explicit ID/name columns; do not assume a worksheet or column order.
- Count observed trade-condition and exchange IDs in both 19-column and 25-column sample members; require the ID distributions to match.
- Reconcile every observed ID to the official current mapping.
- Classify descriptions conservatively: regular/normal, complex/spread, auction/cross, late/out-of-sequence, cancel/correction, extended hours, or unclassified.
- Mark a condition as a candidate side-eligible trade only if the mapping explicitly says Regular/Normal, message_type=trade and security_types includes option. A name-only match is insufficient.
- Detect effective-date fields in the mapping. Their absence means the current mapping cannot be assumed valid for historical samples.
- Persist hashes, IDs, descriptions and aggregate counts only. No raw sample rows, symbols, contracts or mapping workbook bytes are stored.

## Known source caveats

The published Option Trades file specification describes market_date as YYYY-MM-DD and quote_datetime as a full YYYY-MM-DD HH:MM:SS.000 timestamp. The public sample instead uses M/D/YYYY and a seven-character time-only field. Phase 194 quarantines that field; this mismatch remains unresolved and must not be silently normalized into an intraday timestamp.

The product page/FAQ advertise historical coverage, but the public sample is one day and one underlying. It does not prove daily completeness, inactive/delisted coverage, first file receipt or historical condition-map versions.

## Hosted execution result

**MAPPINGS_RECONCILED — 11/11 tests passed.** Workflow [42418568678](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42418568678) downloaded all three public files successfully and uploaded a metadata-only artifact.

- The current trade-condition workbook contains 80 IDs and only three columns: id, name and security_type. SHA-256: 23c94bd8d16229c8ce462a1e351636821670932553c66e84046797275a74cc65. Last-Modified: 2026-10-08 20:33:43 GMT.
- The exchange mapping contains 40 IDs. SHA-256: 1b5cab0414cdc96aee6f2cfea098d36c12a4f7d06b7ad15909e3370b90d3c87f. Last-Modified: 2026-10-29 20:48:45 GMT.
- All 15 trade-condition IDs observed in the sample and all 18 exchange IDs were mapped; both sample members had identical condition/exchange ID distributions. The mapping workbook has no message_type field and no effective-date columns.
- The sample's 74,999 rows had canceled_trade_condition_id=0 throughout.

### Observed condition mix

| Condition ID | Current mapping name | Rows | Share |
|---:|---|---:|---:|
| 18 | AutoExecution | 40,334 | 53.78% |
| 95 | IntermarketSweep | 2,165 | 2.89% |
| 114 | SingLegAuctNonISO | 20,070 | 26.76% |
| 115 | SingLegAuctISO | 20 | 0.03% |
| 116 | SingLegCrossNonISO | 1 | 0.00% |
| 118 | SingLegFlr | 14 | 0.02% |
| 119 | MultLegAutoEx | 4,659 | 6.21% |
| 120 | MultLegAuct | 6,385 | 8.51% |
| 122 | MultLegFlr | 15 | 0.02% |
| 123 | MultLegAutoSingLeg | 1,258 | 1.68% |
| 124 | StkOptAuct | 23 | 0.03% |
| 125 | MultLegAuctSingLeg | 4 | 0.01% |
| 126 | MultLegFlrSingLeg | 10 | 0.01% |
| 127 | StkOptAutoEx | 40 | 0.05% |
| 129 | StkOptFlr | 1 | 0.00% |

Grouped descriptively, single-leg auction/cross prints account for 20,091 rows (26.79%), multi-leg prints 12,331 (16.44%), stock-option prints 64 (0.09%), and single-leg floor prints 14 (0.02%). These names are execution-mechanism labels, not participant identities. AutoExecution is not assumed to mean an uninformed or institutional trade; IntermarketSweep is not treated as ordinary flow.

### Exchange coverage in this sample

All 18 observed exchange IDs mapped. The five largest by row count were CBOE 8,686; ARCA 8,204; PHLX 7,830; MIAX 7,563; and AMEX 7,320. This confirms multi-venue content for this one-underlying sample only, not broad underlying-universe coverage.

### Important limitations

The public XLSX does not expose message_type, although the LiveVol API's message-condition reference describes that dimension as trade versus quote and includes security_types. The API endpoint requires OAuth; no account was created and no credentials were requested. The observed column is trade_condition_id in a trade file, but the audit does not invent the missing reference metadata.

The mapping files were last modified after the sample date (2026-01-07), and contain no effective-date fields. They cannot prove that the same IDs/names applied historically. The public mapping therefore supports descriptive labeling, not historical PIT eligibility. No observed condition passed the strict Regular/Normal + trade + options rule; the candidate side-eligible set is empty.

### Admission decision

Phase 194's -36,763 contract at-ask-minus-at-bid proxy pools automatic executions, ISO, single-leg auctions, multi-leg and stock-option executions. Phase 195 shows why that aggregate cannot be called clean directional flow. Keep the conditions separate; do not infer beneficial owner, institutional status or informed trading. A next step may measure NBBO-side imbalance separately by condition as a one-day descriptive sensitivity, but it is not a return test.

A complete current mapping is a measurement-quality improvement, not PIT admission. Before any historical signed-flow test, require effective-dated condition mappings, correction/cancel semantics, adjusted-deliverable treatment, first file receipt and broad historical sample coverage. No signed-flow feature, stock/option return test, holdout use or production change is authorized. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
