#!/usr/bin/env python3
"""Artifact-only SEC 13D/13G schema and amendment-lineage feasibility audit."""
from __future__ import annotations
import argparse, csv, io, json, re, zipfile, unicodedata
from collections import Counter, defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET


def norm(value):
    return re.sub(r"\s+", " ", str(value or "")).strip().upper()


def norm_form(value):
    x = norm(value)
    return "SC " + x[len("SCHEDULE "):] if x.startswith("SCHEDULE ") else x


def family_for_form(value):
    x = norm_form(value)
    if x in {"SC 13D", "SC 13D/A"}: return "13D"
    if x in {"SC 13G", "SC 13G/A"}: return "13G"
    return None


def norm_cik(value):
    x = re.sub(r"\D", "", str(value or ""))
    return x.zfill(10) if x else None


def norm_name(value):
    x = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode().upper()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]+", " ", x)).strip()


def tag_texts(root, tag):
    return [e.text.strip() for e in root.iter()
            if e.tag.split("}")[-1].lower() == tag.lower() and e.text and e.text.strip()]


def first(root, *tags):
    for tag in tags:
        vals = tag_texts(root, tag)
        if vals: return vals[0]
    return None


def parse_xml_block(raw):
    blocks = re.findall(r"<XML>(.*?)</XML>", raw, flags=re.I | re.S)
    block = next((b.strip() for b in blocks if "edgarSubmission" in b), None)
    if not block: raise ValueError("no edgarSubmission XML block")
    return ET.fromstring(block)


def parse_persons(root, family):
    node_name = "reportingPersonInfo" if family == "13D" else "coverPageHeaderReportingPersonDetails"
    nodes = [e for e in root.iter() if e.tag.split("}")[-1] == node_name]
    persons = []
    for node in nodes:
        def pfirst(*tags):
            for tag in tags:
                vals = [e.text.strip() for e in node.iter()
                        if e.tag.split("}")[-1].lower() == tag.lower() and e.text and e.text.strip()]
                if vals: return vals[0]
            return None
        if family == "13D":
            persons.append({
                "cik": norm_cik(pfirst("reportingPersonCIK")),
                "name": pfirst("reportingPersonName"),
                "no_cik_flag": pfirst("reportingPersonNoCIK"),
                "percent": pfirst("percentOfClass"),
                "amount": pfirst("aggregateAmountOwned"),
                "sole_vote": pfirst("soleVotingPower"),
                "shared_vote": pfirst("sharedVotingPower"),
                "sole_dispositive": pfirst("soleDispositivePower"),
                "shared_dispositive": pfirst("sharedDispositivePower"),
                "type": pfirst("typeOfReportingPerson"),
            })
        else:
            persons.append({
                "cik": None,
                "name": pfirst("reportingPersonName"),
                "percent": pfirst("classPercent"),
                "amount": pfirst("reportingPersonBeneficiallyOwnedAggregateNumberOfShares"),
                "sole_vote": pfirst("soleVotingPower"),
                "shared_vote": pfirst("sharedVotingPower"),
                "sole_dispositive": pfirst("soleDispositivePower"),
                "shared_dispositive": pfirst("sharedDispositivePower"),
                "type": pfirst("typeOfReportingPerson"),
            })
    return persons


def security_key(filing):
    if filing.get("issuer_cusip"):
        return "CUSIP:" + norm(filing["issuer_cusip"])
    if filing.get("class_title"):
        return "CLASS:" + norm_name(filing["class_title"])
    return None


def group_signature(filing):
    names = sorted({norm_name(p.get("name")) for p in filing["persons"] if p.get("name")})
    if filing["family"] == "13D":
        ids = sorted({p["cik"] for p in filing["persons"] if p.get("cik")})
        parts = ["CIK:" + x for x in ids] + ["NAME:" + x for x in names]
        return "|".join(parts)
    return "FILER:" + str(filing["filer_cik"]) + "|" + "|".join("NAME:" + x for x in names)


def validate_previous_link(current, index_rows):
    ciks = {x["cik"] for x in index_rows}
    forms = [norm_form(x["form"]) for x in index_rows]
    family_match = any(family_for_form(x) == current["family"] for x in forms)
    date_before = any(x["date"] < current["filing_date"] for x in index_rows if x["date"])
    subject_match = current["issuer_cik"] in ciks
    filer_match = current["filer_cik"] in ciks
    valid = bool(index_rows) and family_match and date_before and subject_match and filer_match
    return {
        "previous_index_rows": len(index_rows), "previous_forms": forms,
        "previous_subject_cik_present": subject_match, "previous_filer_cik_present": filer_match,
        "previous_family_match": family_match, "previous_date_before_current": date_before,
        "validated": valid,
    }


