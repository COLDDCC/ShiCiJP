#!/usr/bin/env python3
"""Regression checks for explicit orthography aliases in the vocabulary export."""
import json
import sqlite3
import tempfile
from pathlib import Path
from build_jlpt_db import build
from build_jlpt_content import apply_chinese_entries, publish

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    db=root/"test.sqlite"
    build(db)
    with sqlite3.connect(db) as con:
        con.execute("PRAGMA foreign_keys=ON")
        apply_chinese_entries(con)
        row=con.execute("SELECT meaning_zh FROM vocabulary WHERE expression=? AND reading=?",
                        ("かばん","かばん")).fetchone()
        assert row and row[0]=="包；书包",row
        orphan=con.execute("SELECT COUNT(*) FROM vocabulary v LEFT JOIN vocabulary_levels l ON l.vocabulary_id=v.id WHERE v.expression=? AND v.reading=? AND l.vocabulary_id IS NULL",("りんご","りんご")).fetchone()[0]
        assert orphan==0,"Unmatched draft must not create orphan vocabulary"
    publish(db,root/"export")
    data=json.loads((root/"export"/"n5.json").read_text(encoding="utf-8"))
    entries=[w for w in data["words"] if w["expression"]=="かばん" and w["reading"]=="かばん"]
    assert len(entries)==1,entries
    assert entries[0]["meaning_zh"]=="包；书包",entries
    assert entries[0]["example_ja"]=="鞄を買いました。",entries
    assert entries[0]["example_zh"]=="买了一个包。",entries
    assert data["official_exam_appearances_available"] is False
    print("PASS: orthography alias merges into N5 reference word and examples")
