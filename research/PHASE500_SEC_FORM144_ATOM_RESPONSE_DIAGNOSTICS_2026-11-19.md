# Phase 500 — SEC Form 144 Atom response diagnostics

**Date:** 2026-11-19 UTC  
**Branch:** `phase500-sec-form144-atom-response-diagnostics`  
**Baseline main:** `de969d94ed6a665998037f09e976c7e380a93e14`  
**Disposition:** operational diagnostic hardening only; no data or signal admission.

## 1. Triggering evidence

Reviewed the latest 100 Actions runs (7,892 total), current main, open PRs, the first 100 matching phase branches, research files, jobs, logs and artifacts. No workflow was active or queued in the inspected run window.

The latest SEC Form 144 poll was [run 44521745535](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44521745535), created 2026-11-19 12:12:33 UTC. Offline regression passed 43 tests; live capture completed with a **partial** poll.

Observed feed-level results:
- Form 144 feed: XML parser failure at line 1, column 61; 3,292 response bytes; SHA-256 `fa047ac3976e3e3d307625487e2545b4e7126efb2e4101890b028e0abc82d207`.
- Form 144/A feed: 29-byte empty page, zero Atom entries; the previous accession watermark was not present, so the feed interval remained potentially unbounded.
- Successful feeds: 144/A only; failed feeds: 144.
- Events written: 0; feed observation rows appended: 0; research-observation eligible: 0; signal eligible: 0.
- State records 13 poll attempts, 12 complete and 1 partial. The 144/A watermark was not advanced across the missing prior accession.

The response bodies were not retained. The available evidence does **not** establish whether the 3,292-byte Form 144 response was an HTML challenge, malformed XML, or another upstream payload. No retrospective classification is claimed.

## 2. Change

Added a bounded response-format classifier to the existing Phase 403 collector. It records only one of:
- `ATOM_XML`
- `HTML`
- `JSON`
- `XML_OR_MARKUP`
- `OTHER_TEXT`
- `EMPTY`
- `NO_RESPONSE`

The classifier examines at most the first 512 decoded characters and does not persist or emit the body. Existing raw SHA-256 and byte count remain the forensic identifiers. A format label is diagnostic only: it does not turn a failed page into a successful poll, advance a watermark, or certify public availability.

Successful page metadata also records the response kind. Error metadata records the same label where response bytes exist.

## 3. Regression coverage

Added tests for:
- HTML, Atom XML, JSON, malformed markup, other text, empty and absent responses;
- preserving a successful feed while classifying a malformed sibling feed;
- preserving the possible-gap condition when an empty Atom page arrives before a prior watermark.

The existing fail-closed pagination and signal-eligibility rules remain unchanged.

## 4. Other source status at review

- SEC Form 4 latest scheduled capture [44505739718](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44505739718): 18 new canonical metadata events; zero research-observation eligible and zero signal eligible. Transaction XML was not downloaded in that run.
- FINRA Reg SHO latest live capture [44453548570](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44453548570) predates the Phase 495 parser fix: 8 HTTP 200 responses, 0 first-seen and 0 eligible observations. The post-fix PR run was offline-only; a new scheduled live capture is still required.
- CFTC TFF latest capture [44453066854](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44453066854) succeeded, but all four tracked contracts still have 2026-11-10 as their latest report date. No new report was admitted.
- Cboe Phase 357 remains a draft PR (#44). Historical product-start conflicts and PIT delivery-clock limits remain unresolved. Issue #132 remains open for human confirmation of sample redistribution rights; no deletion action is available through the connected GitHub operations.

## 5. Decision

- Keep Form 144/144-A in metadata-only quarantine until both feed pagination and first-seen intervals are complete and bounded.
- Do not infer the cause of the latest parser error without the original response bytes.
- Do not run a manual duplicate capture; the next scheduled workflow should supply the next independent observation.
- No event study, return test, OOS, bootstrap, LOO or signal admission.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
