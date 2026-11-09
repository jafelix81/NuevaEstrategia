"""Phase 212: Form 144 route-identifiability audit (metadata-only, fail-closed)."""
from __future__ import annotations

SAMPLE = (
    {"ticker": "PINS", "accession": "0001921094-26-000697", "intermediary": "Charles Schwab & Co., Inc.", "header": "Name and Address of the Broker", "crd": "5393"},
    {"ticker": "SCHW", "accession": "0001949846-26-000451", "intermediary": "THE CHARLES SCHWAB CORPORATION", "header": "Name and Address of the Broker", "crd": None},
    {"ticker": "SNOW", "accession": "0001959173-26-005295", "intermediary": "Fidelity Brokerage Services LLC", "header": "Name and Address of the Broker", "crd": "7784"},
    {"ticker": "ANET", "accession": "0001959173-26-006426", "intermediary": "Fidelity Brokerage Services LLC", "header": "Name and Address of the Broker", "crd": "7784"},
    {"ticker": "RUN", "accession": "0001921094-26-000789", "intermediary": "Charles Schwab & Co., Inc.", "header": "Name and Address of the Broker", "crd": "5393"},
)

def infer_transaction_route(record: dict) -> str:
    """Never infer Rule 144 route from intermediary name or firm registration."""
    return "UNKNOWN_NOT_ENCODED"

def audit(sample=SAMPLE) -> dict:
    rows = tuple(sample)
    if len(rows) != 5:
        raise ValueError("Phase 212 is a fixed five-document semantic pilot")
    if len({r["accession"] for r in rows}) != len(rows):
        raise ValueError("duplicate accession")
    headers = {r["header"] for r in rows}
    if headers != {"Name and Address of the Broker"}:
        raise ValueError("unexpected intermediary field semantics")
    if any(infer_transaction_route(r) != "UNKNOWN_NOT_ENCODED" for r in rows):
        raise AssertionError("route inference must remain fail-closed")
    names = {r["intermediary"].casefold() for r in rows}
    crds = {r["crd"] for r in rows if r["crd"] is not None}
    unresolved = [r for r in rows if r["crd"] is None]
    return {
        "sample_rows": len(rows),
        "same_intermediary_header_rows": len(rows),
        "explicit_route_flag_rows": 0,
        "distinct_intermediary_strings": len(names),
        "rows_with_current_finra_identity_candidate": sum(r["crd"] is not None for r in rows),
        "distinct_crd_candidates": sorted(crds),
        "unresolved_rows": len(unresolved),
        "routes": sorted({infer_transaction_route(r) for r in rows}),
        "route_specific_test_authorized": False,
        "mixed_route_event_conditional_only": True,
        "alpha_test_authorized": False,
        "holdout_used": False,
        "f80_frozen": True,
    }

if __name__ == "__main__":
    import json
    print(json.dumps(audit(), indent=2))
