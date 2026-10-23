#!/usr/bin/env python3
"""Regression checks for explicit orthography aliases in the vocabulary export."""
import json
import sqlite3
import tempfile
from pathlib import Path
from build_jlpt_db import ROOT, build
from build_jlpt_content import apply_chinese_entries, publish
from audit_jlpt_coverage import inspect

drafts=json.loads((ROOT/"database/content/vocabulary-zh-reviewed.json").read_text(encoding="utf-8"))["entries"]
variant=next(x for x in drafts if x["expression"]=="鞄" and x["reading"]=="かばん")
coverage=inspect()
assert not coverage["issues"],coverage["issues"]
assert coverage["draft_entries"]==len(drafts)
assert coverage["drafts_matching_reference"]+coverage["unmatched_draft_count"]==len(drafts)
assert coverage["unmatched_draft_count"]==len(coverage["unmatched_reference_entries"])
assert coverage["unmatched_draft_count"]==len(coverage["unmatched_draft_details"])
assert all(item["reason"]=="not_in_reference" for item in coverage["unmatched_draft_details"])
assert coverage["levels"]["N5"]["missing"]==0, "N5 draft coverage has regressed"
assert coverage["levels"]["N5"]["chinese_drafts"]==coverage["levels"]["N5"]["reference_words"], "N5 drafts must cover every reference word"
assert coverage["review_status"]=="draft_editorial_review", "Drafts must not be represented as approved translations"

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    db=root/"test.sqlite"
    build(db)
    with sqlite3.connect(db) as con:
        con.execute("PRAGMA foreign_keys=ON")
        before=con.execute("SELECT COUNT(*) FROM vocabulary").fetchone()[0]
        apply_chinese_entries(con)
        after=con.execute("SELECT COUNT(*) FROM vocabulary").fetchone()[0]
        assert before==after,"Editorial drafts must not create vocabulary rows"
        row=con.execute("SELECT meaning_zh FROM vocabulary WHERE expression=? AND reading=?",
                        ("かばん","かばん")).fetchone()
        assert row and row[0]==variant["meaning_zh"],row
        orphans=con.execute("SELECT COUNT(*) FROM vocabulary v LEFT JOIN vocabulary_levels l ON l.vocabulary_id=v.id WHERE l.vocabulary_id IS NULL").fetchone()[0]
        assert orphans==0,"Editorial import must not create orphan vocabulary"
        for item in drafts:
            target=(item.get("variant_of") or item["expression"],item["reading"])
            record=con.execute("SELECT meaning_zh FROM vocabulary WHERE expression=? AND reading=?",target).fetchone()
            if record:
                assert record[0]==item["meaning_zh"],("Missing translated meaning",target)
    publish(db,root/"export")
    exported={level:json.loads((root/"export"/(level+".json")).read_text(encoding="utf-8")) for level in ("n1","n2","n3","n4","n5")}
    data=exported["n5"]
    assert len(data["words"])==coverage["levels"]["N5"]["reference_words"], "N5 export size differs from reference coverage"
    assert all(isinstance(w[field],str) and w[field].strip()
               for w in data["words"] for field in ("meaning_zh","example_ja","example_zh")), "N5 export contains incomplete Chinese drafts"
    entries=[w for w in data["words"] if w["expression"]=="かばん" and w["reading"]=="かばん"]
    assert len(entries)==1,entries
    assert entries[0]["meaning_zh"]==variant["meaning_zh"],entries
    assert entries[0]["example_ja"]==variant["example_ja"],entries
    assert entries[0]["example_zh"]==variant["example_zh"],entries
    assert data["official_exam_appearances_available"] is False
    for level,payload in exported.items():
        assert payload["review_status"]=="draft_editorial_review",level
        assert payload["level"]==level.upper(),level
        assert payload["official_exam_appearances_available"] is False,level
        assert payload["level_classification"]=="community_reference_not_official",level
        published={(w["expression"],w["reading"]):w for w in payload["words"]}
        assert len(published)==len(payload["words"]),("Duplicate exported words",level)
        for item in drafts:
            target=(item.get("variant_of") or item["expression"],item["reading"])
            if target in published:
                word=published[target]
                assert word["meaning_zh"]==item["meaning_zh"],(level,target)
                assert word["example_ja"]==item["example_ja"],(level,target)
                assert word["example_zh"]==item["example_zh"],(level,target)
    print("PASS: all N1–N5 exports preserve editorial translations, examples and source labels")
