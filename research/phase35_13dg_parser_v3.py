"""Schema-aware SEC Schedule 13D/13G parsing primitives.

Identity fields are intentionally separate. A reporting-person set fingerprint is
not an economic-group identifier; group continuity requires explicit filing
lineage and legal/group evidence.
"""
from __future__ import annotations
import hashlib, html, re, xml.etree.ElementTree as ET

FORM_SET = {"SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"}

def lname(tag):
    return tag.rsplit("}", 1)[-1].split(":")[-1].lower()

def txt(node):
    if node is None:
        return None
    value = " ".join("".join(node.itertext()).split())
    return value or None

def children(node, name):
    if node is None:
        return []
    name = name.lower()
    return [x for x in list(node) if lname(x.tag) == name]

def child(node, name):
    xs = children(node, name)
    return xs[0] if xs else None

def child_text(node, name):
    return txt(child(node, name))

def descendants(node, name):
    if node is None:
        return []
    name = name.lower()
    return [x for x in node.iter() if x is not node and lname(x.tag) == name]

def descendant_texts(node, name):
    return [txt(x) for x in descendants(node, name) if txt(x)]

def path(node, *names):
    cur = node
    for name in names:
        cur = child(cur, name)
        if cur is None:
            return None
    return cur

def path_text(node, *names):
    return txt(path(node, *names))

def _reporting_person_13d(node):
    return {
        "cik": child_text(node, "reportingPersonCIK"),
        "cik_not_present_flag": child_text(node, "reportingPersonNoCIK"),
        "name": child_text(node, "reportingPersonName"),
        "group_marker": child_text(node, "memberOfGroup"),
        "aggregate": child_text(node, "aggregateAmountOwned"),
        "percent": child_text(node, "percentOfClass"),
        "sole_voting": child_text(node, "soleVotingPower"),
        "shared_voting": child_text(node, "sharedVotingPower"),
        "sole_dispositive": child_text(node, "soleDispositivePower"),
        "shared_dispositive": child_text(node, "sharedDispositivePower"),
        "types": descendant_texts(node, "typeOfReportingPerson") + descendant_texts(node, "fundType"),
        "schema": "13D_reportingPersonInfo",
    }

def _reporting_person_13g(node):
    shares = child(node, "reportingPersonBeneficiallyOwnedNumberOfShares")
    return {
        # The 13G schema uses reportingCik, not reportingPersonCIK.
        "cik": child_text(node, "reportingCik"),
        "cik_not_present_flag": child_text(node, "reportingCikNotPresentInEdgarFlag"),
        "name": child_text(node, "reportingPersonName"),
        # The 13G schema uses memberGroup, not memberOfGroup.
        "group_marker": child_text(node, "memberGroup"),
        "aggregate": child_text(node, "reportingPersonBeneficiallyOwnedAggregateNumberOfShares"),
        "percent": child_text(node, "classPercent"),
        "sole_voting": child_text(shares, "soleVotingPower"),
        "shared_voting": child_text(shares, "sharedVotingPower"),
        "sole_dispositive": child_text(shares, "soleDispositivePower"),
        "shared_dispositive": child_text(shares, "sharedDispositivePower"),
        "types": descendant_texts(node, "typeOfReportingPerson"),
        "schema": "13G_coverPageHeaderReportingPersonDetails",
    }

