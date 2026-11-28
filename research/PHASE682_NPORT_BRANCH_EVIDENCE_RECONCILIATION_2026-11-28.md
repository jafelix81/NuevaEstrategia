# Phase 682 — N-PORT branch evidence reconciliation and admission decision

**Audit cutoff:** 2026-11-28 UTC  
**Main base:** `d2045f02e8a924689503dd84cc5229ea99128a7f`  
**Disposition:** incorporate the verified Phase 313/314 N-PORT findings into the current research state without merging the old branch. N-PORT remains a conditional, delayed fund-positioning source; no signal or alpha is admitted.

## 1. Repository and workflow preflight

- Inspected the latest 100 Actions runs, explicit active/queued status, jobs, logs and artifacts for the current Form 144, Form 4, FINRA Reg SHO, CFTC TFF and 13F collectors. No active or queued run was found; no duplicate workflow was started.
- Current `main` before this note: `d2045f02e8a924689503dd84cc5229ea99128a7f`.
- The N-PORT evidence remains in the separate Phase 312/313 branch chain and PR #17. PR #17 is open and unmerged; its base is `phase312-nport-raw-stratified-sample`, not `main`.
- Current Phase 313 branch head: `7bc80f1aa7fca411389a4682abdb2adc2b645282`. Compared with `main`, it is 1,168 commits ahead and 712 behind, with merge base `dc99c7289340983241b031beba7c68c3ba35f0dc`. Do not merge this historical branch as a unit.
- Phase 314's run commit `a54975865e75c250dda011de9ab2626ab60de576` is an ancestor of the current Phase 313 branch head. Its hosted run and artifact remain independently inspectable.

## 2. Phase 313 — raw-sample identity correction

Phase 313 re-read the immutable 56-submission Phase 312 sample and verified all recorded raw submission hashes.

| Measure | Result |
|---|---:|
| Raw submissions re-read | 56/56 |
| Raw SHA-256 re-verified | 56/56 |
| Series header/XML identity matches | 53/56 |
| Class header/XML identity matches | 53/56 |
| Series/class mismatches | 0 |
| Series/class identifiers missing in both sources | 3/56 |

The correction was necessary because the SEC complete-submission header uses SGML-style values such as `<SERIES-ID>value` without a closing tag. The Phase 312 parser had required closing tags and therefore under-reported header/XML identity matches. Phase 313 corrected the parser and superseded those earlier labels; it did not change raw filings or holding values.

Hosted validation: [Phase 313 run 43160004366](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43160004366), 8/8 tests passed; [artifact 13916694212](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43160004366/artifacts/13916694212).

### Short-position sample — descriptive, not prevalence

The deterministic 56-filing sample contains 176 rows passing the narrow direct U.S. common-equity short filter. All 176 rows have valid CUSIP and ISIN check digits, but they are concentrated in only two filings:

- Otter Creek Long/Short Opportunity Fund, 2022-07-31 report: 20 rows, 20 reported tickers.
- Saba Capital Income & Opportunities Fund II, 2025-10-31 report: 156 rows, no reported tickers.

Across these two filings there are 173 unique CUSIPs and 173 unique ISINs. Only 6 of the 20 reported ticker strings match the frozen 335-name comparison list; the other 14 do not. The remaining 156 rows have no ticker and must remain `UNKNOWN_NOT_REPORTED`, not be counted as non-matches. This is a string-overlap diagnostic, not an effective-dated security-master or historical-universe coverage result.

## 3. Phase 314 — Otter Creek amendment lineage and position-vintage result

Hosted validation: [Phase 314 run 46006090277](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46006090277) succeeded; the `parent-audit` job completed and all 9/9 tests passed. [Artifact 15201951527](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46006090277/artifacts/15201951527) contains the 25 candidate original submissions and reconciliation outputs.

Target amendment:
- Accession `0001145549-22-060851`, NPORT-P/A.
- Registrant CIK `0000811030`; report date 2022-07-31; filed 2022-10-03.
- Series `S000043717`, Otter Creek Long/Short Opportunity Fund.
- 20 direct short-position rows under the preregistered filter.

Among 25 earlier NPORT-P candidates for the same registrant and 2022 Q3 search window, exactly one candidate matched the registrant CIK, report date, series, original form and earlier filing date:

