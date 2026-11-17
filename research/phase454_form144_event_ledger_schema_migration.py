#!/usr/bin/env python3
"""Fail-closed, atomic schema migration for the append-only Phase 403 event ledger."""
from __future__ import annotations
import argparse, csv, json, os, tempfile
from pathlib import Path
from research.phase403_sec_form144_first_seen_capture import EVENT_FIELDS

def migrate_event_ledger(path: str | Path) -> dict:
    path=Path(path)
    if not path.exists() or path.stat().st_size==0:
        return {"changed":False,"reason":"missing_or_empty","rows_migrated":0}
    with path.open("r",newline="",encoding="utf-8-sig") as handle:
        reader=csv.DictReader(handle)
        old_fields=reader.fieldnames
        if not old_fields:
            raise ValueError("event ledger has no CSV header")
        if len(old_fields)!=len(set(old_fields)):
            raise ValueError("event ledger contains duplicate header names")
        unknown=sorted(set(old_fields)-set(EVENT_FIELDS))
        if unknown:
            raise ValueError(f"event ledger contains unknown columns: {unknown}")
        rows=[]
        for line_number,row in enumerate(reader,start=2):
            if None in row:
                raise ValueError(f"event ledger row {line_number} has extra columns")
            rows.append(row)
    if old_fields==EVENT_FIELDS:
        return {"changed":False,"reason":"already_current","rows_migrated":len(rows)}
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp_name=tempfile.mkstemp(prefix=path.name+".",suffix=".migrating",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w",newline="",encoding="utf-8") as handle:
            writer=csv.DictWriter(handle,fieldnames=EVENT_FIELDS,extrasaction="raise")
            writer.writeheader()
            for row in rows:
                writer.writerow({field:(row.get(field) if row.get(field) is not None else "") for field in EVENT_FIELDS})
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name,path)
    except Exception:
        try: os.unlink(tmp_name)
        except FileNotFoundError: pass
        raise
    return {
        "changed":True,
        "reason":"header_migrated",
        "rows_migrated":len(rows),
        "old_fields":old_fields,
        "new_fields":EVENT_FIELDS,
        "new_fields_blank_for_historical_rows":[x for x in EVENT_FIELDS if x not in old_fields],
        "atomic_replace":True
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--path",type=Path,default=Path("research/data/sec_form144_first_seen/events.csv"))
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=migrate_event_ledger(args.path)
    rendered=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(rendered,encoding="utf-8")
    print(rendered,end="")

if __name__=="__main__": main()