def parse_xml(raw):
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    root = ET.fromstring(raw)
    header = child(root, "headerData")
    if header is None:
        header = root
    form_data = child(root, "formData")
    if form_data is None:
        form_data = root
    submission_type = child_text(header, "submissionType") or child_text(root, "submissionType")
    form_norm = (submission_type or "").upper().replace("SCHEDULE ", "SC ").strip()
    is_13g = "13G" in form_norm or "schedule13g" in (root.tag or "").lower()

    cover = child(form_data, "coverPageHeader")
    if cover is None:
        cover = child(root, "coverPageHeader")
    issuer = child(cover, "issuerInfo")
    if issuer is None:
        issuer_nodes = descendants(form_data, "issuerInfo")
        issuer = issuer_nodes[0] if issuer_nodes else None

    if is_13g:
        people_nodes = children(form_data, "coverPageHeaderReportingPersonDetails")
        if not people_nodes:
            people_nodes = descendants(form_data, "coverPageHeaderReportingPersonDetails")
        people = [_reporting_person_13g(x) for x in people_nodes]
        event_date = child_text(cover, "eventDateRequiresFilingThisStatement")
        cusips = descendant_texts(issuer, "issuerCusip") + descendant_texts(issuer, "issuerCusipNumber")
        filing_person = path_text(form_data, "items", "item2", "filingPersonName")
        purpose = None
        group_text = path_text(form_data, "items", "item8", "identificationAndClassificationOfGroupMembers")
        group_dissolution = path_text(form_data, "items", "item9", "groupDissolutionNotice")
    else:
        reporting_container = child(form_data, "reportingPersons")
        people_nodes = children(reporting_container, "reportingPersonInfo")
        if not people_nodes:
            people_nodes = descendants(form_data, "reportingPersonInfo")
        people = [_reporting_person_13d(x) for x in people_nodes]
        event_date = child_text(cover, "dateOfEvent")
        cusips = descendant_texts(issuer, "issuerCUSIP") + descendant_texts(issuer, "issuerCUSIPNumber")
        filing_person = path_text(form_data, "items1To7", "item2", "filingPersonName")
        purpose = path_text(form_data, "items1To7", "item4", "transactionPurpose")
        group_text = None
        group_dissolution = None

    cusips = list(dict.fromkeys(x.strip().upper() for x in cusips if x and x.strip()))
    filer_credentials = descendants(header, "filerCredentials")
    filer_cik = child_text(filer_credentials[0], "cik") if filer_credentials else None
    rules = descendant_texts(cover, "designateRulePursuantThisScheduleFiled")
    return {
        "submission_type": submission_type,
        "schema_version": child_text(root, "schemaVersion"),
        "filer_cik": filer_cik.zfill(10) if filer_cik and filer_cik.isdigit() else filer_cik,
        "previous_accession": child_text(header, "previousAccessionNumber"),
        "subject_issuer_cik": child_text(issuer, "issuerCIK") or child_text(issuer, "issuerCik"),
        "subject_issuer_name": child_text(issuer, "issuerName"),
        "subject_issuer_cusips": cusips,
        "event_date": event_date,
        "filing_person_name": filing_person,
        "designated_rules": rules,
        "reporting_persons": people,
        "purpose_text": purpose,
        "group_members_text": group_text,
        "group_dissolution_text": group_dissolution,
    }

def legacy_text(raw):
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    raw = re.sub(r"(?i)<\s*(?:br|/?p|/?tr|/?td|/?div|/?li)\b[^>]*>", "\n", raw)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw).replace("\xa0", " ")
    return re.sub(r"[ \t\r\f\v]+", " ", raw)

def parse_legacy(raw):
    text = legacy_text(raw)
    people = [m.group(1).strip() for m in re.finditer(
        r"(?im)^\s*Item\s*1\s*:\s*Reporting\s+Person\s*[-:]\s*(.+?)\s*$", text)]
    lines = [x.strip() for x in text.splitlines()]
    for i, line in enumerate(lines):
        if re.search(r"name\s+of\s+reporting\s+person", line, re.I):
            for nxt in lines[i+1:i+5]:
                if nxt and not re.fullmatch(r"[\d|()\ -]+", nxt):
                    people.append(nxt.strip())
                    break
    m = re.search(r"(?i)CUSIP(?:\s*(?:No\.?|Number|#))?\s*[:#]?\s*([A-Z0-9]{8,9})", text)
    cusip = m.group(1) if m else None
    m = re.search(r"(?is)Item\s*4\.?\s*(?:Purpose of Transaction)?\s*:?\s*(.{20,8000}?)(?=\n\s*Item\s*5\b)", text)
    purpose = re.sub(r"\s+", " ", m.group(1)).strip() if m else None
    m = re.search(r"(?is)(?:previously\s+filed\s+accession|previous\s+accession\s+number|accession\s+(?:number|no\.?))\s*[:#]?\s*(\d{10}-\d{2}-\d{6})", text)
    predecessor = m.group(1) if m else None
    return {
        "reporting_person_names": list(dict.fromkeys(people)),
        "cusip": cusip,
        "purpose_text": purpose,
        "explicit_predecessor": predecessor,
        "joint_filing_agreement": bool(re.search(r"(?i)JOINT FILING AGREEMENT|RULE 13d-1\(k\)\(1\) AGREEMENT", text)),
    }

