# Phase 307 — SEC owner filter semantics audit

**Date:** 2026-11-12  
**Status:** completed; owner=only passed the current-feed isolation and accession-preservation tests.  
**Branch:** phase307-sec-rss-owner-only-filter-audit

## Final hosted result

Final workflow [43142273073](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43142273073) passed **48/48 regressions** (8 Phase 307, 14 Phase 306, 8 Phase 305, 11 Phase 304, 7 Phase 303). All **37/37 live SEC Atom requests** succeeded and parsed. Artifact [13910211291](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43142273073/artifacts/13910211291), ZIP size 155,654 bytes, SHA-256 028c6af605e771fd3362b269f509b09ab210d66ece1d1b328421fa0b6ff010d0.

## Main finding: owner=only is the correct current-feed query mode

The SEC owner filter behaved consistently across the include/only/exclude controls:

- owner=only + type=4 returned **2,111 exact Form 4 entity rows across 1,022 unique accessions**, plus 36 Form 4/A rows caused by the type=4 prefix behavior.
- The Form 4 owner=only scan reached its tail at start=2,080: 27 pages, with the final page containing 67 rows. All 26 adjacent overlaps matched in order, and the final page-zero recheck was identical.
- No non-ownership forms appeared in the owner=only type=4 query. The only non-target token was 4/A (36 rows), which is itself an ownership form and must be separated by exact title-token filtering.
- owner=only + type=4/A returned **36 rows / 18 accessions** and reached its tail in one page; the page-zero recheck was identical.
- The include control preserved the same 50 exact Form 4 accessions on page zero, but sampled deeper offsets 0, 80, 320 and 400 contained 54 non-target rows.
- The owner=exclude negative control returned **zero exact Form 4 or Form 4/A accessions**.

Therefore the prespecified isolation, negative-control and page-zero accession-preservation checks passed. owner=only is useful for prospective Form 4 capture, but the exact form token remains mandatory because type=4 still includes 4/A.

## Data integrity and pagination

- 37 live requests, all HTTP 200 and parsed.
- 48/48 offline regression tests passed.
- Form 4: 2,111 unique target entity rows, 1,022 accessions, 1,022 Issuer rows and 1,089 Reporting rows.
- Form 4/A: 36 unique target rows, 18 accessions, 18 Issuer rows and 18 Reporting rows.
- The Phase 306 ordered-overlap checker was hardened to expect max(0, left-page-row-count minus step), including partial pages. A new regression proves a short right page cannot shrink the expected overlap and hide missing rows.
- The owner=only Form 4 scan passed all 26 ordered overlap checks, had a stable head recheck and no target structural errors.

## Decision

Promote owner=only as the **preferred SEC RSS acquisition filter** for the prospective capture layer, not as an investment signal. Capture Form 4 and Form 4/A separately, retain raw Atom responses and hashes, preserve Issuer and Reporting entities, deduplicate by accession/entity identity, and store first-observed time as an interval bounded by successful polls. Do not equate Atom updated with first public time.

The next research task is a 30-day prospective capture with gap markers and immutable raw-response hashes. A full current-feed snapshot is feasible (about 27 pages for Form 4 plus one page for Form 4/A in this observation), but historical retention and long-run coverage still need measurement.

## Interpretation limits and frozen controls

- This is a current-feed snapshot, not a historical archive or a guarantee of future retention.
- Exact first-public timestamp: **not verified**.
- Strict PIT admission: **not yet authorized**.
- PAC/deletion events: not captured by this query.
- Return/alpha, bootstrap/LOO and chronological OOS: not run.
- Holdout used: **false**.
- F80_TOP20_PARTIAL50_BASELINE_C20, production, universe, capital and parameters: unchanged.
- No vendor purchase/contact, no email sent, no PR opened or merged.
