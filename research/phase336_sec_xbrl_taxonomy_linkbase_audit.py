#!/usr/bin/env python3
"""Phase 336: retrieve SEC XBRL taxonomy schemas and label linkbases for alias candidates.

The source is the pinned Phase 334 artifact. This phase re-fetches only the
eight documents containing the six multi-QName symbols, verifies each XBRL
instance against its Phase 334 SHA-256, and retrieves the schema/linkbase
resources referenced by those filings. It never merges QNames.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import xml.etree.ElementTree as ET

from research.phase328_sec_collision_prior_filing_xbrl_pilot import SECClient

PHASE = 336
SOURCE_RUN_ID = 43226260351
SOURCE_ARTIFACT_ID = 13947767592
SOURCE_AUDIT_JSON_SHA256 = "c360eac0358ca4181664ecf18ea6699bccedd0e3d2251ea936c296a19588bc46"
TARGET_SYMBOLS = {"PCG-PB", "PCG-PE", "PCG-PG", "PCG-PH", "PCG-PI", "STR"}
STANDARD_PREFIXES = {"us-gaap", "dei", "srt", "country", "currency", "exch"}


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


def parse_instance_metadata(raw: bytes) -> dict:
    root = ET.fromstring(raw)
    namespaces = {}
    for _, item in ET.iterparse(io.BytesIO(raw), events=("start-ns",)):
        prefix, uri = item
        namespaces[prefix or ""] = uri
    schema_refs = []
    for element in root.iter():
        if local_name(element.tag) == "schemaRef":
            href = attr(element, "href")
            if href:
                schema_refs.append(href)
    return {
        "namespaces": namespaces,
        "schema_refs": sorted(set(schema_refs)),
    }


def parse_index_items(raw: bytes) -> list[dict]:
    obj = json.loads(raw)
    items = obj.get("directory", {}).get("item", []) or []
    return [
        {
            "name": str(x.get("name") or ""),
            "type": str(x.get("type") or "").upper(),
            "size": x.get("size"),
            "last_modified": x.get("last-modified", ""),
        }
        for x in items if x.get("name")
    ]


def parse_schema(raw: bytes) -> dict:
    root = ET.fromstring(raw)
    target_namespace = str(root.attrib.get("targetNamespace") or "")
    elements = {}
    imports = []
    linkbase_refs = []
    for element in root.iter():
        lname = local_name(element.tag)
        if lname == "element":
            name = str(element.attrib.get("name") or "")
            if name:
                docs = sorted({
                    clean_text("".join(x.itertext()))
                    for x in element.iter() if local_name(x.tag) == "documentation"
                    and clean_text("".join(x.itertext()))
                })
                elements[name] = {
                    "name": name,
                    "type": str(element.attrib.get("type") or ""),
                    "substitution_group": str(element.attrib.get("substitutionGroup") or ""),
                    "abstract": str(element.attrib.get("abstract") or ""),
                    "documentation": docs,
                }
        elif lname in {"import", "include"}:
            imports.append({
                "namespace": str(element.attrib.get("namespace") or ""),
                "schema_location": str(element.attrib.get("schemaLocation") or ""),
            })
        elif lname == "linkbaseRef":
            href = attr(element, "href")
            if href:
                linkbase_refs.append(href)
    return {
        "target_namespace": target_namespace,
        "elements": elements,
        "imports": imports,
        "linkbase_refs": sorted(set(linkbase_refs)),
    }


def parse_label_linkbase(raw: bytes, target_locals: set[str]) -> dict:
    root = ET.fromstring(raw)
    labels = defaultdict(list)
    for link in root.iter():
        if local_name(link.tag) != "labelLink":
            continue
        locators = {}
        resources = {}
        arcs = []
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
                if fragment == member_local or fragment.endswith("_" + member_local) or fragment.endswith(":" + member_local):
                    resource = resources.get(target_id)
                    if resource and resource["text"]:
                        labels[member_local].append(resource)
    for member_local, rows in labels.items():
        unique = {
            (x["role"], x["language"], x["text"]): x for x in rows
        }
        labels[member_local] = [unique[k] for k in sorted(unique)]
    return dict(labels)


def preferred_label_texts(rows: list[dict]) -> list[str]:
    preferred = [
        x["text"] for x in rows
        if x.get("role", "").rstrip("/").endswith("/label") and x.get("text")
    ]
    if not preferred:
        preferred = [x["text"] for x in rows if x.get("text")]
    return sorted(set(preferred))


def classify_alias_evidence(member_profiles: list[dict]) -> str:
    if not member_profiles:
        return "NO_MEMBER_EVIDENCE"
    label_sets = [tuple(x.get("preferred_label_texts") or []) for x in member_profiles]
    if not all(label_sets):
        return "LINKBASE_LABEL_INCOMPLETE_NOT_MERGED"
    if len(set(label_sets)) != 1:
        return "LABELS_DIFFER_OR_AMBIGUOUS_NOT_MERGED"
    definition_sets = [tuple(x.get("schema_documentation") or []) for x in member_profiles]
    if all(definition_sets) and len(set(definition_sets)) == 1:
        return "CANDIDATE_LABEL_AND_SCHEMA_DOC_MATCH_NOT_MERGED"
    return "CANDIDATE_LABEL_MATCH_DEFINITION_NOT_CONFIRMED_NOT_MERGED"


def load_source(path: Path) -> dict:
    digest = sha256_file(path)
    if digest != SOURCE_AUDIT_JSON_SHA256:
        raise ValueError(f"phase334_audit_json_sha256_mismatch:{digest}")
    source = json.loads(path.read_text(encoding="utf-8"))
    if source.get("phase") != 334 or source.get("status") != "COMPLETED_STRATIFIED_CLASS_BINDING_AUDIT":
        raise ValueError("phase334_source_not_admitted")
    return source


def _fetch(client: SECClient, url: str, max_bytes: int) -> dict:
    raw, status, error, headers = client.get(url, max_bytes=max_bytes)
    return {
        "raw": raw,
        "http_status": status,
        "error": error,
        "headers": headers,
        "sha256": sha256_bytes(raw) if raw is not None else "",
        "bytes": len(raw) if raw is not None else 0,
    }


def _schema_resources(client: SECClient, base: str, instance_meta: dict,
                      index_items: list[dict]) -> tuple[list[dict], list[dict]]:
    schema_urls = {urljoin(base, href) for href in instance_meta["schema_refs"]}
    for item in index_items:
        if item["type"].endswith(".SCH") or item["name"].lower().endswith(".xsd"):
            schema_urls.add(urljoin(base, item["name"]))
    fetched_schemas = {}
    pending = list(sorted(schema_urls))
    while pending and len(fetched_schemas) < 20:
        url = pending.pop(0)
        if url in fetched_schemas:
            continue
        got = _fetch(client, url, 6_000_000)
        row = {
            "url": url, "http_status": got["http_status"], "error": got["error"],
            "sha256": got["sha256"], "bytes": got["bytes"],
            "target_namespace": "", "elements": {}, "imports": [], "linkbase_refs": [],
        }
        if got["raw"] is not None:
            try:
                parsed = parse_schema(got["raw"])
                row.update(parsed)
                for imp in parsed["imports"]:
                    loc = imp.get("schema_location")
                    ns = imp.get("namespace")
                    if loc and ns and ns in instance_meta["namespaces"].values():
                        child_url = urljoin(url, loc)
                        if child_url not in fetched_schemas and child_url not in pending:
                            pending.append(child_url)
            except ET.ParseError as exc:
                row["error"] = f"SCHEMA_XML_PARSE_ERROR:{str(exc)[:120]}"
        fetched_schemas[url] = row

    index_label_urls = {
        urljoin(base, item["name"])
        for item in index_items
        if item["type"].endswith(".LAB") or item["name"].lower().endswith("_lab.xml")
    }
    label_urls_by_schema = {}
    for url, schema in fetched_schemas.items():
        urls = {
            urljoin(url, href) for href in schema.get("linkbase_refs", [])
            if "lab" in href.lower()
        }
        if not urls and schema.get("target_namespace"):
            prefixes = [
                prefix for prefix, uri in instance_meta["namespaces"].items()
                if uri == schema["target_namespace"]
            ]
            if any(prefix not in STANDARD_PREFIXES for prefix in prefixes):
                urls = set(index_label_urls)
        label_urls_by_schema[url] = urls

    fetched_labels = []
    seen = set()
    for schema_url, urls in label_urls_by_schema.items():
        schema_ns = fetched_schemas[schema_url].get("target_namespace", "")
        target_locals = set(fetched_schemas[schema_url].get("elements", {}))
        for url in sorted(urls):
            if url in seen:
                continue
            seen.add(url)
            got = _fetch(client, url, 12_000_000)
            row = {
                "url": url, "schema_url": schema_url, "schema_target_namespace": schema_ns,
                "http_status": got["http_status"], "error": got["error"],
                "sha256": got["sha256"], "bytes": got["bytes"], "labels": {},
            }
            if got["raw"] is not None:
                try:
                    row["labels"] = parse_label_linkbase(got["raw"], target_locals)
                except ET.ParseError as exc:
                    row["error"] = f"LABEL_XML_PARSE_ERROR:{str(exc)[:120]}"
            fetched_labels.append(row)
    return list(fetched_schemas.values()), fetched_labels


def run_audit(input_path: Path, output_dir: Path, email: str) -> dict:
    source = load_source(input_path)
    if not email or "@" not in email:
        raise ValueError("SEC_CONTACT_EMAIL_secret_required")

    selected = []
    for doc in source["documents"]:
        symbols = {
            str(x.get("symbol") or "").upper()
            for x in doc.get("symbol_facts", [])
        }
        if symbols & TARGET_SYMBOLS:
            selected.append(doc)
    selected.sort(key=lambda x: (x["filing_date"], x["accession"]))
    if len(selected) != 8:
        raise ValueError(f"unexpected_alias_document_count:{len(selected)}")

    client = SECClient(email, min_interval=0.25)
    document_audits = []
    member_evidence = []
    all_schema_rows = []
    all_label_rows = []
    for doc in selected:
        cik_path = str(int(doc["issuer_cik"]))
        accession_compact = doc["accession"].replace("-", "")
        base = f"https://www.sec.gov/Archives/edgar/data/{cik_path}/{accession_compact}/"
        index = _fetch(client, base + "index.json", 2_000_000)
        index_items = []
        if index["raw"] is not None:
            try:
                index_items = parse_index_items(index["raw"])
            except (ValueError, TypeError):
                index["error"] = "INDEX_JSON_PARSE_ERROR"
        instance_name = str(doc.get("document_name") or "")
        instance = _fetch(client, base + instance_name, 8_000_000) if instance_name else {
            "raw": None, "http_status": 0, "error": "MISSING_DOCUMENT_NAME", "sha256": "", "bytes": 0
        }
        expected_hash = str(doc.get("actual_sha256") or doc.get("expected_sha256") or "").lower()
        instance_hash_match = bool(instance["raw"] is not None and instance["sha256"] == expected_hash)
        ns_meta = {"namespaces": {}, "schema_refs": []}
        schemas, labels = [], []
        if instance["raw"] is not None and instance_hash_match:
            try:
                ns_meta = parse_instance_metadata(instance["raw"])
                schemas, labels = _schema_resources(client, base, ns_meta, index_items)
            except ET.ParseError as exc:
                ns_meta["parse_error"] = f"INSTANCE_XML_PARSE_ERROR:{str(exc)[:120]}"
        all_schema_rows.extend([{**x, "accession": doc["accession"]} for x in schemas])
        all_label_rows.extend([{**x, "accession": doc["accession"]} for x in labels])

        schema_by_ns = {
            x.get("target_namespace"): x for x in schemas if x.get("target_namespace")
        }
        label_map_by_ns = defaultdict(lambda: defaultdict(list))
        for label_file in labels:
            ns = label_file.get("schema_target_namespace", "")
            for local, rows in label_file.get("labels", {}).items():
                label_map_by_ns[ns][local].extend(rows)

        associations = {
            (str(x.get("symbol") or "").upper(), str(x.get("context_ref") or "")): x
            for x in doc.get("context_associations", [])
        }
        doc_members = []
        if instance_hash_match:
            for sf in doc.get("symbol_facts", []):
                symbol = str(sf.get("symbol") or "").upper()
                if symbol not in TARGET_SYMBOLS:
                    continue
                context = str(sf.get("context_ref") or "")
                assoc = associations.get((symbol, context), {})
                titles = sorted(set(assoc.get("same_context_security_titles") or []))
                for axis_member in sf.get("class_axis_members", []):
                    qname = str(axis_member).split("=", 1)[-1]
                    prefix, _, local = qname.partition(":")
                    namespace_uri = ns_meta["namespaces"].get(prefix, "")
                    schema = schema_by_ns.get(namespace_uri, {})
                    element = schema.get("elements", {}).get(local, {})
                    labels_for_member = label_map_by_ns.get(namespace_uri, {}).get(local, [])
                    label_keys = {
                        (x.get("role", ""), x.get("language", ""), x.get("text", ""))
                        for x in labels_for_member
                    }
                    labels_for_member = [
                        {"role": a, "language": b, "text": c}
                        for a, b, c in sorted(label_keys)
                    ]
                    evidence = {
                        "symbol": symbol,
                        "accession": doc["accession"],
                        "filing_date": doc["filing_date"],
                        "issuer_cik": doc["issuer_cik"],
                        "class_axis_member": axis_member,
                        "member_qname": qname,
                        "prefix": prefix,
                        "namespace_uri": namespace_uri,
                        "schema_url": schema.get("url", ""),
                        "schema_sha256": schema.get("sha256", ""),
                        "schema_target_namespace": schema.get("target_namespace", ""),
                        "schema_element_found": bool(element),
                        "schema_element_type": element.get("type", ""),
                        "schema_element_substitution_group": element.get("substitution_group", ""),
                        "schema_documentation": element.get("documentation", []),
                        "label_linkbase_urls": sorted({
                            x.get("url", "") for x in labels
                            if x.get("schema_target_namespace") == namespace_uri
                        }),
                        "labels": labels_for_member,
                        "preferred_label_texts": preferred_label_texts(labels_for_member),
                        "same_context_security_titles": titles,
                        "instance_sha256": instance["sha256"],
                        "instance_hash_match": instance_hash_match,
                    }
                    doc_members.append(evidence)
                    member_evidence.append(evidence)

        document_audits.append({
            "accession": doc["accession"],
            "filing_date": doc["filing_date"],
            "issuer_cik": doc["issuer_cik"],
            "symbols": sorted({str(x.get("symbol") or "").upper() for x in doc.get("symbol_facts", [])
                               if str(x.get("symbol") or "").upper() in TARGET_SYMBOLS}),
            "index_http_status": index["http_status"],
            "index_sha256": index["sha256"],
            "index_item_count": len(index_items),
            "instance_name": instance_name,
            "instance_http_status": instance["http_status"],
            "instance_sha256": instance["sha256"],
            "expected_instance_sha256": expected_hash,
            "instance_hash_match": instance_hash_match,
            "namespace_prefixes": ns_meta.get("namespaces", {}),
            "schema_refs": ns_meta.get("schema_refs", []),
            "schema_files": [{
                "url": x["url"], "http_status": x["http_status"], "sha256": x["sha256"],
                "target_namespace": x["target_namespace"], "error": x["error"],
            } for x in schemas],
            "label_files": [{
                "url": x["url"], "http_status": x["http_status"], "sha256": x["sha256"],
                "schema_target_namespace": x["schema_target_namespace"], "error": x["error"],
            } for x in labels],
            "member_evidence": doc_members,
        })

    grouped = defaultdict(lambda: defaultdict(list))
    for row in member_evidence:
        grouped[row["symbol"]][row["member_qname"]].append(row)
    alias_profiles = []
    for symbol, members in sorted(grouped.items()):
        member_profiles = []
        for qname, rows in sorted(members.items()):
            labels_for_member = sorted({
                (x["role"], x["language"], x["text"])
                for row in rows for x in row["labels"]
            })
            member_profiles.append({
                "member_qname": qname,
                "accessions": sorted({x["accession"] for x in rows}),
                "filing_dates": sorted({x["filing_date"] for x in rows}),
                "namespace_uris": sorted({x["namespace_uri"] for x in rows if x["namespace_uri"]}),
                "schema_hashes": sorted({x["schema_sha256"] for x in rows if x["schema_sha256"]}),
                "schema_element_found_any": any(x["schema_element_found"] for x in rows),
                "schema_documentation": sorted({
                    text for x in rows for text in x["schema_documentation"]
                }),
                "labels": [{"role": a, "language": b, "text": c} for a, b, c in labels_for_member],
                "preferred_label_texts": sorted({
                    text for row in rows for text in row["preferred_label_texts"]
                }),
                "same_context_security_titles": sorted({
                    title for row in rows for title in row["same_context_security_titles"]
                }),
                "all_instance_hashes_match": all(x["instance_hash_match"] for x in rows),
            })
        alias_profiles.append({
            "symbol": symbol,
            "member_count": len(member_profiles),
            "members": member_profiles,
            "label_linkbase_classification": classify_alias_evidence(member_profiles),
            "same_context_titles_across_members": sorted({
                title for x in member_profiles for title in x["same_context_security_titles"]
            }),
            "raw_qnames_merged": False,
        })

    summary = {
        "target_symbols": sorted(TARGET_SYMBOLS),
        "documents_selected": len(selected),
        "documents_with_instance_hash_match": sum(x["instance_hash_match"] for x in document_audits),
        "documents_with_index_200": sum(x["index_http_status"] == 200 for x in document_audits),
        "schema_file_observations": len(all_schema_rows),
        "schema_files_retrieved": sum(bool(x["sha256"]) for x in all_schema_rows),
        "schema_files_failed": sum(not bool(x["sha256"]) for x in all_schema_rows),
        "label_linkbase_observations": len(all_label_rows),
        "label_linkbases_retrieved": sum(bool(x["sha256"]) for x in all_label_rows),
        "label_linkbases_failed": sum(not bool(x["sha256"]) for x in all_label_rows),
        "member_fact_rows": len(member_evidence),
        "unique_member_qnames": len({x["member_qname"] for x in member_evidence}),
        "member_qnames_with_schema_element": len({x["member_qname"] for x in member_evidence if x["schema_element_found"]}),
        "member_qnames_with_preferred_label": len({x["member_qname"] for x in member_evidence if x["preferred_label_texts"]}),
        "alias_groups": len(alias_profiles),
        "alias_groups_with_label_and_schema_doc_match": sum(x["label_linkbase_classification"] == "CANDIDATE_LABEL_AND_SCHEMA_DOC_MATCH_NOT_MERGED" for x in alias_profiles),
        "alias_groups_with_label_match_only": sum(x["label_linkbase_classification"] == "CANDIDATE_LABEL_MATCH_DEFINITION_NOT_CONFIRMED_NOT_MERGED" for x in alias_profiles),
        "alias_groups_with_different_or_ambiguous_labels": sum(x["label_linkbase_classification"] == "LABELS_DIFFER_OR_AMBIGUOUS_NOT_MERGED" for x in alias_profiles),
        "alias_groups_with_incomplete_linkbase_labels": sum(x["label_linkbase_classification"] == "LINKBASE_LABEL_INCOMPLETE_NOT_MERGED" for x in alias_profiles),
        "raw_qnames_merged": 0,
    }
    status = "COMPLETED_TAXONOMY_LINKBASE_AUDIT"
    if (
        summary["documents_with_instance_hash_match"] != len(selected)
        or summary["schema_files_failed"]
        or summary["label_linkbases_failed"]
        or summary["member_qnames_with_preferred_label"] != summary["unique_member_qnames"]
    ):
        status = "COMPLETED_WITH_EXPLICIT_LINKBASE_QUARANTINES"

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
            "phase": 334,
            "run_id": SOURCE_RUN_ID,
            "artifact_id": SOURCE_ARTIFACT_ID,
            "audit_json_sha256": sha256_file(input_path),
        },
        "summary": summary,
        "documents": document_audits,
        "member_evidence": member_evidence,
        "alias_profiles": alias_profiles,
        "schema_files": all_schema_rows,
        "label_linkbases": all_label_rows,
        "controls": controls,
        "interpretation": {
            "taxonomy_labels_and_schema_docs_are_identity_metadata_not_market_signals": True,
            "same_context_security_title_is_not_substituted_for_taxonomy_label": True,
            "raw_qnames_preserved": True,
            "no_alias_merge_authorized": True,
            "filing_date_is_not_first_public_timestamp": True,
            "no_effective_dated_security_master_admitted": True,
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "phase336_taxonomy_linkbase_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "phase336_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_csv(output_dir / "phase336_documents.csv", document_audits)
    write_csv(output_dir / "phase336_member_evidence.csv", member_evidence)
    write_csv(output_dir / "phase336_alias_profiles.csv", alias_profiles)
    write_csv(output_dir / "phase336_schema_files.csv", all_schema_rows)
    write_csv(output_dir / "phase336_label_linkbases.csv", all_label_rows)
    print("PHASE336_STATUS=" + status)
    print("PHASE336_SUMMARY=" + json.dumps(summary, sort_keys=True))
    print("PHASE336_CONTROLS=" + json.dumps(controls, sort_keys=True))
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
    parser.add_argument("--input-json", type=Path,
                        default=Path("phase334_source/phase334-sec-stratified-symbol-class-coverage/phase334_symbol_class_binding_audit.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("phase336_output"))
    parser.add_argument("--email", default=os.environ.get("SEC_CONTACT_EMAIL", ""))
    args = parser.parse_args()
    run_audit(args.input_json, args.output_dir, args.email)


if __name__ == "__main__":
    main()
