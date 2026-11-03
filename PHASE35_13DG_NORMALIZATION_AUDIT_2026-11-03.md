# Phase 35 — 13D/13G Normalization Audit

Date: 2026-11-03
Branch: `phase35-event-normalization-audit`
Source artifact: `phase35-13dg-pit-event-crosswalk-audit`

## Purpose
Audit the completed issuer-level PIT dataset before any forward-return test. This is a data/normalization gate only; no alpha inference is made here.

## Dataset
- 20,266 resolved filings.
- 303 issuer CIKs.
- Forms: 13G 5,509; 13G/A 13,333; 13D 215; 13D/A 1,209.
- 14,542 amendments (71.76%).
- Event date present in 19,680/20,266 (97.11%).
- Reporting-person field populated in only 3,502 rows.
- Purpose text populated in only 261 rows.
- Filing dates in the extracted dataset begin 2020-10-01 and end 2026-09-25.

## Deterministic provisional lineage audit
A conservative provisional key was constructed offline as `issuer_cik + filer_cik + form_family`, where `filer_cik` is the CIK prefix encoded in the accession number. This is deterministic, but it is not a substitute for reporting-group identity. A single beneficial-owner group can contain multiple reporting persons/entities and the current extracted `reporting_person` field is too sparse to reconstruct those groups reliably.

Results:
- 3,115 deterministic filer/issuer/family sequences.
- 3,115 first-observable rows under that provisional key.
- 2,841 first-observable 13G-family rows.
- 274 first-observable 13D-family rows.
- 136 issuers with at least one 13D first-observable sequence.
- 302 issuers with at least one 13G first-observable sequence.
- 360 issuer/family combinations have more than one filer CIK; maximum observed filer count for an issuer/family is 26.
- 1,823/3,115 (58.5%) provisional first-observable rows are amendments.

## Critical gate finding
The 58.5% amendment share among provisional first-observable rows is a data-coverage warning, not evidence of a high amendment rate at true initiation. The current extraction starts on 2020-10-01, so an amendment can be the earliest observation simply because the original filing occurred before the extracted history. Therefore these rows must not be treated as true first 13D/13G economic events.

The correct next gate is to extend the historical filing window sufficiently to capture predecessor/original filing chains before declaring a first-observable event. No forward-return test should use the current provisional first-event set as if it represented true initiations.

## Additional finding: 13D mechanism coverage
Only 47 of the 274 provisional first-observable 13D sequences have non-null `purpose_text`. Therefore a purpose-text requirement would discard most observations. Missing purpose text must remain `unknown`; it cannot be interpreted as non-activist or activist.

## Directional-state audit
Using the provisional filer/issuer/family key and only sequential observations with comparable ownership fields:
- Increase: 7,691 transitions.
- Decrease: 8,364 transitions.
- No change: 874 transitions.
- Unknown/unclassifiable: 222 transitions.

These counts are descriptive only. They are not an alpha test and do not justify selecting increase/decrease as the predictive direction.

## Decision
**ECONOMIC TEST BLOCKED.**

The issuer/PIT identity gate is passed, but event normalization is not yet sufficiently historical or group-deterministic for a clean 13D/13G initiation signal. Next gates:
1. extend filing history before 2020-10-01 to recover predecessor filings;
2. reconstruct reporting groups conservatively from filing-level evidence rather than using filer CIK as a proxy for the whole group;
3. preserve 13D and 13G as separate mechanisms;
4. classify ownership direction only when sequential states for the same deterministic economic group are available;
5. only after these gates pass, construct the historical active-F80 event set and run the preregistered OOS test.

No F80/LTM control changes are permitted by this audit.
