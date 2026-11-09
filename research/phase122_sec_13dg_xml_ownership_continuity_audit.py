#!/usr/bin/env python3
"""Descriptive ownership-continuity audit for SEC 13D/13G XML amendment pairs.

Consumes immutable Phase 84, 120 and 121 artifacts. It does not infer trades,
sum joint filers, estimate returns, or perform feature/alpha tests.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
import xml.etree.ElementTree as ET

AMOUNT_TOL = 0.01
PERCENT_TOL = 1e-8

def norm_name(value):
    return re.sub(r"[^A-Z0-9]+", " ", str(value or "").upper()).strip()

def number(value):
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def xml_root(raw):
    for block in re.findall(r"<XML>(.*?)</XML>", raw, re.I | re.S):
        if "edgarSubmission" not in block:
            continue
        try:
            return ET.fromstring(block.strip())
        except ET.ParseError:
            continue
    return None

def values(node, tag):
    return [
        e.text.strip() for e in node.iter()
        if e.tag.split("}")[-1].lower() == tag.lower()
        and e.text and e.text.strip()
    ]

def first(node, *tags):
    for tag in tags:
        found = values(node, tag)
        if found:
            return found[0]
    return None

def parse_people(raw, family):
    root = xml_root(raw)
    if root is None:
        return None
    node_tag = "reportingPersonInfo" if family == "13D" else "coverPageHeaderReportingPersonDetails"
    people = []
    for node in root.iter():
        if node.tag.split("}")[-1] != node_tag:
            continue
        name = first(node, "reportingPersonName")
        if not name:
            continue
        if family == "13D":
            amount = first(node, "aggregateAmountOwned")
            pct = first(node, "percentOfClass")
            cik = first(node, "reportingPersonCIK")
            group = first(node, "memberOfGroup")
        else:
            amount = first(node, "reportingPersonBeneficiallyOwnedAggregateNumberOfShares")
            pct = first(node, "classPercent")
            cik = None
            group = None
        people.append({
            "name": name,
            "name_key": norm_name(name),
            "cik": re.sub(r"\D", "", cik).zfill(10) if cik and re.sub(r"\D", "", cik) else None,
            "amount": number(amount),
            "percent": number(pct),
            "group": (group or "").strip().lower() or None,
            "sole_vote": number(first(node, "soleVotingPower")),
            "shared_vote": number(first(node, "sharedVotingPower")),
            "sole_dispositive": number(first(node, "soleDispositivePower")),
            "shared_dispositive": number(first(node, "sharedDispositivePower")),
        })
    return people

def unique_name_map(people):
    counts = Counter(p["name_key"] for p in people)
    if any(v > 1 for v in counts.values()):
        return None
    return {p["name_key"]: p for p in people}

def group_overlap_pairs(people, family):
    if family != "13D":
        return []
    grouped = defaultdict(list)
    for p in people:
        if p["group"] in {"a", "b"} and p["amount"] is not None and p["percent"] is not None:
            grouped[p["group"]].append(p)
    overlaps = []
    for group, members in grouped.items():
        for left, right in combinations(members, 2):
            if abs(left["amount"] - right["amount"]) <= AMOUNT_TOL and abs(left["percent"] - right["percent"]) <= PERCENT_TOL:
                overlaps.append({
                    "group_flag": group,
                    "left_name": left["name"],
                    "right_name": right["name"],
                    "amount": left["amount"],
                    "percent": left["percent"],
                })
    return overlaps

def load_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--phase84-dir", type=Path, required=True)
    p.add_argument("--phase120-dir", type=Path, required=True)
    p.add_argument("--phase121-dir", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    a = p.parse_args()

    phase120 = json.loads((a.phase120_dir / "phase120_predecessor_audit.json").read_text(encoding="utf-8"))
    phase121 = json.loads((a.phase121_dir / "phase121_security_identity_adjudication.json").read_text(encoding="utf-8"))
    manifest = load_csv(a.manifest)
    current_meta = {r["accession"]: r for r in load_csv(a.phase84_dir / "pilot_header_validation.csv")}
    p120_by_current = {r["current_accession"]: r for r in phase120["results"]}
    p121_by_current = {r["current_accession"]: r for r in phase121["results"]}

    if len(manifest) != 45 or len({r["current_accession"] for r in manifest}) != 45:
        raise ValueError("expected 45 unique current/predecessor links")
    if phase120.get("predecessor_downloads_validated") != 45 or phase120.get("download_or_accession_failures") != 0:
        raise ValueError("Phase 120 artifact is not the validated 45/45 predecessor archive")
    if phase121.get("raw_hash_validation_count") != 45 or phase121.get("phase120_header_identity_pass_count") != 45:
        raise ValueError("Phase 121 artifact did not validate all 45 raw hashes and SEC headers")
    if len(current_meta) < 600 or len(p120_by_current) != 45 or len(p121_by_current) != 45:
        raise ValueError("unexpected Phase 84/120/121 input dimensions")

    owner_rows, pair_rows, overlap_rows = [], [], []
    eligible_pairs = 0
    previous_xml_pairs = 0
    previous_legacy_pairs = 0
    excluded_security_pairs = 0
    current_raw_hashes = previous_raw_hashes = 0

    for row in manifest:
        current_acc = row["current_accession"]
        previous_acc = row["previous_accession"]
        family = row["current_form"].upper().replace("SCHEDULE ", "SC ").split("/")[0].replace("SC ", "")
        if family not in {"13D", "13G"}:
            raise ValueError(f"unsupported form family for {current_acc}: {family}")
        m = current_meta.get(current_acc)
        r120 = p120_by_current.get(current_acc)
        r121 = p121_by_current.get(current_acc)
        if not m or not r120 or not r121:
            raise ValueError(f"missing immutable metadata for {current_acc}")
        current_rel = row["current_raw_file"]
        if m.get("raw_file") != current_rel:
            raise ValueError(f"Phase 84 path mismatch for {current_acc}")
        current_path = a.phase84_dir / current_rel
        if not current_path.is_file() or sha256(current_path) != m.get("source_sha256"):
            raise ValueError(f"Phase 84 raw SHA-256 mismatch for {current_acc}")
        current_raw_hashes += 1

        previous_rel = "predecessor_submissions/" + previous_acc.replace("-", "") + ".txt"
        previous_path = a.phase120_dir / previous_rel
        selected = r120.get("selected_archive_path")
        selected_meta = next((x for x in r120.get("candidate_paths", []) if x.get("path") == selected and x.get("valid")), None)
        if not selected_meta or not previous_path.is_file() or sha256(previous_path) != selected_meta.get("sha256"):
            raise ValueError(f"Phase 120 raw SHA-256 mismatch for {previous_acc}")
        previous_raw_hashes += 1

        current_raw = current_path.read_text(encoding="utf-8", errors="replace")
        previous_raw = previous_path.read_text(encoding="utf-8", errors="replace")
        current_people = parse_people(current_raw, family)
        previous_people = parse_people(previous_raw, family)
        if current_people is None:
            raise ValueError(f"current filing lacks expected {family} XML: {current_acc}")
        if previous_people is None:
            previous_legacy_pairs += 1
            continue
        previous_xml_pairs += 1

        identity = r121.get("security_status")
        if identity != "CUSIP_MATCH":
            excluded_security_pairs += 1
            continue
        if r121.get("current_cusip") != r121.get("previous_cusip"):
            raise ValueError(f"Phase 121 CUSIP_MATCH is not literal equality for {current_acc}")

        current_map = unique_name_map(current_people)
        previous_map = unique_name_map(previous_people)
        if current_map is None or previous_map is None:
            pair_rows.append({
                "current_accession": current_acc, "previous_accession": previous_acc,
                "family": family, "security_status": identity,
                "pair_status": "AMBIGUOUS_DUPLICATE_REPORTING_PERSON_NAME",
                "current_person_count": len(current_people), "previous_person_count": len(previous_people),
                "matched_person_count": 0,
            })
            continue

        shared = sorted(set(current_map) & set(previous_map))
        eligible_pairs += 1
        pair_rows.append({
            "current_accession": current_acc, "previous_accession": previous_acc,
            "family": family, "security_status": identity, "pair_status": "DESCRIPTIVE_XML_PAIR",
            "current_person_count": len(current_people), "previous_person_count": len(previous_people),
            "matched_person_count": len(shared),
        })

        for period, people in (("CURRENT", current_people), ("PREVIOUS", previous_people)):
            for ov in group_overlap_pairs(people, family):
                overlap_rows.append({
                    "current_accession": current_acc, "previous_accession": previous_acc,
                    "family": family, "period": period, **ov,
                    "interpretation": "IDENTICAL_REPORTED_VALUES_WITHIN_GROUP_FLAG; DO_NOT_SUM_OR_INFER_UNIQUE_HOLDERS",
                })

        for name_key in shared:
            c = current_map[name_key]
            q = previous_map[name_key]
            amount_delta = c["amount"] - q["amount"] if c["amount"] is not None and q["amount"] is not None else None
            percent_delta = c["percent"] - q["percent"] if c["percent"] is not None and q["percent"] is not None else None
            cik_match = (c["cik"] == q["cik"]) if c["cik"] and q["cik"] else None
            owner_rows.append({
                "current_accession": current_acc, "previous_accession": previous_acc,
                "family": family, "reporting_person": c["name"], "current_person_cik": c["cik"],
                "previous_person_cik": q["cik"], "person_cik_match": cik_match,
                "current_group_flag": c["group"], "previous_group_flag": q["group"],
                "current_amount_owned": c["amount"], "previous_amount_owned": q["amount"],
                "amount_delta": amount_delta,
                "amount_changed": abs(amount_delta) > AMOUNT_TOL if amount_delta is not None else None,
                "current_percent_class": c["percent"], "previous_percent_class": q["percent"],
                "percent_point_delta": percent_delta,
                "percent_changed": abs(percent_delta) > PERCENT_TOL if percent_delta is not None else None,
                "current_sole_voting_power": c["sole_vote"], "previous_sole_voting_power": q["sole_vote"],
                "current_sole_dispositive_power": c["sole_dispositive"], "previous_sole_dispositive_power": q["sole_dispositive"],
                "interpretation": "REPORTED_BENEFICIAL_OWNERSHIP_SNAPSHOT_DELTA_NOT_OBSERVED_TRADE_FLOW",
            })

    if current_raw_hashes != 45 or previous_raw_hashes != 45:
        raise ValueError("not all 45 current and predecessor raw submissions passed SHA-256 checks")
    if (previous_xml_pairs, previous_legacy_pairs, excluded_security_pairs, eligible_pairs) != (21, 24, 1, 20):
        raise ValueError(
            "unexpected XML/security eligibility counts: "
            f"{previous_xml_pairs}/{previous_legacy_pairs}/{excluded_security_pairs}/{eligible_pairs}"
        )
    if len(owner_rows) != 59:
        raise ValueError(f"expected 59 shared reporting-person links, got {len(owner_rows)}")

    amount_changed = sum(r["amount_changed"] is True for r in owner_rows)
    percent_changed = sum(r["percent_changed"] is True for r in owner_rows)
    if (amount_changed, percent_changed, len(overlap_rows)) != (34, 43, 24):
        raise ValueError(
            f"unexpected ownership/group diagnostics: amount={amount_changed}, "
            f"percent={percent_changed}, group_overlap_pairs={len(overlap_rows)}"
        )

    family_pairs = Counter(r["family"] for r in pair_rows if r["pair_status"] == "DESCRIPTIVE_XML_PAIR")
    family_links = Counter(r["family"] for r in owner_rows)
    summary = {
        "phase": "122-sec-13dg-xml-ownership-continuity-audit",
        "status": "PASS_DESCRIPTIVE_WITH_CAVEATS",
        "manifest_links": len(manifest),
        "current_raw_sha256_validated": current_raw_hashes,
        "predecessor_raw_sha256_validated": previous_raw_hashes,
        "previous_xml_pairs": previous_xml_pairs,
        "previous_legacy_html_pairs_excluded": previous_legacy_pairs,
        "xml_pairs_excluded_for_nonmatching_cusip": excluded_security_pairs,
        "eligible_exact_cusip_xml_pairs": eligible_pairs,
        "eligible_pairs_by_family": dict(family_pairs),
        "matched_reporting_person_links": len(owner_rows),
        "person_links_by_family": dict(family_links),
        "amount_links_comparable": sum(r["amount_delta"] is not None for r in owner_rows),
        "amount_links_changed": amount_changed,
        "percent_links_comparable": sum(r["percent_point_delta"] is not None for r in owner_rows),
        "percent_links_changed": percent_changed,
        "person_cik_matches": sum(r["person_cik_match"] is True for r in owner_rows),
        "person_cik_comparisons": sum(r["person_cik_match"] is not None for r in owner_rows),
        "within_group_identical_amount_percent_pairs": len(overlap_rows),
        "group_overlap_rule": "diagnostic only; never sum reporting-person rows or infer distinct beneficial owners from group flag",
        "limitations": [
            "Only 20 exact-CUSIP XML predecessor pairs from a stratified pilot are eligible; this is not a population estimate.",
            "The 24 legacy HTML predecessor filings are excluded from ownership-field comparison; parser absence is not position absence.",
            "The one XML predecessor with a nonmatching CUSIP is excluded even though its issuer/filer lineage passes; Phase 121 separately documents the suspected predecessor CUSIP mis-key.",
            "Reporting-person names are the common matching key; 13G XML does not provide per-person CIK in this schema and name matching is not a permanent identity key.",
            "Reported aggregate shares and percent of class are snapshots, not transaction-level flows; changes may reflect transfers, group attribution, denominator changes, conversions, or reporting corrections.",
            "13D group flags and repeated reported amounts can overlap; do not sum joint filers or treat repeated rows as independent positions.",
            "CUSIP equality is a conservative sample-level identity gate, not a substitute for a complete effective-dated CUSIP/issuer/security crosswalk.",
            "SEC acceptance time is not independently verified public dissemination time; use the conservative next-session convention until proven otherwise.",
            "No returns, predictive features, alpha tests, vendor purchases, or production changes are performed."
        ],
    }

    a.output_dir.mkdir(parents=True, exist_ok=True)
    (a.output_dir / "phase122_ownership_continuity_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    for filename, rows in (
        ("phase122_person_ownership_deltas.csv", owner_rows),
        ("phase122_pair_summary.csv", pair_rows),
        ("phase122_group_overlap_diagnostics.csv", overlap_rows),
    ):
        if rows:
            fields = list(dict.fromkeys(k for r in rows for k in r))
            with (a.output_dir / filename).open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
