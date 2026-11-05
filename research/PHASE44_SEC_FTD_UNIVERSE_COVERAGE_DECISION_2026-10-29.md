# Phase 44 — SEC FTD frozen-universe coverage decision

**Date:** 2026-10-29  
**Status:** PASS — identity/coverage feasibility gate only

## Result

The SEC FTD actual-file parser and frozen-universe identity audit passed. The representative files contain usable economic records after excluding SEC trailer metadata:

- 2018 first half: 43,567 rows; 253/335 frozen-universe symbols covered (75.522%).
- 2026 second half: 66,693 rows; 316/335 symbols covered (94.328%).
- Covered in both representative files: 237/335 (70.746%).
- Covered in either representative file: 332/335 (99.104%).
- No exact duplicate economic rows, empty CUSIPs, or negative quantities were found.
- The SEC trailer record counts and total quantities reconcile exactly.
- One 2026 observation has a missing ticker but a valid CUSIP; it remains usable only through deterministic CUSIP identity.

## Interpretation

This is **not** an alpha result and does not authorize a directional interpretation of FTD. Missing symbols in a historical FTD file cannot be treated as zero FTD without first establishing that the security was active/listed at the relevant date. Conversely, the frozen 335-symbol universe contains securities that did not exist or were not listed in 2018.

The important feasibility result is that FTD has meaningful historical coverage, but production research must use a **date-appropriate active universe** and deterministic security identity rather than requiring 335/335 coverage at every historical date.

## PIT rule

For any FTD observation, the `settlement_date` is not the knowledge date. The first-half monthly file is assumed knowable only at its documented release point; the second-half file only at its documented later release point. Signal construction must therefore use the explicit file knowledge date and never the settlement date as the information timestamp.

## Next gate — Phase 45

Build a reproducible historical active-universe/CUSIP crosswalk for the 335 frozen symbols. For each representative and later historical FTD signal date:

1. establish whether the security was active/listed by the knowledge date;
2. preserve ticker changes through CUSIP where possible;
3. distinguish `not active`, `active with zero observed FTD`, and `active with observed FTD`;
4. quantify usable panel coverage by date;
5. reject any signal date where the active-universe identity cannot be established reproducibly.

Only after this gate passes may FTD variables be engineered and tested incrementally against frozen LTM/F80.

## Baseline protection

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No strategy weights, ranking rules, holding periods, or exposure rules were changed.
