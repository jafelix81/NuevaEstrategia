#!/usr/bin/env python3
"""Phase 337: common-role XBRL label comparison and official US-GAAP member labels.

Consumes the immutable Phase 336 artifact. It compares only label roles that
exist for both QNames, separately records one-sided roles, and retrieves the
official 2021/2022 US-GAAP label and documentation linkbases for the STR
standard-taxonomy members. No QName or security alias is merged.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PHASE = 337
SOURCE_RUN_ID = 43228785778
SOURCE_ARTIFACT_ID = 13949661332
SOURCE_ARTIFACT_SHA256 = "da010b603e408260d3191b9af9d70de3f03537db97e1dfd0a98ed8c3b8739dac"
SOURCE_AUDIT_JSON_SHA256 = "17f088d14cdc1f271afc54ab0fd968237b615902ac06a763b2f45a4a37e9aa5e"
TARGET_SYMBOLS = {"PCG-PB", "PCG-PE", "PCG-PG", "PCG-PH", "PCG-PI", "STR"}
STANDARD_RESOURCES = {
    "2021": {
        "namespace": "http://fasb.org/us-gaap/2021-01-31",
        "labels": "https://xbrl.fasb.org/us-gaap/2021/elts/us-gaap-lab-2021-01-31.xml",
        "documentation": "https://xbrl.fasb.org/us-gaap/2021/elts/us-gaap-doc-2021-01-31.xml",
    },
    "2022": {
        "namespace": "http://fasb.org/us-gaap/2022",
        "labels": "https://xbrl.fasb.org/us-gaap/2022/elts/us-gaap-lab-2022.xml",
        "documentation": "https://xbrl.fasb.org/us-gaap/2022/elts/us-gaap-doc-2022.xml",
    },
}
STANDARD_TARGETS = {"CommonClassAMember", "CommonStockMember"}
MAX_RESOURCE_BYTES = 25_000_000


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def local_name(value: str) -> str:
    return str(value).rsplit("}", 1)[-1].split(":")[-1]


def attr(element, wanted: str) -> str:
    for key, value in element.attrib.items():
        if local_name(key) == wanted:
            return str(value)
    return ""


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def parse_linkbase(raw: bytes, target_locals: set[str]) -> dict[str, list[dict]]:
    root = ET.fromstring(raw)
    labels = defaultdict(list)
    for link in root.iter():
        if local_name(link.tag) != "labelLink":
            continue
        locators, resources, arcs = {}, {}, []
        for child in list(link):
            lname = local_name(child.tag)
            if lname == "loc":
                locators[attr(child, "label")] = attr(child, "href")
            elif lname == "label":
                resource_id = attr(child, "label")
                resources[resource_id] = {
                    "role": attr(child, "role"),
                    "language": attr(child, "lang"),
                    "text": clean_text("".join(child.itertext())),
                }
            elif lname == "labelArc":
                arcs.append((attr(child, "from"), attr(child, "to")))
        for source_id, target_id in arcs:
            href = locators.get(source_id, "")
            fragment = href.rsplit("#", 1)[-1]
            for member_local in target_locals:
                if (
                    fragment == member_local
                    or fragment.endswith("_" + member_local)
                    or fragment.endswith(":" + member_local)
                ):
                    resource = resources.get(target_id)
                    if resource and resource["text"]:
                        labels[member_local].append(resource)
    output = {}
    for member_local, rows in labels.items():
        unique = {
            (x["role"], x["language"], x["text"]): x
            for x in rows
        }
        output[member_local] = [unique[k] for k in sorted(unique)]
    return output


def fetch_resource(url: str, retries: int = 2) -> dict:
    last_error = ""
    for attempt in range(retries + 1):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "SmartMoneyResearch-Phase337/1.0",
                    "Accept": "application/xml,text/xml,*/*",
                },
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                status = int(response.status)
                raw = response.read(MAX_RESOURCE_BYTES + 1)
            if len(raw) > MAX_RESOURCE_BYTES:
                return {
                    "url": url, "http_status": status, "error": "RESOURCE_SIZE_LIMIT",
                    "bytes": len(raw), "sha256": "", "labels": {},
                }
            if status != 200:
                return {
                    "url": url, "http_status": status, "error": "HTTP_STATUS_NOT_200",
                    "bytes": len(raw), "sha256": sha256_bytes(raw), "labels": {},
                }
            return {
                "url": url, "http_status": status, "error": "",
                "bytes": len(raw), "sha256": sha256_bytes(raw), "raw": raw,
            }
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            last_error = f"{type(exc).__name__}:{str(exc)[:180]}"
            if attempt < retries:
                time.sleep(2 ** attempt)
    return {
        "url": url, "http_status": 0, "error": last_error or "FETCH_FAILED",
        "bytes": 0, "sha256": "", "labels": {},
    }


def role_map(rows: list[dict]) -> dict[tuple[str, str], set[str]]:
    output = defaultdict(set)
    for row in rows:
        role = str(row.get("role") or "")
        language = str(row.get("language") or "")
        text = clean_text(row.get("text") or "")
        if role and text:
            output[(role, language)].add(text)
    return dict(output)


def compare_common_role_labels(member_profiles: list[dict]) -> dict:
    if len(member_profiles) < 2:
        return {
            "common_role_keys": [],
            "matching_common_role_keys": [],
            "conflicting_common_role_keys": [],
            "one_sided_role_keys": [],
            "common_role_labels_match": False,
        }
    maps = [role_map(x.get("labels") or []) for x in member_profiles]
    key_sets = [set(x) for x in maps]
    common = set.intersection(*key_sets) if key_sets else set()
    all_keys = set.union(*key_sets) if key_sets else set()
    matching, conflicting = [], []
    for key in sorted(common):
        values = [tuple(sorted(m.get(key, set()))) for m in maps]
        if len(set(values)) == 1:
            matching.append(key)
        else:
            conflicting.append(key)
    one_sided = all_keys - common
    return {
        "common_role_keys": [{"role": k[0], "language": k[1]} for k in sorted(common)],
        "matching_common_role_keys": [{"role": k[0], "language": k[1]} for k in matching],
        "conflicting_common_role_keys": [{"role": k[0], "language": k[1]} for k in conflicting],
        "one_sided_role_keys": [{"role": k[0], "language": k[1]} for k in sorted(one_sided)],
        "common_role_labels_match": bool(common) and not conflicting,
    }


def compare_cross_role_text(member_profiles: list[dict]) -> list[str]:
    text_sets = [
        {clean_text(x.get("text") or "") for x in (member.get("labels") or [])
         if clean_text(x.get("text") or "")}
        for member in member_profiles
    ]
    if not text_sets:
        return []
    return sorted(set.intersection(*text_sets))


def compare_documentation(member_profiles: list[dict]) -> str:
    sets = [tuple(sorted(set(x.get("documentation") or []))) for x in member_profiles]
    if not sets or not all(sets):
        return "INCOMPLETE"
    return "MATCH" if len(set(sets)) == 1 else "CONFLICT"


def classify_alias(common: dict, documentation_status: str) -> str:
    if not common["common_role_keys"]:
        return "NO_COMMON_ROLE_LABEL_EVIDENCE_NOT_MERGED"
    if common["conflicting_common_role_keys"]:
        return "COMMON_ROLE_LABEL_CONFLICT_NOT_MERGED"
    if documentation_status == "MATCH":
        return "CANDIDATE_COMMON_ROLE_LABEL_AND_DOCUMENTATION_MATCH_NOT_MERGED"
    if documentation_status == "CONFLICT":
        return "COMMON_ROLE_LABEL_MATCH_DOCUMENTATION_CONFLICT_NOT_MERGED"
    return "CANDIDATE_COMMON_ROLE_LABEL_MATCH_DOCUMENTATION_INCOMPLETE_NOT_MERGED"


def load_source(path: Path) -> dict:
    digest = sha256_file(path)
    if digest != SOURCE_AUDIT_JSON_SHA256:
        raise ValueError(f"phase336_audit_json_sha256_mismatch:{digest}")
    source = json.loads(path.read_text(encoding="utf-8"))
    provenance = source.get("source", {})
    if (
        source.get("phase") != 336
        or provenance.get("phase") != 334
        or provenance.get("artifact_id") != 13947767592
        or provenance.get("run_id") != 43226260351
    ):
        raise ValueError("phase336_source_not_admitted")
    if source.get("summary", {}).get("documents_with_instance_hash_match") != 8:
        raise ValueError("phase336_instance_hash_gate_failed")
    if source.get("summary", {}).get("raw_qnames_merged") != 0:
        raise ValueError("phase336_raw_qname_merge_detected")
    return source


def run_audit(input_path: Path, output_dir: Path, skip_network: bool = False) -> dict:
    source = load_source(input_path)
    standard_resources = []
    standard_labels_by_version = {}
    standard_docs_by_version = {}

    if not skip_network:
        for version, spec in STANDARD_RESOURCES.items():
            for kind, url in (("labels", spec["labels"]), ("documentation", spec["documentation"])):
                got = fetch_resource(url)
                row = {
                    "version": version,
                    "kind": kind,
                    "url": url,
                    "http_status": got["http_status"],
                    "error": got["error"],
                    "bytes": got["bytes"],
                    "sha256": got["sha256"],
                    "target_qnames": [],
                }
                if got.get("raw") is not None:
                    try:
                        parsed = parse_linkbase(got["raw"], STANDARD_TARGETS)
                        row["target_qnames"] = sorted(parsed)
                        if kind == "labels":
                            standard_labels_by_version[version] = parsed
                        else:
                            standard_docs_by_version[version] = parsed
                    except ET.ParseError as exc:
                        row["error"] = f"XML_PARSE_ERROR:{str(exc)[:180]}"
                standard_resources.append(row)
    else:
        for version, spec in STANDARD_RESOURCES.items():
            for kind, url in (("labels", spec["labels"]), ("documentation", spec["documentation"])):
                standard_resources.append({
                    "version": version, "kind": kind, "url": url,
                    "http_status": 0, "error": "SKIPPED_OFFLINE",
                    "bytes": 0, "sha256": "", "target_qnames": [],
                })

    grouped = defaultdict(lambda: defaultdict(list))
    for row in source.get("member_evidence", []):
        symbol = str(row.get("symbol") or "").upper()
        if symbol in TARGET_SYMBOLS:
            grouped[symbol][str(row.get("member_qname") or "")].append(row)

    alias_profiles = []
    for symbol, members in sorted(grouped.items()):
        member_profiles = []
        for qname, rows in sorted(members.items()):
            labels = {
                (x.get("role", ""), x.get("language", ""), x.get("text", ""))
                for row in rows for x in row.get("labels", [])
                if x.get("text")
            }
            documentation = {
                clean_text(text)
                for row in rows for text in row.get("schema_documentation", [])
                if clean_text(text)
            }
            namespace_uris = sorted({x.get("namespace_uri", "") for x in rows if x.get("namespace_uri")})
            standard_version = next(
                (version for version, spec in STANDARD_RESOURCES.items()
                 if spec["namespace"] in namespace_uris),
                None,
            )
            local = qname.split(":", 1)[-1]
            standard_label_rows = []
            standard_doc_rows = []
            if standard_version:
                standard_label_rows = standard_labels_by_version.get(standard_version, {}).get(local, [])
                standard_doc_rows = standard_docs_by_version.get(standard_version, {}).get(local, [])
                labels.update(
                    (x.get("role", ""), x.get("language", ""), x.get("text", ""))
                    for x in standard_label_rows if x.get("text")
                )
                documentation.update(
                    clean_text(x.get("text", ""))
                    for x in standard_doc_rows
                    if clean_text(x.get("text", ""))
                    and "documentation" in str(x.get("role", "")).lower()
                )
            titles = {
                clean_text(title)
                for row in rows for title in row.get("same_context_security_titles", [])
                if clean_text(title)
            }
            member_profiles.append({
                "member_qname": qname,
                "accessions": sorted({x.get("accession", "") for x in rows}),
                "filing_dates": sorted({x.get("filing_date", "") for x in rows}),
                "namespace_uris": namespace_uris,
                "standard_taxonomy_version": standard_version,
                "labels": [
                    {"role": a, "language": b, "text": c}
                    for a, b, c in sorted(labels) if a and c
                ],
                "documentation": sorted(documentation),
                "standard_label_resource_rows": len(standard_label_rows),
                "standard_documentation_resource_rows": len(standard_doc_rows),
                "same_context_security_titles": sorted(titles),
                "instance_hashes_match": all(x.get("instance_hash_match") is True for x in rows),
            })
        common = compare_common_role_labels(member_profiles)
        cross_role_text_overlap = compare_cross_role_text(member_profiles)
        docs_status = compare_documentation(member_profiles)
        title_sets = [tuple(x["same_context_security_titles"]) for x in member_profiles]
        title_status = (
            "MATCH" if title_sets and all(title_sets) and len(set(title_sets)) == 1
            else "CONFLICT_OR_INCOMPLETE"
        )
        alias_profiles.append({
            "symbol": symbol,
            "member_count": len(member_profiles),
            "members": member_profiles,
            **common,
            "cross_role_text_overlap": cross_role_text_overlap,
            "documentation_comparison": docs_status,
            "same_context_title_comparison": title_status,
            "classification": classify_alias(common, docs_status),
            "raw_qnames_merged": False,
        })

    qname_profiles = [m for x in alias_profiles for m in x["members"]]
    summary = {
        "target_symbols": sorted(TARGET_SYMBOLS),
        "alias_groups": len(alias_profiles),
        "unique_member_qnames": len(qname_profiles),
        "groups_with_common_role_label_match": sum(
            x["common_role_labels_match"] for x in alias_profiles
        ),
        "groups_with_common_role_label_conflict": sum(
            bool(x["conflicting_common_role_keys"]) for x in alias_profiles
        ),
        "groups_with_cross_role_text_overlap": sum(
            bool(x["cross_role_text_overlap"]) for x in alias_profiles
        ),
        "groups_without_common_role_label": sum(
            not x["common_role_keys"] for x in alias_profiles
        ),
        "groups_with_same_context_title_match": sum(
            x["same_context_title_comparison"] == "MATCH" for x in alias_profiles
        ),
        "groups_with_documentation_match": sum(
            x["documentation_comparison"] == "MATCH" for x in alias_profiles
        ),
        "standard_resources_expected": 4,
        "standard_resources_retrieved": sum(
            bool(x["sha256"]) and not x["error"] for x in standard_resources
        ),
        "standard_resources_failed_or_skipped": sum(
            not bool(x["sha256"]) or bool(x["error"]) for x in standard_resources
        ),
        "standard_member_label_qnames_found": len({
            (version, local)
            for version, data in standard_labels_by_version.items()
            for local in STANDARD_TARGETS if data.get(local)
        }),
        "standard_member_documentation_qnames_found": len({
            (version, local)
            for version, data in standard_docs_by_version.items()
            for local in STANDARD_TARGETS if data.get(local)
        }),
        "raw_qnames_merged": 0,
    }
    status = "COMPLETED_COMMON_ROLE_TAXONOMY_AUDIT"
    if summary["standard_resources_failed_or_skipped"]:
        status = "COMPLETED_WITH_EXPLICIT_STANDARD_TAXONOMY_QUARANTINES"
    controls = {
        "f80_frozen": True,
        "strict_pit_admitted": False,
        "security_master_admitted": False,
        "universe_coverage_admitted": False,
        "alpha_test_run": False,
        "return_test_run": False,
        "bootstrap_loo_run": False,
        "chronological_oos_run": False,
        "holdout_used": False,
        "production_changed": False,
        "universe_changed": False,
        "capital_changed": False,
        "parameters_changed": False,
        "raw_qnames_merged": False,
        "data_purchased": False,
    }
    result = {
        "phase": PHASE,
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "phase": 336,
            "run_id": SOURCE_RUN_ID,
            "artifact_id": SOURCE_ARTIFACT_ID,
            "artifact_sha256": SOURCE_ARTIFACT_SHA256,
            "audit_json_sha256": sha256_file(input_path),
        },
        "summary": summary,
        "standard_taxonomy_resources": standard_resources,
        "alias_profiles": alias_profiles,
        "controls": controls,
        "interpretation": {
            "compare_only_common_role_language_pairs": True,
            "one_sided_label_roles_are_not_conflicts": True,
            "same_context_titles_are_separate_supporting_evidence": True,
            "documentation_linkbase_is_separate_from_schema_inline_documentation": True,
            "raw_qnames_preserved": True,
            "no_alias_merge_authorized": True,
            "taxonomy_labels_are_identity_metadata_not_market_signals": True,
            "filing_date_is_not_first_public_timestamp": True,
            "no_effective_dated_security_master_admitted": True,
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "phase337_common_role_taxonomy_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "phase337_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_csv(output_dir / "phase337_alias_profiles.csv", alias_profiles)
    write_csv(output_dir / "phase337_standard_taxonomy_resources.csv", standard_resources)
    print("PHASE337_STATUS=" + status)
    print("PHASE337_SUMMARY=" + json.dumps(summary, sort_keys=True))
    print("PHASE337_ALIAS_PROFILES=" + json.dumps(alias_profiles, sort_keys=True))
    return result


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                k: json.dumps(v, ensure_ascii=False, sort_keys=True)
                if isinstance(v, (dict, list)) else v
                for k, v in row.items()
            })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", type=Path, default=Path("phase336_source/phase336_taxonomy_linkbase_audit.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("phase337_output"))
    parser.add_argument("--skip-network", action="store_true")
    args = parser.parse_args()
    run_audit(args.input_json, args.output_dir, skip_network=args.skip_network)


if __name__ == "__main__":
    main()
