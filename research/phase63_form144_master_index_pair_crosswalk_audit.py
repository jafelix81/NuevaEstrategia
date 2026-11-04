#!/usr/bin/env python3
"""Diagnostic audit of SEC Form 144 master-index CIK pairs against primary XML.

This is an identity-structure diagnostic, not a historical coverage estimator.
The candidate CIK set is a current ticker mapping and is not a PIT universe.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


def norm_cik(value: object) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    return digits.zfill(10) if digits else ""


def parse_cik_list(value: object) -> list[str]:
    return sorted({norm_cik(x) for x in str(value or "").split(";") if norm_cik(x)})


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def load_candidate_ciks(rows: list[dict[str, str]]) -> set[str]:
    candidates: set[str] = set()
    for row in rows:
        candidates.update(parse_cik_list(row.get("candidate_ciks", "")))
    return candidates


def audit_rows(
    census_rows: list[dict[str, str]],
    xml_rows: list[dict[str, str]],
    candidate_ciks: set[str],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    census_by_accession = {r.get("accession", ""): r for r in census_rows}
    output: list[dict[str, object]] = []
    missing_census = 0

    for xml in xml_rows:
        accession = xml.get("accession", "")
        census = census_by_accession.get(accession)
        if census is None:
            missing_census += 1
            continue

        pair = parse_cik_list(census.get("master_index_ciks", ""))
        issuer = norm_cik(xml.get("xml_issuer_cik", ""))
        filer = norm_cik(xml.get("xml_filer_cik", ""))
        issuer_in_pair = bool(issuer and issuer in pair)
        filer_in_pair = bool(filer and filer in pair)
        candidate_pair = sorted(set(pair) & candidate_ciks)
        exactly_one_candidate = len(candidate_pair) == 1
        unique_candidate = candidate_pair[0] if exactly_one_candidate else ""
        unique_candidate_role = (
            "issuer" if exactly_one_candidate and unique_candidate == issuer
            else "filer" if exactly_one_candidate and unique_candidate == filer
            else "unresolved" if exactly_one_candidate
            else "ambiguous" if len(candidate_pair) > 1
            else "none"
        )

        output.append({
            "accession": accession,
            "form": xml.get("form", ""),
            "master_index_pair_size": len(pair),
            "master_index_ciks": ";".join(pair),
            "xml_issuer_cik": issuer,
            "xml_filer_cik": filer,
            "issuer_in_master_pair": issuer_in_pair,
            "filer_in_master_pair": filer_in_pair,
            "both_xml_ciks_in_pair": issuer_in_pair and filer_in_pair and issuer != filer,
            "candidate_ciks_in_pair": ";".join(candidate_pair),
            "candidate_count_in_pair": len(candidate_pair),
            "unique_candidate_role": unique_candidate_role,
        })

    matched = [r for r in output if r["candidate_count_in_pair"] == 1]
    by_form: dict[str, dict[str, int]] = {}
    for form in sorted({str(r["form"]) for r in output}):
        subset = [r for r in output if r["form"] == form]
        by_form[form] = {
            "rows": len(subset),
            "both_xml_ciks_in_pair": sum(bool(r["both_xml_ciks_in_pair"]) for r in subset),
            "exactly_one_candidate": sum(r["candidate_count_in_pair"] == 1 for r in subset),
            "unique_candidate_is_issuer": sum(r["unique_candidate_role"] == "issuer" for r in subset),
            "unique_candidate_is_filer": sum(r["unique_candidate_role"] == "filer" for r in subset),
            "ambiguous_candidate_pair": sum(r["unique_candidate_role"] == "ambiguous" for r in subset),
        }

    summary: dict[str, object] = {
        "xml_sample_rows": len(xml_rows),
        "rows_joined_to_master_index": len(output),
        "missing_census_rows": missing_census,
        "candidate_cik_count": len(candidate_ciks),
        "master_pair_size_distribution": dict(Counter(str(r["master_index_pair_size"]) for r in output)),
        "both_xml_ciks_in_master_pair": sum(bool(r["both_xml_ciks_in_pair"]) for r in output),
        "exactly_one_candidate_in_pair": len(matched),
        "unique_candidate_is_issuer": sum(r["unique_candidate_role"] == "issuer" for r in matched),
        "unique_candidate_is_filer": sum(r["unique_candidate_role"] == "filer" for r in matched),
        "unique_candidate_unresolved": sum(r["unique_candidate_role"] == "unresolved" for r in matched),
        "ambiguous_candidate_pairs": sum(r["unique_candidate_role"] == "ambiguous" for r in output),
        "no_candidate_in_pair": sum(r["unique_candidate_role"] == "none" for r in output),
        "by_form": by_form,
        "interpretation_limit": (
            "The XML sample is not a random coverage sample. Candidate CIKs are current ticker mappings, "
            "not a point-in-time historical universe. This diagnostic validates pair membership and "
            "observed role concordance only."
        ),
    }
    return summary, output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--census", required=True)
    parser.add_argument("--xml-sample", required=True)
    parser.add_argument("--ticker-candidates", required=True)
    parser.add_argument("--output", default="phase63_form144_pair_audit")
    args = parser.parse_args()

    census = read_csv(args.census)
    xml_rows = read_csv(args.xml_sample)
    candidates = load_candidate_ciks(read_csv(args.ticker_candidates))
    summary, detail = audit_rows(census, xml_rows, candidates)

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if detail:
        with open(out / "detail.csv", "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(detail[0]))
            writer.writeheader()
            writer.writerows(detail)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
