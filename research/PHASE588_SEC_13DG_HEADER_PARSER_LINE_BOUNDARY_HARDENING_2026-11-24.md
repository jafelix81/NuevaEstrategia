# Phase 588 — SEC 13D/G header parser line-boundary hardening

**Audit cutoff:** 2026-11-24 05:06 UTC  
**Disposition:** parser-quality fix merged and regression-tested. This improves field isolation but does not complete subject-issuer identity reconstruction or authorize a historical return test.

## Finding

The Phase 485 _field regular expression used \s* around the colon and value. In Python, \s includes newline characters. If a SEC header contained an empty single-line field such as COMPANY CONFORMED NAME:, the expression could consume the next header line and return it as the empty field's value. For example, an empty name could be misread as the following CENTRAL INDEX KEY: field label and value.

The old behavior did not make a valid CIK from that example, but it could contaminate descriptive identity fields and weakened the parser's fail-closed audit trail.

## Change

PR [#213](https://github.com/jafelix81/NuevaEstrategia/pull/213) was merged into main as commit 100262a91e4faf15ef7174bc6ded6b4577ac9639.

- Restrict block-marker and field whitespace to horizontal spaces/tabs, with explicit CRLF handling.
- Restrict each parsed field value to a single line.
- Return None for blank values rather than consuming the next field.
- Add regression tests for empty subject name, empty filer name, and empty subject CIK.

The Phase 485 workflow [run 45330853390](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330853390) completed successfully. The job compiled the parser/tests and passed **11/11** unit tests, including the three new blank-field regressions.

## Scope and limitations

- No SEC request was made; no secret was read or changed.
- No 13D/G historical rebuild or accession backfill was run.
- No subject issuer, filer, ticker, CUSIP or historical F80 membership was newly certified by this parser-only change.
- The legacy 20,266-row 13D/G panel remains quarantined pending separate subject-company identity, reporting-group, security-class, historical-universe and point-in-time reconstruction.
- The repository's SEC_USER_AGENT prerequisite remains necessary before the bounded live SEC sample and any subsequent rebuild.
- No event study, forward-return test, backtest, OOS, bootstrap, LOO or holdout test was run.

**Signals admitted: 0.** F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No universe, parameter, exposure, cost, holdout, holding-period or production change.
