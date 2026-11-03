"""Conservative SEC Schedule 13D/13G parser primitives.

Separates query/filer/subject/reporting-person identities. Never infers groups
from accession prefixes.
"""
import hashlib
import html
import re
import xml.etree.ElementTree as ET


def lname(tag):
    return tag.rsplit("}", 1)[-1].split(":")[-1].lower()


def txt(node):
    value = " ".join("".join(node.itertext()).split()) if node is not None else ""
    return value or None


def find(node, *names):
    names = {x.lower() for x in names}
    for child in node.iter():
        if lname(child.tag) in names and txt(child):
            return txt(child)
    return None


def parse_xml(raw):
    root = ET.fromstring(raw)
    get = lambda *names: find(root, *names)
    people = []
    for node in root.iter():
        tag = lname(node.tag)
        if tag == "reportingpersoninfo":
            d = {lname(x.tag): txt(x) for x in list(node)}
            people.append({
                "cik": d.get("reportingpersoncik"), "name": d.get("reportingpersonname"),
                "group": d.get("memberofgroup"), "aggregate": d.get("aggregateamountowned"),
                "percent": d.get("percentofclass"), "schema": "13D_reportingPersonInfo",
            })
        elif tag == "coverpageheaderreportingpersondetails":
            types = [txt(x) for x in node.iter() if lname(x.tag) == "typeofreportingperson"]
            people.append({
                "cik": find(node, "reportingPersonCIK"), "name": find(node, "reportingPersonName"),
                "group": find(node, "memberOfGroup"),
                "aggregate": find(node, "reportingPersonBeneficiallyOwnedAggregateNumberOfShares", "aggregateAmountOwned"),
                "percent": find(node, "classPercent", "percentOfClass"),
                "types": "|".join(x for x in types if x), "schema": "13G_coverPageHeaderReportingPersonDetails",
            })
    cusips = []
    for x in root.iter():
        if lname(x.tag) in {"issuercusip", "issuercusipnumber"} and txt(x) and txt(x) not in cusips:
            cusips.append(txt(x))
    purposes = [txt(x) for x in root.iter() if lname(x.tag) in {"transactionpurpose", "purposeoftransaction"} and txt(x)]
    transactions = [txt(x) for x in root.iter() if lname(x.tag) in {"transactiondesc", "transactiondescription"} and txt(x)]
    return {
        "submission_type": get("submissionType"),
        "previous_accession": get("previousAccessionNumber"),
        "subject_issuer_cik": get("issuerCIK", "issuerCik"),
        "subject_issuer_name": get("issuerName"),
        "subject_issuer_cusips": cusips,
        "event_date": get("dateOfEvent", "eventDateRequiresFilingThisStatement"),
        "filing_person_name": get("filingPersonName"),
        "reporting_persons": people,
        "purpose_text": "\n".join(dict.fromkeys(purposes)) or None,
        "transaction_text": "\n".join(dict.fromkeys(transactions)) or None,
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
                if nxt and not re.fullmatch(r"[\d|()\- ]+", nxt):
                    people.append(nxt.strip()); break
    m = re.search(r"(?i)CUSIP(?:\s*(?:No\.?|Number|#))?\s*[:#]?\s*([A-Z0-9]{8,9})", text)
    cusip = m.group(1) if m else None
    m = re.search(r"(?is)Item\s*4\.?\s*(?:Purpose of Transaction)?\s*:?\s*(.{20,8000}?)(?=\n\s*Item\s*5\b)", text)
    purpose = re.sub(r"\s+", " ", m.group(1)).strip() if m else None
    m = re.search(r"(?is)(?:accession\s+(?:number|no\.?)|accession\s*#)\s*[:#]?\s*(\d{10}-\d{2}-\d{6})", text)
    predecessor = m.group(1) if m else None
    return {
        "reporting_person_names": list(dict.fromkeys(people)), "cusip": cusip,
        "purpose_text": purpose, "explicit_predecessor": predecessor,
        "joint_filing_agreement": bool(re.search(r"(?i)JOINT FILING AGREEMENT|RULE 13d-1\(k\)\(1\) AGREEMENT", text)),
    }


def parse_index(raw):
    text = legacy_text(raw)
    out = {"filed_by_name": None, "filed_by_cik": None, "subject_name": None, "subject_cik": None, "accepted_at": None}
    for line in text.splitlines():
        for label in ("Filed by", "Subject"):
            m = re.search(rf"(?i)^\s*(.*?)\s*\({label}\)\s*CIK:\s*(\d{{6,10}})", line)
            if m:
                key = "filed_by" if label == "Filed by" else "subject"
                out[key+"_name"] = m.group(1).strip()
                out[key+"_cik"] = m.group(2).zfill(10)
    m = re.search(r"(?i)Accepted\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", text)
    if m: out["accepted_at"] = m.group(1)
    return out


def group_fingerprint(people):
    ids = []
    for p in people:
        cik, name = (p.get("cik") or "").strip(), (p.get("name") or "").strip()
        if cik: ids.append("CIK:"+cik.zfill(10))
        elif name: ids.append("NAME:"+re.sub(r"\s+", " ", name).casefold())
        else: return None
    return hashlib.sha256("|".join(sorted(set(ids))).encode()).hexdigest() if ids else None
