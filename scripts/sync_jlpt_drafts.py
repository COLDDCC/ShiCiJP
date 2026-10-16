#!/usr/bin/env python3
"""Validate or refresh the static Chinese vocabulary overlay from its single source."""
import argparse
import json
from pathlib import Path
from build_jlpt_db import ROOT

SOURCE = ROOT / "database/content/vocabulary-zh-reviewed.json"
TARGET = ROOT / "public/jlpt/vocabulary/data/zh-drafts.json"

def render():
    source=json.loads(SOURCE.read_text(encoding="utf-8"))
    fields=("expression","reading","meaning_zh","example_ja","example_zh","variant_of")
    entries=[{k:item[k] for k in fields if k in item} for item in source["entries"]]
    return json.dumps({"status":source["review_status"],"entries":entries},
                      ensure_ascii=False,separators=(",",":"))+"\n"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--check",action="store_true")
    args=p.parse_args()
    expected=render()
    if args.check:
        if not TARGET.exists() or json.loads(TARGET.read_text(encoding="utf-8"))!=json.loads(expected):
            raise SystemExit("Stale zh-drafts.json: run python3 scripts/sync_jlpt_drafts.py")
        print("PASS: static Chinese draft overlay matches editorial source")
    else:
        TARGET.parent.mkdir(parents=True,exist_ok=True)
        TARGET.write_text(expected,encoding="utf-8")
        print("Updated:",TARGET)

if __name__=="__main__":
    main()
