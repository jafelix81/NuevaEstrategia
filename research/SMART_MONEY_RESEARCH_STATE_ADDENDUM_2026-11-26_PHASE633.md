# Smart Money Research state addendum — Phase 633 (2026-11-26 06:45 UTC)

**Main HEAD before checkpoint:** `99754d55cc63f972796f81b8dc4b060500e63391`

- Merged Phase 626 / PR #240 (`b43c562`): strict Form 4 entity duplicate sidecar; exact key requires recognized 4/4A feed, valid accession, role, nonzero numeric CIK and normalized name. PR regression 80/80. Natural post-merge capture still pending.
- Merged Phase 628 / PR #241 (`03470ce`): corrected 13D/G identity documentation; master-index company is candidate subject, SUBJECT COMPANY verifies subject, FILED BY identifies filing entity, accession prefix is submitter/login CIK, archive-path CIK is locator. Existing offline regression 30/30; live 44-header sample still pending.
- Merged Phase 618 / PR #235 (`99754d5`): crosswalk now reports missing Form 144 and Form 4 acceptance clocks separately. Existing offline regression 65/65; no timestamps imputed and no signal eligibility changed.
- Form 4 per-poll ledger re-audit: run 45714679017 had 912 entity rows / 910 strict keys / 2 exact repeated entity rows; run 45759597509 had 192 / 192 / 0. Do not aggregate exact-duplicate counts across poll runs.
- Latest natural Form 4 run 45759597509 added 90 canonical accession events and 192 entity observations; both feed continuity gates passed, but exact public availability and signal eligibility remain false.
- SEC 13F scheduled run 45751086501 failed closed because `SEC_USER_AGENT` was injected empty; no SEC request or state write occurred. The code fix is on main; repository secret availability is the remaining blocker.
- SEC 13D/G 44-header live sample not run; requires manual dispatch `run_live_sample=true` after the secret is available.
- FINRA Reg SHO run 45754121648: 8/8 files rejected for BCPC/TPC overlapping facility rows; zero accepted/eligible.
- CFTC TFF run 45753716471: 3,043 rows through 2026-11-17; no new reports/revisions; zero eligible.
- Options/MIDAS remain conditional feasibility only; no vendor contact, quote or purchase; options budget USD 0.
- N-PORT aggregate share-growth alpha candidate remains killed under Phase 526.
- Phase 20C same-day-close remains NO-GO; next-session test remains blocked by missing prospective label bridge and incomplete inactive/delisted price coverage.
- No new alpha, valid OOS, bootstrap or LOO result. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- Actions preflight: 0 in-progress / 0 queued; no duplicate workflow dispatched.

Full audit: [Phase 633](PHASE633_SMART_MONEY_OPERATIONAL_ADJUDICATION_2026-11-26.md).