def parse_index(raw):
    text = legacy_text(raw)
    flat = re.sub(r"\s+", " ", text).strip()
    out = {
        "filed_by_name": None, "filed_by_cik": None,
        "subject_name": None, "subject_cik": None,
        "accepted_at": None, "filing_date": None,
        "form": None, "accession": None,
    }
    lines = [re.sub(r"\s+", " ", x).strip() for x in text.splitlines() if x.strip()]
    for label, key in (("Filed by", "filed_by"), ("Subject", "subject")):
        found = False
        for line in lines:
            m = re.search(rf"(?i)^(.{{1,180}}?)\s*\({label}\)\s*CIK:\s*(\d{{6,10}})", line)
            if m:
                out[key+"_name"] = m.group(1).strip(" |\t")
                out[key+"_cik"] = m.group(2).zfill(10)
                found = True
                break
        if not found:
            m = re.search(rf"(?is)(.{{1,100}}?)\s*\({label}\)\s*CIK:\s*(\d{{6,10}})", flat)
            if m:
                out[key+"_name"] = re.sub(r"\s+", " ", m.group(1)).strip(" |\t")
                out[key+"_cik"] = m.group(2).zfill(10)
    m = re.search(r"(?i)Accepted\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", flat)
    if m: out["accepted_at"] = m.group(1)
    m = re.search(r"(?i)Filing Date\s+(\d{4}-\d{2}-\d{2})", flat)
    if m: out["filing_date"] = m.group(1)
    m = re.search(r"(?i)Form\s+(SCHEDULE\s+13[DG](?:/A)?)", flat)
    if m: out["form"] = " ".join(m.group(1).upper().split())
    m = re.search(r"(?i)SEC Accession No\.\s*(\d{10}-\d{2}-\d{6})", flat)
    if m: out["accession"] = m.group(1)
    return out

def parse_master_index(raw):
    """Return SC 13D/G master-index rows, preserving filer as filer."""
    if isinstance(raw, bytes):
        raw = raw.decode("latin-1", "replace")
    lines = raw.lstrip("\ufeff").splitlines()
    header = None
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("cik|company name|form type|date filed|filename"):
            header = i
            break
    if header is None:
        raise ValueError("SEC master.idx pipe-delimited header not found")
    rows = []
    for line in lines[header+1:]:
        if not line.strip() or line.startswith("---"):
            continue
        parts = line.split("|", 4)
        if len(parts) != 5:
            continue
        filer_cik, company, form, filed, filename = [x.strip() for x in parts]
        form = " ".join(form.upper().split())
        if form not in FORM_SET:
            continue
        accession_match = re.search(r"(\d{10}-\d{2}-\d{6})\.txt$", filename, re.I)
        if not accession_match:
            continue
        accession = accession_match.group(1)
        archive_dir = filename.rsplit("/", 1)[0].lstrip("/")
        rows.append({
            "filer_cik": filer_cik.zfill(10),
            "filer_company_name": company,
            "form": form,
            "filing_date": filed,
            "accession": accession,
            "filename": filename,
            "index_url": f"https://www.sec.gov/Archives/{archive_dir}/{accession}-index.htm",
        })
    return rows

def reporting_person_set_fingerprint(people):
    """Hash a complete CIK set; never call this an economic-group identifier."""
    if not people:
        return None
    ciks = []
    for person in people:
        cik = (person.get("cik") or "").strip()
        if not cik or not cik.isdigit():
            return None
        ciks.append(cik.zfill(10))
    canonical = "|".join(sorted(set(ciks)))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

# Backwards-compatible alias. It fingerprints a reporting-person set only.
def group_fingerprint(people):
    return reporting_person_set_fingerprint(people)
