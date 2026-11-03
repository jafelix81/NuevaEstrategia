"""Validate filer-to-reporting-person candidate links against explicit 13D CIKs.

The name crosswalk itself never consumes reporting-person CIKs. This audit joins its
selected reporting-person index back to the source XML-derived JSON and uses explicit
13D reporting CIKs as held-out identity labels. 13G matches are coverage-only because
its reportingCik is optional and was absent in the tested sample.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_cik(value):
    if value is None:
        return None
    raw = str(value).strip()
    if raw.endswith(".0"):
        raw = raw[:-2]
    digits = "".join(ch for ch in raw if ch.isdigit())
    return digits.zfill(10) if digits else None


def precision_label(family: str, candidate_cik, explicit_cik):
    """Return (eligible, correct, mismatch) for a selected person link."""
    if family != "13D" or not explicit_cik:
        return False, False, False
    candidate = normalize_cik(candidate_cik)
    explicit = normalize_cik(explicit_cik)
    if candidate is None:
        return True, False, True
    return True, candidate == explicit, candidate != explicit


def audit(root: Path, quarters: list[str], detail_path: Path) -> dict:
    detail = load_csv(detail_path)
    out = []
    for quarter in quarters:
        qdir = root / quarter
        target_rows = load_csv(qdir / "target_subject_filings_xml.csv")
        global_rows = load_csv(qdir / "global_subject_census_xml.csv")
        target = {r["accession"]: r for r in target_rows}
        global_map = {r["accession"]: r for r in global_rows}
        selected = [r for r in detail if r.get("quarter") == quarter]
        seen = set()
        for d in selected:
            sample = d.get("sample")
            if sample not in {"target_subject", "non_target_validation"}:
                continue
            key = (sample, d.get("accession"))
            if key in seen:
                raise ValueError(f"Duplicate crosswalk detail key: {quarter} {key}")
            seen.add(key)
            source = target.get(d.get("accession")) if sample == "target_subject" else global_map.get(d.get("accession"))
            if source is None:
                raise ValueError(f"Missing source accession: {quarter} {sample} {d.get('accession')}")
            try:
                people = json.loads(source.get("reporting_persons_json") or "[]")
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid reporting_persons_json: {d.get('accession')}") from exc
            status = d.get("crosswalk_status") or ""
            idx_text = d.get("matched_reporting_person_index") or ""
            person = None
            if status == "unique_exact_normalized_name_match":
                if not idx_text:
                    raise ValueError(f"Unique match missing person index: {d.get('accession')}")
                idx = int(float(idx_text))
                if idx < 0 or idx >= len(people):
                    raise ValueError(f"Reporting-person index out of range: {d.get('accession')}")
                person = people[idx]
            form = d.get("form") or ""
            family = "13D" if "13D" in form else "13G" if "13G" in form else "OTHER"
            candidate = d.get("candidate_reporting_person_cik") or ""
            explicit = person.get("cik") if person else None
            eligible, correct, mismatch = precision_label(family, candidate, explicit)
            out.append({
                "quarter": quarter,
                "sample": sample,
                "family": family,
                "accession": d.get("accession"),
                "status": status,
                "candidate_cik": normalize_cik(candidate),
                "matched_person_name": person.get("name") if person else None,
                "explicit_person_cik": normalize_cik(explicit),
                "precision_validation_eligible": eligible,
                "precision_match": correct if eligible else None,
                "precision_mismatch": mismatch if eligible else None,
            })

    grouped = defaultdict(list)
    for row in out:
        grouped[(row["quarter"], row["sample"], row["family"])].append(row)

    summaries = []
    for (quarter, sample, family), rows in sorted(grouped.items()):
        matched = [r for r in rows if r["status"] == "unique_exact_normalized_name_match"]
        eligible = [r for r in rows if r["precision_validation_eligible"]]
        summaries.append({
            "quarter": quarter,
            "sample": sample,
            "family": family,
            "filings": len(rows),
            "unique_name_matches": len(matched),
            "unique_name_match_rate": len(matched) / len(rows) if rows else None,
            "ambiguous": sum(r["status"] == "ambiguous_multiple_reporting_person_matches" for r in rows),
            "no_match": sum(r["status"] == "no_exact_normalized_name_match" for r in rows),
            "explicit_13d_cik_validation_n": len(eligible),
            "explicit_13d_cik_matches": sum(bool(r["precision_match"]) for r in eligible),
            "explicit_13d_cik_mismatches": sum(bool(r["precision_mismatch"]) for r in eligible),
            "explicit_13d_cik_precision": (
                sum(bool(r["precision_match"]) for r in eligible) / len(eligible) if eligible else None
            ),
            "interpretation": (
                "Held-out explicit-CIK validation" if family == "13D"
                else "Coverage only; no explicit reporting-person CIK available for validation"
            ),
        })

    all_eligible = [r for r in out if r["precision_validation_eligible"]]
    result = {
        "status": "PASS" if not any(r["precision_mismatch"] for r in all_eligible) else "FAIL",
        "quarters": quarters,
        "rows_audited": len(out),
        "explicit_13d_validation_n": len(all_eligible),
        "explicit_13d_validation_matches": sum(bool(r["precision_match"]) for r in all_eligible),
        "explicit_13d_validation_mismatches": sum(bool(r["precision_mismatch"]) for r in all_eligible),
        "13g_precision_claim": False,
        "economic_group_inference": False,
        "forward_returns_used": False,
        "summaries": summaries,
        "detail": out,
    }
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--quarters", default="2025Q2,2025Q3")
    ap.add_argument("--detail", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = audit(args.root, [x.strip() for x in args.quarters.split(",") if x.strip()], args.detail)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "detail"}, indent=2), flush=True)
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
