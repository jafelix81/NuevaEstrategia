# Phase 106 — SEC FTD identity and availability decision

**Date:** 2026-11-05  
**Source audit:** [Phase 105 run 41977069080](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41977069080)  
**Artifact:** [phase105-sec-ftd-identity, artifact 13391249428](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41977069080/artifacts/13391249428)  
**Artifact SHA-256:** `2ea3a0d365fb8d264c23531a942d5d092b43e3fffbdbd0ecfc15d87ac3218e25`  
**Decision:** SAME-DAY IDENTITY MOSTLY CLEAN; HISTORICAL PIT AND PERMANENT-ID GATES STILL OPEN.

## 1. Actual-file result

All seven official SEC FTD archives downloaded again, passed parsing/schema checks, and produced no malformed members or duplicate (settlement date, CUSIP, symbol) keys. CUSIP was nonblank and nine-character-valid in every sampled row. One blank symbol appeared in the September 2026 second-half file.

| Sample | Rows | Dates | CUSIPs | Symbols | Same-day CUSIP → multiple symbols | Same-day symbol → multiple CUSIPs |
|---|---:|---:|---:|---:|---:|---:|
| 2004 Q2 | 173,436 | 63 | 8,993 | 9,209 | 0 | 0 |
| 2008 Q3 | 285,343 | 64 | 14,857 | 14,987 | 0 | 0 |
| 2008 Q4 | 454,860 | 62 | 16,037 | 16,270 | 0 | 0 |
| 2009 Q2 | 422,893 | 63 | 14,729 | 15,019 | 0 | 0 |
| July 2009 first half | 57,537 | 9 | 10,556 | 10,563 | 0 | 0 |
| January 2018 first half | 43,567 | 9 | 9,820 | 9,824 | 0 | 1 |
| September 2026 second half | 66,693 | 12 | 13,397 | 13,394 | 0 | 0 |

**Key distinction:** many-to-many CUSIP/symbol relationships exist when counts are pooled across dates, but almost all disappear when mapping is evaluated on each settlement date. That indicates that much of the pooled ambiguity reflects effective-dated ticker/CUSIP changes rather than simultaneous conflicting identities.

## 2. The single same-day ambiguity

The only same-day symbol-to-multiple-CUSIP case is **DPW on 2018-01-02**:
- CUSIP 253862106 — description Digital Power Corp
- CUSIP 26140E105 — description DPW Holdings Inc

This aligns with the issuer's December 29, 2017 announcement that the formal name change to DPW Holdings would become effective at the close of business while retaining ticker DPW. This is consistent with a corporate-reorganization/CUSIP transition, not evidence that two unrelated securities should be merged. Keep both CUSIPs as separate effective-dated identifiers until the corporate-action crosswalk resolves the transition. Never collapse them by ticker alone.

## 3. HTTP metadata and PIT

HEAD and GET succeeded for all seven archives. ETag was absent for every file. The HTTP Last-Modified results were:

| Sample | Last-Modified |
|---|---|
| 2004 Q2 | 2020-12-19 |
| 2008 Q3 | 1970-01-01 (invalid) |
| 2008 Q4 | 2020-12-19 |
| 2009 Q2 | 2020-12-19 |
| July 2009 first half | 2020-12-19 |
| January 2018 first half | 2020-12-19 |
| September 2026 second half | 2026-10-15 |

The current September 2026 second-half file's Last-Modified date matches the SEC's approximate mid-month release convention. Older archives show migration/reset timestamps, so this cannot be generalized to historical publication dates.

The SEC explicitly states:
- first-half data are available at month-end;
- second-half data are available about the 15th of the next month;
- it cannot guarantee posting by a particular date.

Therefore the schedule is useful for a conservative knowledge-date convention, but not an exact verified posting ledger. The older archive HTTP metadata are not valid PIT timestamps. A future test must use an independently defensible delayed availability rule and disclose it as an assumption, or obtain contemporaneous release evidence.

## 4. What this changes

- FTD CUSIP/symbol identity is materially more promising than a ticker-only source: same-day ambiguity was zero in six of seven samples and limited to one plausible corporate-action transition in the 2018 sample.
- CUSIP is still not a permanent return-source identifier. A point-in-time CUSIP-to-PERMNO/FIGI/security-master crosswalk with effective dates, record-known dates, corporate actions and inactive/delisted coverage remains necessary.
- The SEC FTD file is an event/balance feed, not a complete listing universe. Absence from an FTD file is not evidence that a security was not listed.
- FTD remains a settlement-friction hypothesis. It is not daily short-sale flow, aggressor direction, investor identity, or proof of informed/institutional trading.

## 5. Gate status

| Gate | Result |
|---|---|
| Seven representative archives download and parse | PASS |
| CUSIP completeness / format in sample | PASS |
| Same-day CUSIP-symbol ambiguity measured | PASS |
| Duplicate key check | PASS |
| Effective-dated CUSIP-to-permanent-ID crosswalk | NOT ESTABLISHED |
| Inactive/delisted return linkage | NOT ESTABLISHED |
| Complete historical public-availability vintages | NOT ESTABLISHED |
| Forward-return / alpha test | NOT AUTHORIZED |

No return data were joined, no feature was constructed, no forward returns were inspected, no vendor was contacted, no data were purchased, and F80 was not changed.
