# Phase 509 — SEC Form 144 structured proposed-sale detail parser and PIT ledger (2026-11-19)

## Executive result

Phase 509 ports the previously audited Phase 65 Form 144 section parser into the prospective Phase 403 first-seen collector and adds a separate append-only structured-detail ledger. It preserves four distinct concepts:

1. securitiesInformation: proposed-sale tranches;
2. securitiesToBeSold: acquisition lots;
3. securitiesSoldInPast3Months: historical completed sales reported by the filer;
4. filing-level context: issuer/filer/seller, relationships, notice date, prior accession, remarks, no-prior-sales flag, plan-adoption dates and signature.

The parser does not infer that a proposed sale was executed, does not classify a seller as informed, does not normalize the reported outstanding-share denominator, and does not authorize a signal.

## Preflight

- Main before Phase 509: b93034c249f7c5679429e4e192b307b211a379df.
- Latest reviewed scheduled Form 144 capture: [Run 44614323236](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44614323236), completed successfully.
- Both Form 144 feeds responded; 28 new Form 144 events were appended and 28 acceptance reconciliations were resolved. Form 144/A had no new accession and its previous interval remains unbounded due to an earlier poll gap.
- The prospective ledger contained 378 event accessions after the capture (350 pre-existing rows plus 28 new events).
- The 28 new Form 144 filings covered 24 issuer CIKs. Two issuers repeated: Hyliion Holdings Corp. (4 filings) and Amdocs Limited (2). Nine filings had non-empty remarks: five explicitly referred to tax-obligation/withholding context, three to a trust/account or managing-member context, and one identified a filing agent. These are literal document descriptions, not verified execution classifications or alpha.
- The current static 290-CIK manifest is not the historical F80 security master.
- No active Actions run was found in the latest inspected run window. PR #159 remains a separate draft/conditional FINRA Short Interest item. No live workflow was started or duplicated.

## Historical parser precedent — do not repeat Phase 67

Phase 67 already parsed 21,634 candidate issuer events from 14 quarters (2023Q2–2026Q3) in artifact 13334881835. Phase 397 audited that artifact and documented 188 multi-tranche events, 291 multi-ticker candidate rows, 1,424 rows with a 10b5-1 mention, and a small set of numeric/denominator exceptions. The Phase 67 data are not a historical F80 security master and do not establish historical ticker/class membership or first-public-receipt timestamps.

Phase 509 therefore does not rerun the 14-quarter census. It addresses a separate gap: the current prospective first-seen collector stores filing-level metadata but not a structured detail ledger for the newer prospective events.

References:
- [Phase 397 PIT/data integrity audit](https://github.com/jafelix81/NuevaEstrategia/blob/main/research/PHASE397_FORM144_PIT_CLOCK_AND_EVENT_INTEGRITY_2026-11-14.md)
- [Phase 67 full candidate resolution report](https://github.com/jafelix81/NuevaEstrategia/tree/phase67-form144-full-candidate-role-resolution)

## Parser and ledger design

New module: research/phase509_form144_structured_detail_parser.py.

New ledger: research/data/sec_form144_first_seen/sale_details.csv.

The long-form ledger writes one filing-header row plus zero or more rows for each section. It retains raw source strings and separate numeric/date parses. Multiple securities, acquisition lots and prior sales are never collapsed into one row.

### Temporal and semantic controls

- The event's original first-seen interval, poll-response upper bound and poll run ID are copied unchanged into each detail row.
- Filing acceptance, Atom updated, notice date and approximate sale date remain separate clocks.
- The original event XML hash is compared with the re-fetched XML hash during backfill. A mismatch is recorded as source_hash_mismatch; it is not promoted. Backfill eligibility uses the stored XML hash rather than the older identity-parser status, so hash-bearing legacy rows with a prior identity parse error can still be retried; hash mismatches are counted separately.
- Numeric parsing uses decimal strings (including parenthetical negatives and currency punctuation), not binary floats. Date parsing accepts the formats audited in the Phase 65 parser, including two-digit-year and timestamp forms; unrecognized values remain missing.
- The backfill is capped at 10 previously captured events per hourly Phase 403 run, newest-first. New filings are parsed from the same XML retrieval already used by the collector, avoiding a duplicate request for those new events.
- Full filing XML is not persisted. Only normalized fields, source hashes, parser version and the original event clocks are retained.
- units_outstanding remains a raw reported field. No shares-outstanding ratio is computed because unit/scale semantics were previously not established.
- approx_sale_date_relation_to_notice is only a date comparison (before/same/after/unknown). It is not a claim that a sale executed.
- mentions_10b5_1_in_remarks is lexical only. Plan-adoption dates are preserved separately; neither field proves an active plan or directional intent.
- A 144/A retains its own accession and previous-accession reference. It is not counted as an independent new sale event by default.
- All detail rows have signal_eligible=false, public_availability_certified=false, and same_day_intraday_use_authorized=false.

## Validation scope

The new parser tests use synthetic XML fixtures for:
- multiple proposed-sale tranches and brokers;
- separate acquisition lots and realized prior-sale rows;
- namespaced tags and multi-valued issuer relationships;
- numeric/date missingness and invalid values;
- Form 144/A parent accession normalization;
- approximate-sale-date versus notice-date comparison;
- source-hash mismatch fail-closed behavior;
- append-only idempotency and separation of row types.

The existing Phase 403 regression suite also asserts that the live metadata fetch invokes the structured parser. Pull-request CI is offline-only: the live-capture job is not run for a pull request. The next existing hourly scheduled Phase 403 run will exercise the integrated code after merge; no extra workflow is needed.

## Research disposition

Data extraction gate advanced; alpha remains untested and unauthorized.

The 28-event sample shows why filing-level text alone is insufficient: several notices describe tax-withholding or trust/account context, and multiple sellers can file for the same issuer on the same day. The next useful unit of analysis is issuer-security-day with separate seller/tranche rows, not raw accession count.

Before any event study:
1. Reconcile XML subject issuer CIK and security class to a point-in-time security master, including delisted/predecessor names.
2. Link 144/A to the correct parent using issuer, seller, security class and accession lineage; amendments must not become independent observations.
3. Distinguish proposed-sale tranches from prior completed-sale disclosures and from sales that may already have occurred by notice date.
4. Establish first executable session from the conservative first-seen upper bound and retain next-session-only execution.
5. Validate units, corporate actions and any market-value normalization using only information available at the event time.
6. Accumulate a sufficiently broad prospective sample before testing proposed supply pressure incrementally against frozen LTM/F80 with identical exposure/costs, chronological validation, issuer clustering, block bootstrap and issuer LOO.

No forward returns, event study, backtest, OOS, bootstrap, LOO or holdout test was run. No signal was admitted. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

Parser status vocabulary: parsed (source hash matches), parsed_unverified_hash (legacy event has no original hash), source_hash_mismatch (re-fetched XML differs and is excluded from feature use), and parse_error (XML structure could not be parsed). A fetch failure without XML bytes remains uncompleted and may be retried in a later bounded batch.

The numeric/date normalization has been cross-checked against the Phase 65 field-coverage parser; Decimal strings are retained to avoid float rounding, while unrecognized source formats remain null rather than coerced.
