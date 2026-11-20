# Phase 525 — SEC Form 144 / Form 4 matched-event audit and filing-level owner identity (2026-11-20)

## Decision

Two high-confidence Atea Pharmaceuticals (AVIR) proposed-sale records in the current Form 144 detail sample match Form 4 sale transactions on issuer CIK, owner, transaction date and exact share count. A third match links a Form 144 prior-sale-history row to a Form 4 sale. The Form 4 remarks describe the sales as related to option exercise price and tax planning. These are useful event-semantics examples, not evidence of discretionary bearish insider selling or predictive alpha.

The current Form 4 parser preserves owner count but not reporting-owner identity. Phase 525 adds an append-only filing-level owner/remarks sidecar and a conservative crosswalk. It never maps multi-owner filings to transaction lines. No signal, return test or model change is authorized.

## Preflight and latest scheduled captures

Main HEAD at preflight: \`74ae49d3a17e8dce424d5fd5722d0bd49d2c2c65\` (Phase 524). The latest Actions list was inspected before edits; no active or queued run was present. The latest SEC runs were:

- Form 4 [44716430351](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44716430351), scheduled, success.
  - Two feeds succeeded; 33 new accession metadata events; no feed/page errors; 38 same-feed duplicate occurrences were suppressed; no cross-feed duplicates or incomplete-poll candidates were admitted.
  - Ten bounded filings were structurally parsed: 37 detail rows (10 headers and 27 transaction rows), zero parse errors; 1,213 bounded accessions remained at that run.
  - Current committed ledger: 1,268 first-seen accessions; 20 structured accessions; 59 detail rows, including 39 transaction rows. Eighteen structured filings are single-owner; two are multi-owner and remain quarantined from line-level attribution.
- Form 144 [44720422923](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44720422923), scheduled, success.
  - Both 144 and 144/A feeds succeeded; 52 feed-observation rows were persisted; no live-feed errors or possible window gap; zero new accessions in this poll.
  - Ten bounded filings were backfilled: 64 detail rows, zero parse errors; 358 structured accessions remained.
  - Current committed ledger: 448 first-seen accessions; 90 structured accessions; 660 detail rows: 90 proposed-sale rows, 288 prior-three-month sale rows, and 282 filing/security-section rows. All 660 detail rows have matching source/event XML hashes.
  - The offline regression log contains an intentionally simulated 144/A timeout fixture for partial-poll behavior. It is not a live-capture feed failure.

The Form 4 live run had already completed before this phase began. No manual capture or duplicate dispatch was started.

## Cross-source audit of committed data

The current detail sample contains 90 Form 144 proposed-sale rows across 71 issuer CIKs and 39 Form 4 transaction rows across 16 issuer CIKs. Only one issuer CIK overlaps in the two structured samples (Atea Pharmaceuticals, CIK 0001593899). Within that issuer there were 14 issuer-level row comparisons, eight same-date pairs and two exact proposed-sale matches on date and share quantity. These counts are descriptive of the bounded, newest-first parser samples, not population coverage.

### Proposed-sale matches

| Form 144 | Seller | Proposed date / shares | Form 4 | Transaction | Form 4 gross value vs Form 144 reported value |
|---|---|---:|---|---|---:|
| 0001950047-26-011348 | Bruce Polsky | 2026-11-19 / 8,750 | 0001193125-26-469037 | S / D, 8,750 @ $4.0341 | $35,298.375 vs $35,299.25 (difference +$0.875) |
| 0001950047-26-011363 | Bruno Lucidi | 2026-11-19 / 22,619 | 0001193125-26-469038 | S / D, 22,619 @ $3.9445 | $89,220.6455 vs $89,219.37 (difference -$1.2755) |

The reporting-owner names and CIKs are corroborated by the issuer's filing index and independent filing-level views. The Form 4s identify Bruce Polsky (owner CIK 0001508458) and Bruno Lucidi (owner CIK 0001829622), respectively. The Form 144 filer CIKs in the structured ledger match those owner CIKs.

### Prior-sale-history match

The Bruno Lucidi Form 144 also reports 6,741 shares sold on 2026-11-17 for gross proceeds of $27,189.82. Form 4 accession 0001193125-26-469038 reports a matching S / D sale of 6,741 shares at $4.0335; calculated gross is $27,189.8235, a $0.0035 difference. This is a match to the Form 144 *prior sales* section, not a second proposed sale.

The Bruce Polsky Form 144 lists three additional prior sales (18,252 on Nov 18; 8,720 on Nov 17; 14,254 on Nov 16). Those transactions are not present in the current 39-row Form 4 structured sample; absence from this partial sample is not evidence that no Form 4 exists.

### Timing: not a proven leading signal

- Polsky Form 144 acceptance: 2026-11-19 21:17:53Z. Matching Form 4 acceptance: 2026-11-20 02:51:07Z (5h 33m 14s later).
- Lucidi Form 144 acceptance: 2026-11-19 21:38:14Z. Matching Form 4 acceptance: 2026-11-20 02:51:12Z (5h 12m 58s later).
- Both Form 144s have first-seen upper bound 2026-11-20 02:39:27Z; the Form 4 first-seen upper bound is 2026-11-20 10:07:15Z.

The Form 144s were accepted before the Form 4s, but both report a Nov 19 sale date and neither source supplies the intraday execution timestamp. Therefore the ordering of public filing acceptance does **not** prove the Form 144 preceded execution. Classify these as \`FORM144_ACCEPTED_BEFORE_FORM4_ACCEPTANCE_EXECUTION_TIME_UNKNOWN\`, not as pre-trade predictive events. The first-seen timestamps are polling upper bounds, not exact receipt times.

### Economic context

The Form 4 remarks for both Atea filings state that sale transactions were executed to pay option exercise prices and for tax-planning purposes. Lucidi's filing also contains option-exercise (M) rows alongside the S / D sales. This is a material confounder: a code-S disposition is not automatically a discretionary bearish view. The new sidecar captures filing-level remarks and conservative phrase flags; flags are descriptive, not definitive economic labels.

A separate prior Phase 524 case remains useful: Clean Energy Fuels (CLNE) Form 4 reported a 100,000-share sale on Nov 10 and was filed Nov 12, while a matching Form 144 was filed Nov 19. That is a post-trade notice case, not a leading sale-intent signal. The CLNE Form 4 is not in the current 20-accession structured Form 4 sample, so it is retained as external case evidence rather than a current ledger match.

## Phase 525 implementation

1. \`phase525_form4_reporting_owner_identity.py\` parses the public Form 4 XML reportingOwner blocks into an append-only \`reporting_owners.csv\` sidecar. It stores owner CIK/name, relationship flags, filing-level remarks, remarks hash and separate first-seen/acceptance clocks. It does not store owner addresses.
2. Single-owner filings are explicitly labelled \`SINGLE_REPORTING_OWNER_FILING_GRAIN_ONLY\`. Multi-owner filings retain their owner identities but remain \`MULTI_OWNER_FILING_GRAIN_ONLY_NO_LINE_LINK\`; no owner order, signature order or proximity is used to assign a transaction line.
3. \`phase525_form144_form4_crosswalk.py\` matches only on issuer CIK, Form 144 filer/owner CIK, normalized owner name, transaction date, exact shares, security class, and Form 4 S / D disposition. It separately labels proposed-sale and prior-sale-history matches. Price/gross-value differences are retained as diagnostics, not used as a loose match key.
4. The Form 4 workflow runs a bounded ten-filing owner-identity enrichment after its existing structured-detail backfill, then emits a descriptive crosswalk artifact. It persists only the owner sidecar; crosswalk output is an artifact, not a mutable research ledger.
5. The owner enrichment selects the oldest still-unenriched, bounded, already-parsed filings first so new hourly backfill does not starve the existing 20-filing backlog.

## Data and inference gates

- The current Atea issuer CIK is not verified as a historical F80 member in the Form 144 event ledger. These matched examples are not eligible for F80 feature testing.
- Form 4's current schema does not link transaction lines to owners in multi-owner filings. Those filings remain quarantined.
- EDGAR acceptance and poll first-seen bounds are separate clocks; neither is treated as exact public receipt without evidence.
- Form 144 \`approx_sale_date\` is used only to reconcile against a Form 4 transaction date, never as the event-availability timestamp.
- Form 144 prior sales and proposed sales are distinct event roles. A Form 144/A amendment or plan termination is not automatically a new forward sale.
- Remarks flags are filing-level text cues. They do not establish motive for each transaction line.
- No raw XML is committed. The sidecar retains XML hashes and source provenance.

## Disposition

- Two exact proposed-sale candidates and one exact prior-sale-history match are identified in the current overlapping Atea sample.
- The owner-identity sidecar is new and will be populated by subsequent scheduled runs; the current matches are independently corroborated but are not yet reproducible from the sidecar.
- No signal admitted; no event/return study, backtest, OOS, bootstrap, LOO or holdout test run.
- \`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen. No exposure, cost, universe, holdout or production change.
