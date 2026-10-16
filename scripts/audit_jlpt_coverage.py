#!/usr/bin/env python3
"""Report coverage and editorial issues without treating drafts as approved."""
import argparse
import csv
import json
from pathlib import Path
from build_jlpt_db import ROOT, LEVELS

def inspect(root=ROOT):
    data=json.loads((root/"database/content/vocabulary-zh-reviewed.json").read_text(encoding="utf-8"))
    entries=data["entries"]
    by_key={}
    problems=[]
    for i,item in enumerate(entries,1):
        key=(item.get("expression","").strip(),item.get("reading","").strip())
        if not key[0]: problems.append(f"entry {i}: missing expression")
        if key in by_key: problems.append(f"entry {i}: duplicate {key}")
        by_key[key]=item
        if item.get("variant_of") and item["variant_of"]==key[0]: problems.append(f"entry {i}: variant_of points to itself")
        for field in ("meaning_zh","example_ja","example_zh"):
            if not item.get(field,"").strip(): problems.append(f"entry {i}: missing {field}")
    stats={}
    known=set()
    for level in LEVELS:
        path=root/"data-src"/(level.lower()+".csv")
        with path.open(encoding="utf-8-sig",newline="") as fh:
            rows=list(csv.DictReader(fh))
        keys={(r["expression"].strip(),(r.get("reading") or "").strip()) for r in rows if r.get("expression","").strip()}
        known.update(keys)
        present=keys & set(by_key)
        alias_hits={ (item["variant_of"],item["reading"]) for item in entries if item.get("variant_of") and (item["variant_of"],item["reading"]) in keys }
        present |= alias_hits
        stats[level]={"reference_words":len(keys),"chinese_drafts":len(present),
                      "coverage_percent":round(100*len(present)/len(keys),2) if keys else 0,
                      "missing":len(keys-present)}
    orphan=set(by_key)-known
    aliases={(item["variant_of"],item["reading"]) for item in entries if item.get("variant_of")}
    targets={}
    for i,item in enumerate(entries,1):
        target=(item.get("variant_of") or item.get("expression"),item.get("reading"))
        if target in known:
            previous=targets.get(target)
            if previous is not None:
                problems.append(f"entry {i}: duplicate reference target {target} (also entry {previous})")
            else:
                targets[target]=i
    unmatched=[repr(key) for key in sorted(orphan) if not by_key[key].get("variant_of")]
    invalid_aliases=[repr(key) for key in sorted(aliases-known)]
    problems.extend("variant target missing from reference: "+key for key in invalid_aliases)
    return {"review_status":data.get("review_status","unknown"),
            "unique_reference_words":len(known),"draft_entries":len(by_key),
            "drafts_matching_reference":len(targets),
            "levels":stats,"issues":problems,"unmatched_reference_entries":unmatched,"unmatched_draft_count":len(unmatched),"invalid_aliases":invalid_aliases,
            "note":"Draft coverage is not reviewed/approved Chinese translation coverage."}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    parser.add_argument("--strict",action="store_true")
    args=parser.parse_args()
    result=inspect()
    payload=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    print(payload)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(payload,encoding="utf-8")
    if args.strict and result["issues"]:
        raise SystemExit(1)
