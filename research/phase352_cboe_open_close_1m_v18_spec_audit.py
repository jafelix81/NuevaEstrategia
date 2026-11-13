"""Phase 352: audit Cboe Open-Close 1-minute v1.8 specification and PIT semantics."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SPEC_URL = "https://datashop.cboe.com/documents/Open_Close_1m_Spec_v1.8.pdf"
USER_AGENT = "Mozilla/5.0 (compatible; NuevaEstrategiaResearch/1.0)"
REQUIRED_CHECKS = (
    "version_v1_8_20261108",
    "cumulative_day_to_date_snapshots",
    "real_time_publication_cadence",
    "late_trades_can_arrive_in_later_snapshot",
    "subsequent_corrections_are_reflected",
    "later_busted_or_cancelled_trades_are_removed",
    "trading_dt_and_trading_segment_present",
    "c1_has_gth_and_rth",
    "c2_bzx_edgx_are_rth_only",
    "c1_segment_is_product_specific",
    "non_c1_segment_is_null",
    "fields_10_to_17_empty_in_1m",
    "capacity_code_mapping_present",
    "field_87_and_88_are_date_and_segment",
)


def normalize_text(value: str) -> str:
    value = value.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    value = value.replace("\u2019", "'").replace("\u2018", "'").replace("\u00a0", " ")
    return re.sub(r"\s+", " ", value.lower()).strip()


def audit_spec_text(text: str) -> dict:
    normalized = normalize_text(text)
    empty_interval_count = normalized.count("empty, not included in 1-minute intervals")
    checks = {
        "version_v1_8_20261108": "v1.8 20261108" in normalized,
        "cumulative_day_to_date_snapshots": (
            "trade count and volume within buckets are aggregated throughout the day, not just the latest interval"
            in normalized
        ),
        "real_time_publication_cadence": "files are published on a real-time cadence" in normalized,
        "late_trades_can_arrive_in_later_snapshot": (
            "processed slightly late" in normalized and "later 1-minute snapshot" in normalized
        ),
        "subsequent_corrections_are_reflected": "incorporate subsequent trade corrections" in normalized,
        "later_busted_or_cancelled_trades_are_removed": (
            "broken/canceled will be removed in the subsequent 1-minute snapshots" in normalized
        ),
        "trading_dt_and_trading_segment_present": (
            "trading_dt" in normalized and "trading_segment" in normalized
        ),
        "c1_has_gth_and_rth": "c1 (global trading hours and regular trading hours)" in normalized,
        "c2_bzx_edgx_are_rth_only": "c2, bzx, edgx (regular trading hours only)" in normalized,
        "c1_segment_is_product_specific": all(
            token in normalized
            for token in (
                "first trading segment",
                "second segment",
                "normal rth session",
                "normal gth session",
                "extended gth session",
            )
        ),
        "non_c1_segment_is_null": "null for c2, bzx, and edgx" in normalized,
        "fields_10_to_17_empty_in_1m": empty_interval_count >= 8,
        "capacity_code_mapping_present": all(
            token in normalized
            for token in (
                "firm f, l, j",
                "broker-dealer b",
                "market maker m, n",
                "customer c",
                "pro-customer u, w",
            )
        ),
        "field_87_and_88_are_date_and_segment": (
            "87 trading_dt" in normalized and "88 trading_segment" in normalized
        ),
    }
    failures = [name for name in REQUIRED_CHECKS if not checks.get(name, False)]
    return {
        "status": "PASS_SPEC_SEMANTICS" if not failures else "FAIL_SPEC_SEMANTICS",
        "spec_url": SPEC_URL,
        "spec_version": "v1.8",
        "spec_effective_date": "2026-11-08",
        "checks": checks,
        "failed_checks": failures,
        "empty_not_included_phrase_occurrences": empty_interval_count,
        "snapshot_model": "CUMULATIVE_DAY_TO_DATE",
        "correction_model": "LATER_SNAPSHOTS_REFLECT_LATE_TRADES_AND_SUBSEQUENT_BREAKS_OR_BUSTS",
        "intraday_oi_and_eod_price_fields": "FIELDS_10_TO_17_EMPTY_IN_1M_FILES",
        "historical_pit_admitted": False,
        "prospective_pit_admitted": False,
        "alpha_admission": False,
        "return_test_authorized": False,
        "holdout_used": False,
        "f80_frozen": True,
        "decision": "CONDITIONAL_PROSPECTIVE_CANDIDATE_NO_HISTORICAL_PIT_OR_ALPHA",
        "pit_reason": (
            "The specification documents a real-time cadence and cumulative corrected snapshots, "
            "but does not provide immutable first-receipt timestamps or historical snapshot vintages. "
            "Prospective PIT would require append-only capture of each file as first received."
        ),
    }


def download_spec(url: str = SPEC_URL, retries: int = 3) -> tuple[bytes, int, str]:
    last_error = None
    for attempt in range(retries):
        request = Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/pdf,*/*"},
        )
        try:
            with urlopen(request, timeout=60) as response:
                payload = response.read()
                content_type = response.headers.get("Content-Type", "")
                if response.status != 200 or not payload.startswith(b"%PDF"):
                    raise RuntimeError(
                        f"unexpected specification response: status={response.status}, "
                        f"content_type={content_type}, prefix={payload[:12]!r}"
                    )
                return payload, response.status, content_type
        except HTTPError as error:
            last_error = f"HTTP {error.code}"
            if error.code not in (408, 429, 500, 502, 503, 504):
                raise
        except (URLError, TimeoutError, OSError) as error:
            last_error = f"{type(error).__name__}: {error}"
        if attempt + 1 < retries:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"specification download failed after {retries} attempts: {last_error}")


def audit_pdf(payload: bytes, *, retrieved_at_utc: str | None = None) -> dict:
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise RuntimeError("pypdf is required; install the pinned CI dependency") from error

    reader = PdfReader(io.BytesIO(payload), strict=True)
    pages = [page.extract_text() or "" for page in reader.pages]
    extracted_text = "\n".join(pages)
    result = audit_spec_text(extracted_text)
    result.update(
        {
            "retrieved_at_utc": retrieved_at_utc or datetime.now(timezone.utc).isoformat(),
            "http_status": 200,
            "content_type": "application/pdf",
            "pdf_bytes": len(payload),
            "pdf_sha256": hashlib.sha256(payload).hexdigest(),
            "page_count": len(reader.pages),
            "extracted_characters": len(extracted_text),
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("phase352_output/spec_audit.json"))
    parser.add_argument("--spec-url", default=SPEC_URL)
    args = parser.parse_args()

    payload, status, content_type = download_spec(args.spec_url)
    result = audit_pdf(payload)
    result["http_status"] = status
    result["content_type"] = content_type
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0 if result["status"] == "PASS_SPEC_SEMANTICS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
