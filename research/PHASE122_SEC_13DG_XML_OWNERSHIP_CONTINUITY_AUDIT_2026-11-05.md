# Phase 122 — SEC 13D/13G XML ownership-continuity audit

Date: 2026-11-05  
Status: PASS_DESCRIPTIVE_WITH_CAVEATS  
Scope: compare reporting-person ownership snapshots only across exact-CUSIP, XML-to-XML predecessor pairs from the stratified Phase 84 pilot. This is not a global 13D/13G census and is not an alpha test.

## Executive result

Phase 120 retrieved all 45 predecessor submissions selected from the 45/46 Phase 119 index-validated amendment pointers. Phase 120's workflow conclusion was `failure` because the auditor deliberately returned `INCOMPLETE_OR_CONFLICT` for unresolved security identity; it was **not** a retrieval failure:

- 45/45 predecessor submissions downloaded and validated; zero download/accession failures.
- 44 pairs of SEC archive paths were byte-identical; one had a single valid path.
- 45/45 predecessor SEC headers passed accession, issuer/filer role, form-family and chronology checks.
- The 45 predecessors comprise 21 XML and 24 legacy HTML submissions.

Phase 121 re-parsed the immutable Phase 84 and Phase 120 inputs and completed the security-identity adjudication:

| Security identity result | Pairs |
|---|---:|
| Exact CUSIP match | 39 |
| CUSIP mismatch requiring adjudication/quarantine | 5 |
| No CUSIP on either side; exact class-title match only | 1 |
| **Total** | **45** |

The five CUSIP mismatches are not one homogeneous error class:

1. United Homes Group / DiamondHead Holdings: documented SPAC business combination; successor security, not unchanged CUSIP (effective 2023-03-30).
2. Benitec Biopharma: documented 1-for-17 reverse split and new CUSIP (effective 2023-07-26).
3. NuCana: documented ADS-ratio change from one ADS per ordinary share to one ADS per 25 ordinary shares, with a new ADS CUSIP (effective 2024-04-16).
4. First Trust ETF VIII: predecessor and current filings point to different ETF series under the same trust CIK; this is a cross-series index link, not the same security.
5. Toro Corp.: predecessor filing's CUSIP is strongly inconsistent with the issuer CIK/name and appears to be a filing-level mis-key. This remains **suspected, not confirmed**, and is excluded from same-security continuity.

The one class-title-only pair is Jefferies Credit Partners BDC: issuer/filer roles and class title match, but neither side supplies a CUSIP. It remains weaker evidence than a security identifier.

## Phase 122 — ownership fields on eligible XML pairs

The Phase 122 workflow re-downloaded the three immutable input artifacts (Phase 84, 120 and 121), verified all 45 current and 45 predecessor raw-file SHA-256 values, and compared only predecessor pairs meeting both conditions:
- predecessor and current filings contain their correct family-specific XML schema; and
- Phase 121 reports literal exact CUSIP equality.

Result:

| Metric | Result |
|---|---:|
| Exact-CUSIP XML predecessor pairs | 20 |
| 13D pairs | 14 |
| 13G pairs | 6 |
| Shared reporting-person links | 59 |
| 13D reporting-person links | 47 |
| 13G reporting-person links | 12 |
| Comparable reported share amounts | 59/59 |
| Share amounts that changed | 34/59 |
| Comparable percent-of-class values | 59/59 |
| Percent-of-class values that changed | 43/59 |
| Available per-person CIK comparisons matching | 36/36 |
| Identical amount-and-percent pairs within 13D group flags, across current/prior filings | 24 |

The 24 group-overlap observations are diagnostics, not 24 unique holders or independent positions. The 13D group flag is not a unique group identifier. The audit never sums reporting-person rows. In some filings multiple reporting persons report identical aggregate amounts and percentages; summing them would double-count overlapping beneficial ownership.

The 24 legacy HTML predecessors are not treated as zero ownership or zero reporting-person continuity. They are excluded from this XML ownership-field comparison because the Phase 120 legacy parser only established a conservative security-field probe. The single XML predecessor with a CUSIP mismatch (Toro) is also excluded.

## Interpretation

The result shows that ownership snapshots can be compared reproducibly for a narrow subset once the predecessor pointer is independently checked against issuer/filer roles, form family, chronology, XML schema and security identity. It does **not** show that a reporting person bought or sold the reported number of shares.

Changes in aggregate beneficial ownership can reflect purchases, sales, transfers, group attribution, denominator changes, conversions, ADS-ratio changes, corporate actions or filing corrections. A 13D group flag and identical reported amounts are not evidence that rows represent separate capital. Reporting-person names are the common match key; 13G XML does not provide a per-person CIK in this schema, so name matching is not a permanent identity key.

SEC acceptance timestamps are reproducible in the Phase 84 raw headers, but acceptance is not independently proven to equal public dissemination time. Keep the conservative next-regular-session availability rule until dissemination timing is independently verified. Event date is not knowledge date.

## Decision

- **Phase 120:** retrieval and SEC-header lineage passed; its overall status correctly remained incomplete because security identity was unresolved.
- **Phase 121:** PASS_WITH_CAVEATS for the 45-link security adjudication. Five CUSIP mismatches have explicit classifications; the suspected Toro mis-key remains quarantined.
- **Phase 122:** PASS_DESCRIPTIVE_WITH_CAVEATS for 20 exact-CUSIP XML ownership comparisons. This is a schema/lineage result, not evidence of predictive behavior.
- SEC 13D/13G remains a conditional event-data candidate. Do not authorize a return test until historical subject-issuer discovery, permanent/effective-dated security identity, inactive/delisted coverage, legacy HTML parsing and ex-ante dissemination timing are established across the broader filing population.
- No forward returns, feature selection, alpha test, vendor purchase, production change or F80 modification was performed.

## Reproduction and immutable artifacts

- Phase 120 live run: [42058411930](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42058411930) · artifact 13430422445 · SHA-256 `7a22b0b9e51a471047174d0b0ddea641cbe3147e8e9b0da60b08a939c639329c`.
- Phase 121 adjudication run: [42060958167](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42060958167) · artifact 13431157032 · SHA-256 `770f02fcf6be83457c33b5e20c1265d5ff33326b8f0bb16e497e2d7326dcc4bc`.
- Phase 122 ownership audit: [42062157962](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42062157962) · artifact 13430963372 · SHA-256 `fd359c74ee4442a096956bac1ed6947e85242569ebca102cbe7407e425abc007`.
- Auditor: [phase122_sec_13dg_xml_ownership_continuity_audit.py](phase122_sec_13dg_xml_ownership_continuity_audit.py).
- Regression tests: [test_phase122_sec_13dg_xml_ownership_continuity_audit.py](test_phase122_sec_13dg_xml_ownership_continuity_audit.py).
- Workflow: [phase122_sec_13dg_xml_ownership_continuity_audit.yml](../.github/workflows/phase122_sec_13dg_xml_ownership_continuity_audit.yml).

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
