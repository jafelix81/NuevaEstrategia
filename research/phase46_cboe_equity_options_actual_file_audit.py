#!/usr/bin/env python3
"""Phase 46 — Cboe equity-option volume actual-file audit.

Data-feasibility only. No alpha test and no baseline change.
Audits representative public Cboe monthly equity-option volume files against
F80's frozen 335-symbol universe. Because historical release timestamps are not
published with the archive, the audit treats PIT availability as unresolved and
requires a conservative lag for any future research use.
"""
from __future__ import annotations

import io
import json
import re
import urllib.request
from pathlib import Path

import pandas as pd

HEADERS = {"User-Agent": "NuevaEstrategia research audit contact research@example.com"}
FILES = {
    "2018-01": "https://cdn.cboe.com/resources/options/volume_archive/2018/2018_01_rank_wosym.xlsx",
    "2018-12": "https://cdn.cboe.com/resources/options/volume_archive/2018/2018_12_rank_wosym.xlsx",
    "2019-01": "https://cdn.cboe.com/resources/options/volume_archive/2019/2019_01_rank_wosym.xlsx",
    "2019-08": "https://cdn.cboe.com/resources/options/volume_archive/2019/2019_08_rank_wosym.xlsx",
}


def norm_ticker(x: object) -> str:
    s = str(x).strip().upper()
    return re.sub(r"[^A-Z0-9.\-]", "", s)


def load_frozen() -> set[str]:
    src = Path("Nueva_Estrategia_Fase0_Descubrimiento.py").read_text(encoding="utf-8")
    block = src.split("DEFAULT_UNIVERSE = [", 1)[1].split("]\n", 1)[0]
    return set(re.findall(r"'([A-Z0-9.\-]+)'", block))


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def parse_xlsx(payload: bytes) -> dict:
    xls = pd.ExcelFile(io.BytesIO(payload), engine="openpyxl")
    sheets = xls.sheet_names
    frames = []
    for sheet in sheets:
        df = pd.read_excel(xls, sheet_name=sheet, header=None)
        if df.empty:
            continue
        # Find the first row containing a likely symbol header.
        header_row = None
        for i in range(min(15, len(df))):
            vals = [norm_ticker(v) for v in df.iloc[i].tolist()]
            if any(v in {"SYMBOL", "SYM", "ROOT"} for v in vals):
                header_row = i
                break
        if header_row is None:
            continue
        h = [str(v).strip() if pd.notna(v) else "" for v in df.iloc[header_row].tolist()]
        body = df.iloc[header_row + 1 :].copy()
        body.columns = h
        symbol_col = next((c for c in body.columns if norm_ticker(c) in {"SYMBOL", "SYM", "ROOT"}), None)
        if symbol_col is None:
            continue
        symbols = [norm_ticker(x) for x in body[symbol_col].dropna().tolist()]
        symbols = sorted({x for x in symbols if x})
        frames.append({"sheet": sheet, "rows": len(body), "symbols": symbols})
    all_symbols = sorted({s for f in frames for s in f["symbols"]})
    return {"sheets": sheets, "parsed_sheets": frames, "unique_symbols": all_symbols}


def main() -> None:
    frozen = load_frozen()
    if len(frozen) != 335:
        raise RuntimeError(f"Frozen universe expected 335, found {len(frozen)}")

    report = {
        "phase": "46_CBOE_EQUITY_OPTIONS_ACTUAL_FILE_AUDIT",
        "frozen_universe": len(frozen),
        "status": "UNKNOWN",
        "pit": {
            "historical_release_timestamp_documented": False,
            "interpretation": "The archive provides month-labelled files but does not expose a historical release/acceptance timestamp. Any later alpha test must therefore impose a conservative ex-ante lag and never treat month-end as the knowledge date."
        },
        "datasets": {},
    }

    for label, url in FILES.items():
        payload = download(url)
        parsed = parse_xlsx(payload)
        symbols = set(parsed["unique_symbols"])
        matched = sorted(symbols & frozen)
        report["datasets"][label] = {
            "url": url,
            "download_bytes": len(payload),
            "sheets": parsed["sheets"],
            "parsed_sheets": [{"sheet": x["sheet"], "rows": x["rows"]} for x in parsed["parsed_sheets"]],
            "unique_symbols": len(symbols),
            "frozen_matches": len(matched),
            "coverage_rate": len(matched) / len(frozen),
            "matched_examples": matched[:30],
        }

    min_cov = min(x["coverage_rate"] for x in report["datasets"].values())
    report["minimum_coverage"] = min_cov
    report["status"] = "PASS_FILE_SCHEMA_COVERAGE_PENDING_PIT" if min_cov >= 0.70 else "FAIL_FILE_SCHEMA_COVERAGE"
    report["next_gate"] = "If coverage is adequate, define and freeze a conservative publication-lag rule, then test incremental option-volume information versus F80/LTM. Do not infer informed trading from volume alone."

    Path("cboe_equity_options_actual_file_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