def audit(phase84_zip: Path, phase82_zip: Path):
    filings = []
    with zipfile.ZipFile(phase84_zip) as z84:
        rows = list(csv.DictReader(io.TextIOWrapper(z84.open("pilot_header_validation.csv"), encoding="utf-8-sig", newline="")))
        xml_rows = [r for r in rows if str(r.get("xml_present", "")).lower() == "true"]
        for row in xml_rows:
            raw = z84.read(row["raw_file"]).decode("utf-8", errors="replace")
            root = parse_xml_block(raw)
            family = family_for_form(row.get("header_form"))
            if not family: raise ValueError(f"non-13D/G form in XML sample: {row.get('accession')}")
            issuer_cik = norm_cik(first(root, "issuerCIK", "issuerCik"))
            filer_cik = norm_cik(first(root, "cik"))
            persons = parse_persons(root, family)
            filings.append({
                "accession": row["accession"], "form": norm_form(row["header_form"]), "family": family,
                "filing_date": row.get("header_filing_date", ""),
                "subject_header_cik": norm_cik(row.get("subject_cik")),
                "filer_header_cik": norm_cik(row.get("filer_cik")),
                "issuer_cik": issuer_cik, "filer_cik": filer_cik,
                "issuer_cusip": norm(first(root, "issuerCUSIP", "issuerCusip")),
                "class_title": first(root, "securitiesClassTitle"),
                "event_date": first(root, "dateOfEvent") if family == "13D" else first(root, "eventDateRequiresFilingThisStatement"),
                "previously_filed_flag": first(root, "previouslyFiledFlag"),
                "amendment_no": first(root, "amendmentNo"),
                "previous_accession": first(root, "previousAccessionNumber"),
                "group_members_text": first(root, "identificationAndClassificationOfGroupMembers"),
                "subsidiaries_text": first(root, "subsidiaryIdentificationAndClassification"),
                "persons": persons,
            })

    prev_ids = {x["previous_accession"] for x in filings if x["previous_accession"]}
    prev_map = {x: [] for x in prev_ids}
    index_files = 0
    with zipfile.ZipFile(phase82_zip) as z82:
        names = [n for n in z82.namelist() if n.startswith("raw_master_indexes/") and n.endswith(".idx")]
        index_files = len(names)
        for name in names:
            with z82.open(name) as fh:
                for bline in fh:
                    parts = bline.decode("latin-1", errors="replace").rstrip("\r\n").split("|")
                    if len(parts) < 5: continue
                    match = re.search(r"(\d{10}-\d{2}-\d{6})\.txt$", parts[4])
                    if not match: continue
                    accession = match.group(1)
                    if accession in prev_map:
                        prev_map[accession].append({
                            "cik": norm_cik(parts[0]), "company": parts[1],
                            "form": parts[2], "date": parts[3], "path": parts[4],
                        })

    links = []
    for filing in filings:
        if filing["previous_accession"]:
            links.append({
                "accession": filing["accession"], "form": filing["form"],
                "issuer_cik": filing["issuer_cik"], "filer_cik": filing["filer_cik"],
                "previous_accession": filing["previous_accession"],
                **validate_previous_link(filing, prev_map.get(filing["previous_accession"], [])),
            })

    family_stats = {}
    for family in ("13D", "13G"):
        fs = [x for x in filings if x["family"] == family]
        persons = [p for x in fs for p in x["persons"]]
        def count_field(field): return sum(bool(p.get(field)) for p in persons)
        family_stats[family] = {
            "filings": len(fs), "person_nodes": len(persons),
            "event_date_present": sum(bool(x["event_date"]) for x in fs),
            "amendment_filings": sum(x["form"].endswith("/A") for x in fs),
            "amendment_no_present": sum(bool(x["amendment_no"]) for x in fs),
            "issuer_cik_matches_header": sum(x["issuer_cik"] == x["subject_header_cik"] for x in fs),
            "filer_cik_matches_header": sum(x["filer_cik"] == x["filer_header_cik"] for x in fs),
            "reporting_person_cik_nodes": count_field("cik"),
            "reporting_person_names": count_field("name"),
            "ownership_percent": count_field("percent"),
            "aggregate_owned": count_field("amount"),
            "sole_voting_power": count_field("sole_vote"),
            "shared_voting_power": count_field("shared_vote"),
            "sole_dispositive_power": count_field("sole_dispositive"),
            "shared_dispositive_power": count_field("shared_dispositive"),
            "reporting_person_type": count_field("type"),
            "group_members_text_present": sum(bool(x["group_members_text"]) for x in fs),
            "subsidiaries_text_present": sum(bool(x["subsidiaries_text"]) for x in fs),
        }

    group_counts = {}
    six_cusip_example = None
    for family in ("13D", "13G"):
        fs = [x for x in filings if x["family"] == family]
        no_sec, with_sec = Counter(), Counter()
        no_sec_rows = defaultdict(list)
        for x in fs:
            sig = group_signature(x)
            base = x["issuer_cik"] + "|" + sig
            sec = security_key(x) or "UNRESOLVED_SECURITY"
            no_sec[base] += 1
            with_sec[base + "|" + sec] += 1
            no_sec_rows[base].append(x)
        group_counts[family] = {
            "unique_issuer_reporting_group_keys_without_security": len(no_sec),
            "repeated_groups_without_security": sum(v > 1 for v in no_sec.values()),
            "rows_in_repeated_groups_without_security": sum(v for v in no_sec.values() if v > 1),
            "unique_issuer_reporting_group_security_keys": len(with_sec),
            "repeated_groups_with_security": sum(v > 1 for v in with_sec.values()),
            "rows_in_repeated_groups_with_security": sum(v for v in with_sec.values() if v > 1),
        }
        if family == "13G":
            for base, group in no_sec_rows.items():
                cusips = sorted({x["issuer_cusip"] for x in group if x["issuer_cusip"]})
                if len(group) >= 5 and len(cusips) >= 5:
                    six_cusip_example = {
                        "issuer_cik": group[0]["issuer_cik"], "filer_cik": group[0]["filer_cik"],
                        "reporting_person_names": sorted({p["name"] for x in group for p in x["persons"] if p.get("name")}),
                        "filings": [{"accession": x["accession"], "form": x["form"], "cusip": x["issuer_cusip"], "class_title": x["class_title"], "event_date": x["event_date"], "amendment_no": x["amendment_no"]} for x in group],
                    }
                    break

    cusip_count = sum(bool(x["issuer_cusip"]) for x in filings)
    class_count = sum(bool(x["class_title"]) for x in filings)
    amendment_filings = [x for x in filings if x["form"].endswith("/A")]
    return {
        "phase": "119-sec-13dg-xml-schema-and-lineage-feasibility",
        "status": "PASS_WITH_LINEAGE_CAVEATS" if len(filings) == 200 and all(x["issuer_cik"] == x["subject_header_cik"] and x["filer_cik"] == x["filer_header_cik"] for x in filings) else "FAIL",
        "sample": {"phase84_rows": 600, "xml_rows": len(filings), "non_xml_rows": 600-len(filings), "families": dict(Counter(x["family"] for x in filings)), "phase82_index_files_scanned": index_files},
        "identity": {"issuer_cik_header_matches": sum(x["issuer_cik"] == x["subject_header_cik"] for x in filings), "filer_cik_header_matches": sum(x["filer_cik"] == x["filer_header_cik"] for x in filings), "cusip_present": cusip_count, "class_title_present": class_count},
        "family_schema": family_stats,
        "amendment_lineage": {
            "amendment_filings": len(amendment_filings),
            "amendment_no_present": sum(bool(x["amendment_no"]) for x in amendment_filings),
            "previous_accession_present": len(links),
            "previous_accession_validated_in_phase82_index": sum(x["validated"] for x in links),
            "previous_accession_unresolved": sum(not x["validated"] for x in links),
            "amendments_without_explicit_previous_accession": len(amendment_filings)-len(links),
            "links": links,
        },
        "group_identity": group_counts,
        "same_group_six_security_example": six_cusip_example,
        "forward_returns_used": False, "alpha_test_authorized": False,
        "limitations": [
            "The 200 XML rows are a stratified Phase 84 sample, not a representative estimate of the full historical 13D/G population.",
            "The 400 non-XML rows require a legacy HTML parser; XML-only extraction cannot backfill the 2016–2024 period.",
            "13D and 13G use different XML schemas; a single generic reportingPersonInfo parser misses the 13G reporting-person nodes.",
            "13D reporting-person CIK is missing on some person nodes; 13G reporting-person nodes have names but no per-person CIK, while the filing-level CIK matches the filer.",
            "CUSIP is absent in some filings; class-title fallback is diagnostic only and must be checked for ambiguity before creating a security key.",
            "A previousAccessionNumber is accepted only after prior-index, issuer-CIK, filer-CIK, form-family and chronology checks; unresolved links are not guessed.",
            "SEC acceptance timestamp is not independently verified public dissemination time; use next-session knowledge availability until proven otherwise.",
        ],
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--phase84-zip",type=Path,required=True)
    p.add_argument("--phase82-zip",type=Path,required=True)
    p.add_argument("--output",type=Path,default=Path("phase119_lineage_audit.json"))
    a=p.parse_args()
    result=audit(a.phase84_zip,a.phase82_zip)
    a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in ("amendment_lineage","same_group_six_security_example")},indent=2,ensure_ascii=False))
    if result["status"] != "PASS_WITH_LINEAGE_CAVEATS": raise SystemExit(2)


if __name__ == "__main__": main()
