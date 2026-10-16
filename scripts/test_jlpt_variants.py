#!/usr/bin/env python3
"""Regression checks for explicit orthography aliases in the vocabulary export."""
import json
import sqlite3
import tempfile
from pathlib import Path
from build_jlpt_db import ROOT, build
from build_jlpt_content import apply_chinese_entries, publish

drafts=json.loads((ROOT/"database/content/vocabulary-zh-reviewed.json").read_text(encoding="utf-8"))["entries"]
variant=next(x for x in drafts if x["expression"]=="鞄" and x["reading"]=="かばん")

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
    data=json.loads((root/"export"/"n5.json").read_text(encoding="utf-8"))
    entries=[w for w in data["words"] if w["expression"]=="かばん" and w["reading"]=="かばん"]
    assert len(entries)==1,entries
    assert entries[0]["meaning_zh"]==variant["meaning_zh"],entries
    assert entries[0]["example_ja"]==variant["example_ja"],entries
    assert entries[0]["example_zh"]==variant["example_zh"],entries
    assert data["official_exam_appearances_available"] is False
    print("PASS: orthography alias merges into N5 reference word and examples")
