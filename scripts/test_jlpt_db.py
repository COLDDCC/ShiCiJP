#!/usr/bin/env python3
"""Smoke tests for the JLPT relational schema and frequency isolation."""
import sqlite3
import tempfile
from pathlib import Path
from build_jlpt_db import build

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "test.sqlite"
    build(path)
    db = sqlite3.connect(str(path))
    db.execute("PRAGMA foreign_keys=ON")
    assert db.execute("SELECT COUNT(*) FROM vocabulary").fetchone()[0] > 0
    assert db.execute("SELECT COUNT(*) FROM vocabulary_levels").fetchone()[0] > 0
    assert db.execute("SELECT COUNT(*) FROM official_vocabulary_frequency").fetchone()[0] == 0
    v = db.execute("SELECT id FROM vocabulary LIMIT 1").fetchone()[0]
    db.execute("INSERT INTO sources(id,title,source_type) VALUES('test','Original practice','original')")
    db.execute("""INSERT INTO exams(id,level,title,source_id) VALUES('practice-1','N5','Test paper','test')""")
    db.execute("""INSERT INTO questions(id,exam_id,section,question_number,explanation_zh)
                  VALUES('q1','practice-1','vocabulary',1,'示例解析')""")
    db.execute("""INSERT INTO question_vocabulary(question_id,vocabulary_id,evidence)
                  VALUES('q1',?,'original_practice')""", (v,))
    assert db.execute("SELECT COUNT(*) FROM practice_vocabulary_frequency").fetchone()[0] == 1
    assert db.execute("SELECT COUNT(*) FROM official_vocabulary_frequency").fetchone()[0] == 0
    try:
        db.execute("""INSERT INTO question_vocabulary(question_id,vocabulary_id,evidence)
                      VALUES('missing',?,'verified_original')""", (v,))
        raise AssertionError("Foreign key check did not reject missing question")
    except sqlite3.IntegrityError:
        pass
    db.close()
print("JLPT database tests passed")
