#!/usr/bin/env python3
"""Fail-closed, dimension-preserving SEC Item 408 Inline XBRL extractor.

This module extracts filing-level ECD Item 408 facts. It deliberately does not
infer executions, active-plan status, discretionary intent, or aggregate shares
across contexts. Public availability must be supplied from the EDGAR SGML header
and separately mapped to a conservative trading session.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")

ITEM408_CONCEPTS = {
    "MtrlTermsOfTrdArrTextBlock",
    "TrdArrIndName",
    "TrdArrIndTitle",
    "Rule10b51ArrAdoptedFlag",
    "NonRule10b51ArrAdoptedFlag",
    "TrdArrAdoptionDate",
    "Rule10b51ArrTrmntdFlag",
    "NonRule10b51ArrTrmntdFlag",
    "TrdArrTerminationDate",
    "TrdArrExpirationDate",
    "TrdArrDuration",
    "TrdArrSecuritiesAggAvailAmt",
    "Rule10b51ArrModifiedFlag",
    "NonRule10b51ArrModifiedFlag",
}
IX_FACT_TAGS = {"ix:nonnumeric", "ix:nonfraction", "ix:fraction"}
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


class Node:
    __slots__ = ("tag", "attrs", "children", "content", "parent")

    def __init__(self, tag: str, attrs: dict[str, str], parent: "Node | None"):
        self.tag = tag.lower()
        self.attrs = attrs
        self.children: list[Node] = []
        self.content: list[Node | str] = []
        self.parent = parent


class _TreeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", {}, None)
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        parent = self.stack[-1]
        node = Node(tag, {k.lower(): (v or "") for k, v in attrs}, parent)
        parent.children.append(node)
        parent.content.append(node)
        if tag.lower() not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        parent = self.stack[-1]
        node = Node(tag, {k.lower(): (v or "") for k, v in attrs}, parent)
        parent.children.append(node)
        parent.content.append(node)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        # HTML/XHTML can contain omitted or mismatched optional end tags. Pop
        # only through the nearest matching open element; never pop document.
        for idx in range(len(self.stack) - 1, 0, -1):
            if self.stack[idx].tag == tag:
                del self.stack[idx:]
                break

    def handle_data(self, data: str) -> None:
        self.stack[-1].content.append(data)


def _walk(node: Node):
    yield node
    for child in node.children:
        yield from _walk(child)


def _text(node: Node, *, skip_exclude: bool = True) -> str:
    out: list[str] = []
    for item in node.content:
        if isinstance(item, str):
            out.append(item)
        else:
            if skip_exclude and item.tag == "ix:exclude":
                continue
            out.append(_text(item, skip_exclude=skip_exclude))
    return re.sub(r"\s+", " ", "".join(out)).strip()


def _descendants(node: Node, tag: str):
    target = tag.lower()
    for child in _walk(node):
        if child is not node and child.tag == target:
            yield child


def _is_under_hidden(node: Node) -> bool:
    parent = node.parent
    while parent is not None:
        if parent.tag == "ix:hidden":
            return True
        parent = parent.parent
    return False


def _qname_parts(qname: str) -> tuple[str | None, str]:
    if ":" in qname:
        prefix, local = qname.split(":", 1)
        return prefix, local
    return None, qname


def parse_acceptance_datetime(header_text: str) -> dict[str, str]:
    """Parse SEC <ACCEPTANCE-DATETIME> as Eastern wall time, not as UTC.

    SEC's PDS specification labels the header clock EST; the governing filing
    rules refer to EST or EDT, whichever is in effect. Preserve the raw digits
    and use America/New_York for a timezone-aware instant. Never parse the
    submissions-API acceptanceDateTime suffix as authoritative when the
    SGML header is available.
    """
    values = re.findall(
        r"(?im)^\s*<ACCEPTANCE-DATETIME>\s*(\d{14})\s*$",
        header_text,
    )
    if not values:
        # Some copied headers place the value on a line with adjacent tags.
        values = re.findall(r"<ACCEPTANCE-DATETIME>\s*(\d{14})", header_text, re.I)
    unique = sorted(set(values))
    if len(unique) != 1:
        raise ValueError(f"expected one unique ACCEPTANCE-DATETIME; found {unique!r}")
    raw = unique[0]
    try:
        local_naive = datetime.strptime(raw, "%Y%m%d%H%M%S")
    except ValueError as exc:
        raise ValueError(f"invalid ACCEPTANCE-DATETIME: {raw}") from exc
    local = local_naive.replace(tzinfo=EASTERN)
    return {
        "acceptance_raw": raw,
        "acceptance_eastern": local.isoformat(),
        "acceptance_utc": local.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "acceptance_timezone": "America/New_York",
        "acceptance_precision": "second",
    }


def _context_map(root: Node) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for context in _descendants(root, "xbrli:context"):
        context_id = context.attrs.get("id")
        if not context_id:
            continue
        entity = next(_descendants(context, "xbrli:entity"), None)
        identifier = next(_descendants(entity, "xbrli:identifier"), None) if entity else None
        period = next(_descendants(context, "xbrli:period"), None)
        period_values: dict[str, str] = {}
        if period:
            for child in period.children:
                if child.tag in {"xbrli:startdate", "xbrli:enddate", "xbrli:instant"}:
                    period_values[child.tag.split(":", 1)[1]] = _text(child)
        dimensions: dict[str, list[dict[str, str]]] = {}
        for member_tag in ("xbrldi:explicitmember", "xbrldi:typedmember"):
            for member in _descendants(context, member_tag):
                dimension = member.attrs.get("dimension", "")
                if not dimension:
                    continue
                dimensions.setdefault(dimension, []).append({
                    "kind": "explicit" if member_tag.endswith("explicitmember") else "typed",
                    "member": _text(member),
                })
        result[context_id] = {
            "context_id": context_id,
            "entity_identifier": _text(identifier) if identifier else None,
            "period": period_values,
            "dimensions": dimensions,
        }
    return result


def _continuation_text(node: Node, continuations: dict[str, Node]) -> str:
    chunks = [_text(node)]
    next_id = node.attrs.get("continuedat")
    seen: set[str] = set()
    while next_id:
        if next_id in seen:
            raise ValueError(f"cyclic ix:continuation chain at {next_id}")
        seen.add(next_id)
        continuation = continuations.get(next_id)
        if continuation is None:
            raise ValueError(f"missing ix:continuation id {next_id}")
        chunks.append(_text(continuation))
        next_id = continuation.attrs.get("continuedat")
    return re.sub(r"\s+", " ", " ".join(part for part in chunks if part)).strip()


def _numeric_value(tag: str, raw: str, attrs: dict[str, str]) -> str | None:
    if tag != "ix:nonfraction" or not raw:
        return None
    lexical = raw.replace(",", "").replace("$", "").strip()
    try:
        value = Decimal(lexical)
        scale = int(attrs.get("scale", "0") or "0")
        value *= Decimal(10) ** scale
        if attrs.get("sign") == "-":
            value = -abs(value)
        return str(value)
    except (InvalidOperation, ValueError):
        return None


def extract_item408_facts(
    inline_xbrl: str | bytes,
    *,
    accession: str,
    issuer_cik: str,
) -> dict[str, Any]:
    """Extract Item 408 ECD facts, preserving every context and dimension.

    This is a fact extractor, not a plan-state engine. It does not sum share
    amounts, collapse duplicate facts, or infer missing/false/active states.
    """
    source = inline_xbrl.decode("utf-8", "replace") if isinstance(inline_xbrl, bytes) else inline_xbrl
    parser = _TreeParser()
    parser.feed(source)
    parser.close()
    root = parser.root
    contexts = _context_map(root)
    continuations = {
        node.attrs["id"]: node
        for node in _walk(root)
        if node.tag == "ix:continuation" and node.attrs.get("id")
    }
    namespace_map: dict[str, str] = {}
    for candidate in _walk(root):
        for attr_name, namespace_uri in candidate.attrs.items():
            if attr_name.startswith("xmlns:"):
                namespace_map[attr_name.split(":", 1)[1]] = namespace_uri
    ecd_prefixes = {
        prefix for prefix, namespace_uri in namespace_map.items()
        if "/ecd/" in namespace_uri.lower()
    }
    if not ecd_prefixes:
        ecd_prefixes = {"ecd"}

    facts: list[dict[str, Any]] = []
    issuer_extension_facts: list[dict[str, Any]] = []
    extension_pattern = re.compile(
        r"(?:rule|nonrule)10b5?1|trdarr|tradingarr", re.IGNORECASE
    )

    def make_fact_record(node: Node, prefix: str, concept: str) -> dict[str, Any]:
        context_ref = node.attrs.get("contextref")
        context = contexts.get(context_ref or "")
        raw_value = _continuation_text(node, continuations)
        nil = node.attrs.get("xsi:nil", "").lower() in {"true", "1"}
        if nil:
            raw_value = ""
        return {
            "accession": accession,
            "issuer_cik": str(issuer_cik).zfill(10),
            "taxonomy_prefix": prefix,
            "taxonomy_namespace": namespace_map.get(prefix),
            "concept": concept,
            "fact_tag": node.tag,
            "context_ref": context_ref,
            "context_found": context is not None,
            "period": context["period"] if context else None,
            "dimensions": context["dimensions"] if context else None,
            "entity_identifier": context["entity_identifier"] if context else None,
            "unit_ref": node.attrs.get("unitref"),
            "decimals": node.attrs.get("decimals"),
            "scale": node.attrs.get("scale"),
            "format": node.attrs.get("format"),
            "nil": nil,
            "value": None if nil else raw_value,
            "numeric_value": None if nil else _numeric_value(node.tag, raw_value, node.attrs),
            "is_hidden": _is_under_hidden(node),
        }

    for node in _walk(root):
        if node.tag not in IX_FACT_TAGS:
            continue
        qname = node.attrs.get("name", "")
        prefix, concept = _qname_parts(qname)
        if prefix is None or prefix not in namespace_map:
            continue
        if prefix in ecd_prefixes and concept in ITEM408_CONCEPTS:
            facts.append(make_fact_record(node, prefix, concept))
        elif prefix not in ecd_prefixes and extension_pattern.search(concept):
            # Preserve issuer taxonomy facts related to Item 408 lifecycle or
            # arrangement fields. Their semantics remain issuer-specific.
            issuer_extension_facts.append(make_fact_record(node, prefix, concept))

    return {
        "accession": accession,
        "issuer_cik": str(issuer_cik).zfill(10),
        "context_count": len(contexts),
        "standard_fact_count": len(facts),
        "issuer_extension_fact_count": len(issuer_extension_facts),
        "item408_fact_count": len(facts) + len(issuer_extension_facts),
        "extraction_status": "facts_found" if facts or issuer_extension_facts else "no_tagged_item408_facts_unknown",
        "facts": facts,
        "issuer_extension_facts": issuer_extension_facts,
        "limitations": [
            "facts remain at their original context/dimension grain",
            "no aggregation across TradingArrAxis or IndividualAxis",
            "no execution, discretionary-intent, active-plan, or natural-expiry inference",
            "missing facts remain unknown, not false",
            "issuer extension facts are preserved separately and require issuer-specific semantic review",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inline-xbrl", required=True)
    parser.add_argument("--header", required=True)
    parser.add_argument("--accession", required=True)
    parser.add_argument("--issuer-cik", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    header = Path(args.header).read_text(encoding="utf-8", errors="replace")
    source = Path(args.inline_xbrl).read_bytes()
    result = extract_item408_facts(source, accession=args.accession, issuer_cik=args.issuer_cik)
    result["acceptance"] = parse_acceptance_datetime(header)
    result["inline_xbrl_sha256"] = __import__("hashlib").sha256(source).hexdigest()
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "accession": args.accession,
        "acceptance": result["acceptance"],
        "context_count": result["context_count"],
        "item408_fact_count": result["item408_fact_count"],
        "output": args.output,
    }, indent=2))


if __name__ == "__main__":
    main()