- Original candidate `0001145549-22-059178`, filed 2022-09-28.
- Series and class identities match; 20 short rows.
- All 25 candidate submissions were downloaded and hashed; series and class identity matched in 25/25.

The relationship is classified `UNIQUE_METADATA_PARENT_CANDIDATE_NOT_AUTHORITATIVE`, not an authoritative parent-accession edge.

The original and amendment each contain 20 audited short rows. Comparison: **20 unchanged, 0 modified, 0 added, 0 removed**. The amendment therefore does not represent a second short-position event or a new trade.

A same-series 2023 control (accession `0001145549-23-060491`, report date 2023-07-31) contains 27 short rows; compared with the 2022 amendment, 4 were modified, 23 added, 16 removed and 0 unchanged. This is a comparison of disclosed snapshots, not a record of when positions were opened, covered, hedged or transferred.

Report-to-filing lags in the three audited vintages were 59, 64 and 60 calendar days. These are not verified first-public-receipt lags.

## 4. Point-in-time and economic interpretation

N-PORT has a useful measurement distinction from 13F: it can explicitly report certain non-derivative short payoff positions. It is still a delayed registered-fund holdings snapshot, not a market-wide short-interest series, securities-borrow tape, hedge-fund census, beneficial-owner record or executed transaction feed.

Keep the following clocks separate:
- `report_date`: portfolio measurement date;
- `filing_date` and SEC acceptance datetime: filing/availability metadata;
- prospective first-public receipt, if captured: actual collector knowledge-time bound;
- first full regular U.S. equity session whose open is strictly after the accepted filing: conservative daily execution boundary until a stronger release/receipt record is available.

The distinct short-side hypothesis remains the preregistered **change in short share quantity**, not raw change in short percent of NAV. It requires the same fund series and effective-dated security across consecutive publicly disclosed report vintages, verified corporate-action adjustments, and explicit short rows in both vintages. Missing rows remain unknown unless complete-filing and omission semantics are proven. An amendment is a new as-filed vintage, not a new trade.

The existing Phase 27O long-share-accumulation hypothesis was killed in its tested form. Do not reuse it as evidence against this distinct short-side hypothesis, but do not test the short-side hypothesis until the data gates below pass.

## 5. Admission decision and next gates

| Gate | Current disposition |
|---|---|
| Public quarterly archive history | Documented, 2019 Q4–2026 Q3 |
| Narrow short-row field/sign semantics | Verified in selected raw filings |
| Header/XML series/class identity | 53/56 in Phase 313; 25/25 in Phase 314 candidate set |
| Original/amendment relationship | Unique metadata candidate; not authoritative |
| Broad fund/series/year sample | Not representative; 176 rows concentrated in two filings |
| Effective-dated CUSIP/ISIN-to-U.S.-listing identity | Not established |
| Inactive/delisted and historical F80 coverage | Not measured |
| First-public receipt and full amendment-vintage history | Not established |
| Approved historical prices/corporate actions | Not established |
| Return/alpha/OOS/bootstrap/LOO | Not run or authorized |

Next work should prioritize a representative fund/series/year sample and an effective-dated security crosswalk. Preserve raw submissions and every amendment as separate immutable vintages. Only after those gates pass should the preregistered short-share-quantity hypothesis be considered for chronological tests at all economically plausible holding periods, against frozen LTM/F80 with identical eligible securities, exposure and costs, date/registrant/series/issuer resampling, and an untouched prospective holdout.

## 6. Controls

- No raw N-PORT artifact was copied into `main`; the 25-submission Phase 314 artifact remains in the expiring Actions artifact store.
- No historical short position was treated as a trade or as evidence of informed intent.
- No return/event study, alpha test, OOS, bootstrap, LOO or holdout use.
- No data purchase, vendor contact, quote request or paid-data use; spend remains USD 0.
- No source, universe, parameter, cost, exposure, holding-period or production change.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

**Conclusion:** Phase 313/314 add a useful, verified N-PORT data-lineage result: a unique but non-authoritative original-filing candidate, and proof that the 2022 amendment did not change the 20 audited short rows. This improves data interpretation, not investment predictability.
