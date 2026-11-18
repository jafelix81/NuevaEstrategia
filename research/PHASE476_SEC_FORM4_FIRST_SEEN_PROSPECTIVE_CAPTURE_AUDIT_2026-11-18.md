# Phase 476 — SEC Form 4 / 4-A prospective first-seen metadata capture

**Audit cutoff:** 2026-11-18 10:50 UTC  
**Base main:** \`5ba900aa6901f6f5e015f3219885fa9f4ffa2c9b\`  
**Disposition:** add a metadata-only prospective collector for Forms 4 and 4/A. This fills a gap not covered by the existing Form 144 collector. It does not admit an insider signal, reconstruct historical first-public timestamps, or authorize a return test.

## 1. Preflight before changes

- Main HEAD: \`5ba900aa6901f6f5e015f3219885fa9f4ffa2c9b\`, Phase 475 merged through PR #135.
- Actions inventory: 7,798 total runs; latest 100 contained no active or queued runs. Latest Phase 475 run [44280678035](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44280678035) completed successfully; its only job \`offline-regression\` passed and it produced no artifact. The push run [44280647505](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44280647505) also passed.
- Latest scheduled CFTC run [44232546204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204) succeeded at 03:44:45 UTC and produced artifact [14395926632](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204/artifacts/14395926632).
- Latest scheduled SEC Form 144 run [44228413864](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228413864) succeeded at 03:09:36 UTC and produced artifact [14393319006](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228413864/artifacts/14393319006). The main workflow still declares \`47 * * * *\`; no later Phase 403 schedule event appeared in the latest 100-run inventory through 09:57 UTC. This is a delivery gap, not proof that the workflow is disabled. Issue [#136](https://github.com/jafelix81/NuevaEstrategia/issues/136) records the manual enabled-state/default-branch check.
- FINRA Phase 469 run [44228802578](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44228802578) was PR CI, not a scheduled live capture. Its scheduled slots on Nov 18 at 22:30/23:30 UTC were still in the future.
- Workflow directory contains 81 files. No existing scheduled Form 4/4-A prospective collector was found; Phase 39 is a manual acceptance-gate workflow, and Phases 431/439/453/455/458–461 are audits/regressions.
- No workflow was dispatched, rerun, or duplicated.

## 2. Why this is a useful independent next step

Phase 457 established that SEC quarterly Form 3/4/5 bulk archives cover January 2006–September 2026 (83 quarterly ZIPs) and can support a descriptive historical census, but the bulk archive is not a point-in-time feed. Its \`FILING_DATE\` is date-only and the archive itself is published quarterly. It cannot reconstruct when the system first observed each filing.

The existing Phase 403 collector captures Forms 144 and 144/A only. The workflow inventory has no scheduled Form 4/4-A first-seen collector. A separate prospective metadata ledger therefore adds a distinct, free SEC information stream without purchasing a commercial data set.

Official SEC references:
- [SEC RSS feeds](https://www.sec.gov/about/rss-feeds) — EDGAR Latest Filings can be filtered by form type and ownership filings.
- [SEC Search Filings](https://www.sec.gov/search-filings) — Latest Filings is described as a real-time listing.
- [Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) — declares User-Agent, describes dissemination/index timing and sets a maximum of 10 requests per second.

## 3. Collector design

The new workflow polls two form-specific Atom feeds:
- Form 4: \`type=4\`
- Form 4/A: \`type=4%2FA\`

It polls every 15 minutes on weekdays at UTC minutes 10, 25, 40 and 55. The existing Form 144 poll remains on minute 47; the new schedule is separated from it by at least eight minutes at the closest hourly boundary.

The collector:
- uses the repository's existing SEC fetch helper and declared User-Agent;
- pages in 100 raw Atom rows, advancing offsets by raw entry count rather than unique accessions;
- follows the prior accession watermark up to 20 pages;
- detects repeated page hashes, missing watermarks, empty pages and fetch errors;
- records the response receipt time, page hash, offset, accession, form, feed timestamp, filing date and filing URL;
- stores only a feed-path CIK as **unverified** metadata, not as a security identity;
- preserves an append-only event ledger and separate page-observation ledger;
- records initial baseline and gap observations without promoting them to bounded events;
- uses the previous successful poll end as a conservative lower bound and the actual response receipt as an upper bound;
- preserves Form 4/A as a separate information-arrival event; it does not count amendments as new economic trades.

No filing XML/text is downloaded. No transaction rows, owner names, prices or raw Atom payloads are persisted. SHA-256 hashes and aggregate poll summaries are retained.

## 4. Strict eligibility policy

A poll interval can be marked \`BOUNDED_METADATA_ONLY\` only when:
1. a previous successful poll exists;
2. the prior accession watermark is found during complete pagination; and
3. the run is a scheduled poll rather than a manual diagnostic.

Even then:
- \`research_observation_eligible=false\`;
- \`signal_eligible=false\`;
- \`public_availability_certified=false\`;
- \`same_day_intraday_use_authorized=false\`;
- security identity, historical F80 membership, owner attribution and transaction semantics remain unverified;
- EDGAR feed \`updated\` is retained as source metadata, not treated as the exact first-public timestamp;
- first-seen local receipt is an upper bound, not the exact public-availability instant.

This phase only builds a future-research metadata clock. It does not overcome the historical identity and line-to-owner constraints in Phases 453/459/461, nor the mixed public/private meaning of transaction code P documented in Phase 457.

## 5. Validation and operational controls

The offline suite covers accession parsing, Form 4/4-A classification, filing date and CIK extraction, UTC conversion, baseline/gap/manual classification, raw-row pagination offsets, watermark discovery, repeated-page detection, page-limit failure, fetch failure and append-only persistence.

The workflow runs only offline tests on push/PR. Live capture runs only on the scheduled event or explicit manual dispatch. Manual dispatch is diagnostic and does not persist the ledger. Scheduled runs commit metadata to \`research/data/sec_form4_first_seen\` and upload a compact summary artifact; no raw filing bytes are uploaded.

The schedule is a proposed prospective capture cadence, not evidence that GitHub has delivered any first-seen observation. The first scheduled run after merge will be a baseline. The next successful bounded poll is required before any event can have a bounded metadata interval.

## 6. Research disposition

- Form 4/4-A is retained as a conditional disclosure-event source.
- No insider signal or participant identity is admitted.
- No bulk archive is backfilled into the prospective ledger.
- No event study, forward-return test, alpha, OOS, bootstrap, LOO or holdout test was run.
- No vendor account, paid data, credentials or trial was created.
- \`F80_TOP20_PARTIAL50_BASELINE_C20\`, the 335-name universe, parameters, capital, exposure, costs, holding rules, holdout and production remain unchanged.

**Next gate:** obtain at least two successful scheduled polls with bounded intervals; then reconcile accession acceptance headers and filing XML only for a stratified sample, validate the form feed's 4/A coverage and historical security/owner mapping, and only then assess whether a preregistered insider hypothesis has sufficient independent issuer-event count.
