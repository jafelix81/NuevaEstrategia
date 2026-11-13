# Phase 382 — CFTC archive anomaly repair diagnostic

**Status:** implementation and deterministic tests added; hosted targeted probe pending.  
**Parent:** Phase 380 full post-launch archive census.

## Targets

Five failed archive pages: 2011-06-14, 2013-12-31, 2014-11-25, 2014-12-02, 2019-12-24.  
One report-heading mismatch: 2018-09-25 filename resolves to a page whose content says positions as of 2018-09-18.  
Two stale Updated fields: 2011-05-10 page says Updated 2010-05-13; 2012-10-16 page says Updated 2007-06-29.

## Method

For each target, probe the expected archive filename and neighboring filenames at -14, -7, 0, +7 and +14 calendar days. Parse the report heading and Updated date, and collect HTTP Last-Modified, ETag and content length. Separately query CFTC TFF row counts for all instruments and Russell codes 239742/23977A on the target report date. Do not retain raw HTML or positions.

An exact page is identified only when the archive heading equals the target report date. A later file name is not assumed to be the correct report merely because it is nearby.

## Decision rules

- If no exact heading page is found, exclude that report date from any historical panel.
- If Updated predates the report heading, reject it as a PIT timestamp; inspect HTTP Last-Modified only as a separate candidate, not as an automatic replacement.
- If the CFTC API has Russell rows but no matching archive page, do not backfill a date from the next report.
- No strict PIT or alpha test is authorized by this diagnostic.

## Controls

No raw HTML, positions, trader identifiers, forward returns, alpha, OOS, bootstrap, LOO or holdout use. No changes to F80, production, universe, capital, parameters or exposure.
