# Phase 336 — SEC XBRL taxonomy schema and custom label-linkbase retrieval

**Date:** 2026-11-12 UTC  
**Status:** COMPLETED WITH EXPLICIT LINKBASE QUARANTINES  
**Research class:** identity metadata and source feasibility; no return or alpha test.

## Executive result

Phase 336 consumed the immutable Phase 334 symbol/class-binding artifact, selected the eight filings containing the six multi-QName symbols, re-fetched their XBRL instances, verified each instance against its pinned SHA-256, and retrieved the filing-specific schema and custom label-linkbase resources.

- 8/8 selected filing indexes returned HTTP 200.
- 8/8 XBRL instance hashes matched the Phase 334 manifest.
- 42/42 schema-resource observations were retrieved.
- 8/8 custom label-linkbase observations were retrieved.
- 32 member-fact rows represented 12 unique raw QNames across six symbol groups.
- 12/12 QNames were found in a schema element; 10/12 had a preferred label under the Phase 336 extraction rule.
- No raw QName was merged.

GitHub Actions [run 43228785778](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43228785778) passed **8/8 offline regressions**. Artifact [13949661332](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43228785778/artifacts/13949661332), ZIP SHA-256 \`da010b603e408260d3191b9af9d70de3f03537db97e1dfd0a98ed8c3b8739dac\`.

## What the first classifier missed

The initial classifier compared each member's complete set of default-role label texts. If one QName had an extra \`label\` resource and the other had only a \`terseLabel\`, the complete sets differed even when the pair shared an exact \`terseLabel\`.

For PCG-PB, PCG-PE, PCG-PG and PCG-PI, both QNames share an identical \`terseLabel\`; one QName also has a one-sided default \`label\` resource. PCG-PH has a different default-label string on the common \`label\` role, although one member's \`terseLabel\` exactly overlaps the other member's \`label\` text.

STR's two members use standard US-GAAP namespaces. Their standard label/documentation linkbases are not referenced from the base schema and were not retrieved by the Phase 336 custom-linkbase-only path. This was a retrieval-scope omission, not evidence that the members lack standard labels.

The Phase 336 classification is therefore retained as a conservative first-pass result, not treated as a final semantic comparison. Phase 337 corrects the comparison and retrieves the missing official standard-taxonomy resources.

## Decision

- Preserve all 12 raw QNames and all accession/context/namespace relationships.
- Do not merge any QName.
- Do not infer that equal same-context Security12bTitle text alone proves security identity.
- Do not admit an effective-dated security master, strict PIT source, or broad-universe mapping.
- Continue to a common-role comparison and official standard-taxonomy retrieval (Phase 337).

**Controls:** F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No alpha/return, bootstrap/LOO, chronological OOS or holdout test. No production, universe, capital or parameter changes. No data purchase.
