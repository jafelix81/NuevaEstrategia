# Phase 632 — Form 4 transaction-quality refresh and cross-source gate recheck

**Audit cutoff:** 2026-11-26 05:40 UTC  
**Main HEAD at capture:** `2654f5729bb934451915604f9f78f798554d3d01`  
**Disposition:** new Form 4 metadata and structured rows were captured successfully; transaction-code P is not a usable insider-buy signal without owner, plan, execution, public-availability and historical-universe adjudication. No alpha, OOS or strategy change.

## 1. Preflight and Actions state

- Reviewed the latest Actions runs, jobs, logs and available artifacts before proceeding. No existing live capture was duplicated.
- Form 4 scheduled run [45759597509](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45759597509) completed both `offline-regression` and `live-capture` successfully; artifact [15089685727](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45759597509/artifacts/15089685727) was downloaded and inspected.
- The scheduled Form 4 job committed append-only state to main as [2654f57](https://github.com/jafelix81/NuevaEstrategia/commit/2654f5729bb934451915604f9f78f798554d3d01).
- The subsequent PR #240 regression run [45762887631](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45762887631) completed successfully (79 tests); its live-capture job was skipped. No workflow remained queued or in progress at final review.

## 2. SEC Form 4 — new metadata capture

Run [45759597509](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45759597509):

- 90 new canonical accession events; 192 entity-observation rows; 90 canonical issuer events.
- 100 reporting-entity occurrences; up to seven entities per accession.
- Both Form 4 and Form 4/A feed continuity/watermark gates passed; no missing issuer entity, unknown role, path-CIK mismatch or entity quarantine.
- The legacy `same_feed_duplicate_occurrences=100` field counts repeated accession occurrences, **not** exact duplicate entity rows. It must not be interpreted as 100 duplicate insiders or 100 duplicate entity records. PR #240 adds a separate strict entity-key audit to resolve this ambiguity.
- The collector records bounded metadata-observation intervals for the 90 new events, but exact SEC public-availability certification remains false; research-eligible and signal-eligible rows remain zero. No XML was downloaded for the 90 new feed events.

## 3. Structured Form 4 backfill — latest 37 appended rows

The post-capture artifact and the append-only repository ledger were reconciled. The current `transaction_details.csv` contains 340 rows; the latest scheduled backfill appended 37 rows across 10 accessions. Repository blob SHA: `dcb44f38182ff1c9e7208358995a3b94877710d7`.

- Transaction-code counts in the 37 appended rows: 11 `P`, 9 `S`, 4 `M`, 3 `A`, and 10 non-transaction/header rows.
- All 37 rows have `signal_eligible=false` and `public_availability_certified=false`.
- 34 rows remain `FILING_GRAIN_ONLY_SINGLE_OWNER`; 3 are `QUARANTINED_MULTI_OWNER_NO_LINE_LINK`. No transaction-line-to-owner attribution is verified.
- Nine of the eleven P-coded rows are for Atlassian (TEAM), held indirectly through the Cannon-Brookes Head Trust and explicitly reported as executed under a Rule 10b5-1 plan adopted 2026-08-09. This is a useful negative control: P-coded acquisitions are not automatically discretionary open-market insider buys.
- The remaining two P-coded rows are XBP Global Holdings (XBP): 3,595 shares at $2.29 on 2026-11-23 and 405 shares at $2.10 on 2026-11-24. No matching owner-sidecar record or footnote was present in this bounded sample. Treat these only as unresolved candidates; do not infer open-market execution, beneficial ownership, F80 membership or predictive intent.
- The backfill appended 66 footnote references; a separate footnote pass appended 26 references across 10 accessions, with four accessions marked as having no references. Eighty footnote accessions remain in the bounded queue.

The distinction between filing-grain owner count and transaction-line owner attribution remains mandatory. A one-owner filing is not itself proof that the reported person beneficially owns every transaction row.

## 4. Form 144 / Form 4 crosswalk

The run produced 11 descriptive crosswalk rows: 10 proposed-sale rows and one prior-sale-history row, across nine matched Form 4 accessions.

- All 11 rows are disposition code `S` / `D`; no crosswalk row is signal-eligible.
- Three rows have exercise/tax context flags; eight have no specific Remarks flag.
- Eight proposed-sale rows have Form 144 acceptance before Form 4 acceptance, but Form 4 acceptance is not execution time.
- Two proposed-sale rows have unresolved Form 144 acceptance clocks.
- Seven multi-owner accessions were quarantined; 13 Form 4 accessions lacked a single-owner identity in the crosswalk.
- Historical F80 membership and intraday execution time remain unverified.

Form 144 is a proposed-sale notice, not proof of execution. The crosswalk is not evidence of predictive selling.

## 5. PR #240 — entity-duplicate semantics review

PR [#240](https://github.com/jafelix81/NuevaEstrategia/pull/240) remains Draft and unmerged.

The branch adds an append-only `entity_duplicate_audit.csv` with a strict key over feed, accession, role, numeric nonzero CIK and normalized entity name. During independent review, I found that blank CIK values could be zero-padded into a truthy string; this was corrected by requiring 1–10 numeric digits and a nonzero value, with a dedicated regression. An initially over-escaped regex caused two tests to fail in run [45762844103](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45762844103); it was corrected in commit `10c5002`, and the subsequent run [45762887631](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45762887631) passed **79/79**. Live capture was skipped as intended.

The correction is still on the Draft PR branch, not main. Do not interpret its new exact-entity counts as production-validated until reviewed/merged and a later natural capture confirms the sidecar.

## 6. Other source gates rechecked

### SEC 13F

Scheduled run [45751086501](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45751086501): offline regression 36/36 passed; live capture failed before any SEC request because the injected `SEC_USER_AGENT` value was empty. No state or ledger advanced. PR #242's code guard is on main; this remains a repository Actions-secret availability/configuration issue.

### SEC 13D/G

Runs [45733913256](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45733913256) and [45733842155](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45733842155) were `pull_request` events, not manual `workflow_dispatch` events. Their 30/30 offline tests passed, but `live-sample` was skipped. The preregistered 44-header sample has **not** been executed. It requires a manual dispatch with `run_live_sample=true` after the SEC User-Agent secret is available.

### FINRA Reg SHO

Run [45754121648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648), artifact [15086513251](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648/artifacts/15086513251):

- Eight requested daily files returned HTTP 200; all eight were rejected by the fail-closed duplicate-symbol/facility-overlap gate.
- BCPC and TPC recurred in every file: 16 extra rows across eight dates.
- No exact raw-row duplicates; facility-token sets overlap.
- Zero accepted files, first-seen events or eligible observations; raw volumes were not persisted.
- Keep the parser quarantined. Do not sum, drop or select rows by ticker/facility overlap. The bounded `regShoDaily` API reconciliation remains conditional on authorized credentials and permitted-use rights.

### CFTC TFF

Run [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471), artifact [15086462804](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471/artifacts/15086462804): 3,043 observations, no new reports/revisions, latest report date 2026-11-17, zero signal-eligible historical rows. Retain only as a possible broad positioning/regime covariate, not security-level institutional flow.

### Options / MIDAS

No new source passed the historical-coverage, ex-ante timestamp, license and reproducibility gates. No vendor was contacted, no quote requested and no data purchased. Options-data budget remains USD 0.

## 7. Phase 20C and model disposition

- Phase 593 remains authoritative: same-day-close FINRA entry is NO-GO because the daily file is published after the regular session. The next-session successor is not yet validated.
- No new return test, OOS, bootstrap or LOO result was produced.
- New signals admitted: **0**.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No changes to universe, parameters, exposure, costs, holding-period policy, holdout or production.

## 8. Next gates

1. Verify that the exact repository Actions secret `SEC_USER_AGENT` exists as a repository Actions secret and is available to scheduled workflows; do not expose its value.
2. After that secret is available, execute the one-time Phase 616 workflow dispatch with `run_live_sample=true`; do not treat PR CI as a live sample.
3. Keep Form 4 transaction candidates descriptive until transaction-line owner identity, transaction semantics, exact public-availability clock and effective-dated historical F80 membership are independently established.
4. Resolve FINRA BCPC/TPC only through an authorized security-grain/facility reconciliation; preserve fail-closed behavior meanwhile.
5. Continue prospective SEC Form 4, Form 144 and CFTC capture without treating source labels as evidence of institutional intent.
