# Phase 324 — SEC Form 4 exception source-level adjudication

**Date:** 2026-11-12 UTC  
**Status:** PASS WITH THREE QUARANTINED CASES  
**Research class:** SEC source-integrity / point-in-time availability audit; no return test

## Executive decision

Phase 323 had 21 of 24 full-census exceptions corroborated at the date level by original filing acceptance dates and SEC daily-index dates. Three remained unresolved. Phase 324 re-fetched the three original SEC submissions and a targeted set of 21 daily Form 4 indexes.

All three original submission headers and XML identity sets matched the immutable Phase 322/323 metadata. The six exact accession/index rows recovered for two cases are internally consistent at the entity/path level. The third accession is absent from all six business-day indexes searched after its acceptance date. **All three cases remain quarantined** because each has a distinct unresolved clock/index issue.

This closes the source-level review of the 24 purposive exceptions; it does not make the full Form 4 dataset strict-PIT eligible.

## 1. Provenance and controls

- Phase 321 full-census source: run [43177940904](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43177940904), artifact [13925636412](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43177940904/artifacts/13925636412), SHA-256 \`e45cab68d1ebe15248cc76bad70b015c8f0bd2052689c0690478bbca4526965c\`.
- Phase 322 exception source: run [43187165781](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43187165781), artifact 13928752264, SHA-256 \`c7eaf3cfc751e401d543bceeec20c3fe6643b09dfb8d2b0ff97df86070dca50d\`.
- Phase 323 clock source: run [43188524842](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43188524842), artifact 13928449264, SHA-256 \`dacc9f8374e4f86cc31dbe59de5d856ee1900902ce4096b879b69127e38e66fb\`.
- Phase 324 final run: [43192937006](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43192937006), artifact [13930934547](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43192937006/artifacts/13930934547), ZIP SHA-256 \`e2828741eba0317dc5a582e0c70796f88ec438a606e268807f92cb9a2ef0f78b\`.
- Final run passed 9/9 offline regression tests, fetched 3/3 original filings and 21/21 daily indexes, parsed 6 exact accession rows, and had zero HTTP or parser errors.
- The committed source manifest records the source run/artifact IDs and hashes; it contains parsed metadata only, not raw SEC bytes. Original SEC bytes and index bytes were hashed/parsed in memory and not uploaded.
- The source manifest is a purposive three-case subset of the 24 Phase 322/323 exceptions. It is not a probability sample.

## 2. Results by accession

### A. VIST Financial Corp — accession 0000775662-08-000044

**Classification:** \`MULTI_INDEX_DATE_OR_FILED_DATE_CONFLICT_QUARANTINED\`

- Original header and XML identity: PASS. Issuer CIK 775662; reporting-owner CIK 1102914.
- Header \`FILED AS OF DATE\`: 2006-02-15.
- \`ACCEPTANCE-DATETIME\`: 2008-10-02 13:14:57 ET — a 662-EDGAR-business-day lag from the header date.
- Four exact daily-index rows were found, all with matching row CIK and filing-path CIK:
  - 2008-10-02 index: two entity rows, both with row \`FILING_DATE\` 2008-10-02.
  - 2008-10-06 index: the same two entity rows, both with row \`FILING_DATE\` 2006-02-15.
- The same accession is therefore repeated in two daily indexes with conflicting row dates. Both entity CIKs are present, but the cross-index date conflict prevents routine admission.
- XML transaction code is \`P\`. SEC code P means “open market or private” purchase; it does not, by itself, prove a public-market execution.

Original submission: [SEC accession](https://www.sec.gov/Archives/edgar/data/775662/000077566208000044/0000775662-08-000044.txt).

### B. BeOne Medicines Ltd. — accession 0001193125-26-393103

**Classification:** \`ORIGINAL_HEADER_CONFIRMED_DAILY_INDEX_ABSENT_IN_RECHECK_WINDOW_QUARANTINED\`

- Original header and XML identity: PASS. Issuer CIK 1651308 and six reporting-owner CIKs (seven expected entity CIKs total).
- Header filed date and acceptance date: 2026-09-16; acceptance time 16:18:45 ET.
- No exact accession row was found in any of the six business-day indexes searched: 2026-09-16, 09-17, 09-18, 09-21, 09-22 and 09-23. All six indexes were retrieved and parsed successfully.
- XML transaction code is \`M\`, classified as exercise/conversion rather than an open-market purchase. The XML contains two non-derivative and two derivative transaction records; multiple reporting owners must not be treated as independent copies of a single economic trade.
- The absence of a daily-index row is a source-coverage exception, not evidence that the original filing did not exist. It remains quarantined.

Original submission: [SEC accession](https://www.sec.gov/Archives/edgar/data/1087939/000119312526393103/0001193125-26-393103.txt). The SEC header identifies the acceptance and filed dates; the XML identifies the issuer, six reporting owners and transaction code M. [SEC original filing](https://www.sec.gov/Archives/edgar/data/1087939/000119312526393103/0001193125-26-393103.txt).

### C. Nalco Holding Co. — accession 0001298341-06-000168

**Classification:** \`LONG_ACCEPTANCE_LAG_INDEX_FOUND_QUARANTINED\`

- Original header and XML identity: PASS. Issuer CIK 1298341; reporting-owner CIK 1120330.
- Header \`FILED AS OF DATE\`: 2006-02-14.
- \`ACCEPTANCE-DATETIME\`: 2006-10-13 15:47:51 ET — a 168-EDGAR-business-day lag.
- The 2006-10-13 daily index contains two exact rows (issuer and owner); both row dates and the index-file date equal the acceptance date. Both row CIK/path CIK pairs match.
- XML transaction code is \`P\`, which the SEC defines as open-market or private purchase. The unusually long filed-date/acceptance lag is not explained, so the case remains quarantined despite the acceptance-date/index-date agreement.

Original submission: [SEC accession](https://www.sec.gov/Archives/edgar/data/1298341/000129834106000168/0001298341-06-000168.txt).

## 3. Interpretation

The three exceptions are not one generic parser problem:

1. VIST is a cross-index repeat with conflicting filed dates and a very long acceptance lag.
2. BeOne is a verified multi-owner filing missing from the six-day daily-index window; its M code is not a discretionary purchase signal.
3. Nalco has matching acceptance/index dates but an unexplained 168-business-day lag from the header filed date.

The 21/24 cases previously corroborated in Phase 323 are mostly one-business-day shifts (20 cases) and one four-business-day shift. They match acceptance date and daily-index date, but the 24 exceptions are a purposive exception population, not a probability sample. Do not generalize 21/24 to all SEC Form 4 filings.

A daily-index date is date-level evidence, not an exact first-public receipt timestamp. \`ACCEPTANCE-DATETIME\` is not transmission commencement. The conservative date-level rule remains: for a corroborated daily-index date, do not permit strategy use before the first full XNYS session strictly after that date. Strict PIT admission remains closed.

## 4. Decision and next gates

- Retain all three accessions in quarantine with explicit reason codes; do not repair dates by choosing the most convenient source.
- Keep the 21 corroborated cases as date-level evidence only, not as proof of exact public availability.
- Continue the prospective Form 4 RSS capture until a new accession arrives and a real first-observation interval can be measured.
- Resolve effective-dated issuer/security/share-class identity and survivorship-aware broad-universe coverage before any event study.
- Preserve transaction-code and footnote distinctions. SEC P/S codes include private transactions; M is not an open-market purchase. Do not infer discretionary informed buying from acquired shares alone.

**F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.** No alpha/return test, bootstrap/LOO, chronological OOS or holdout test was run. No production, universe, capital or parameter change; no vendor contact, data purchase or email. Strict PIT and signal admission remain closed.

## Reproduction

- [Phase 324 source-level audit script](phase324_sec_form4_exception_source_adjudication.py)
- [Offline regression tests](test_phase324_sec_form4_exception_source_adjudication.py)
- [Immutable parsed source manifest](data/phase324_source_cases.json)
- [Final GitHub Actions run](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43192937006)
- [Parsed artifact and hashes](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43192937006/artifacts/13930934547)
