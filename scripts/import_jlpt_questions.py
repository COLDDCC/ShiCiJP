#!/usr/bin/env python3
"""Import vetted, version-controlled original questions into SQLite."""
import json
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTENT=ROOT/"database"/"content"/"original-practice.json"

def import_questions(db: sqlite3.Connection, content_path: Path=CONTENT):
    payload=json.loads(content_path.read_text(encoding="utf-8"))
    src=payload["source"]
    assert src["source_type"]=="original", "Only owned original practice is supported by this importer"
    db.execute("""INSERT INTO sources(id,title,source_type,url,license,permission_status)
      VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING""",
      (src["id"],src["title"],src["source_type"],src.get("url"),src.get("license"),src.get("permission_status","owned")))
    for exam in payload["exams"]:
        db.execute("""INSERT INTO exams(id,level,title,source_id,is_official,publication_status)
          VALUES(?,?,?,?,0,'original_public') ON CONFLICT(id) DO NOTHING""",
          (exam["id"],exam["level"],exam["title"],src["id"]))
        for q in exam["questions"]:
            opts=q["options"]
            if len(opts)!=4 or not 1<=q["correct_option"]<=4:
                raise ValueError("Each question needs four options and a correct option 1-4")
            if not q.get("explanation_zh") or any(not o.get("explanation_zh") for o in opts):
                raise ValueError("All answer options and questions require explanations")
            db.execute("""INSERT INTO questions(id,exam_id,section,question_number,stem,correct_option,explanation_zh,content_rights)
              VALUES(?,?,?,?,?,?,?,'owned_original') ON CONFLICT(id) DO NOTHING""",
              (q["id"],exam["id"],exam["section"],q["number"],q["stem"],q["correct_option"],q["explanation_zh"]))
            for i,opt in enumerate(opts,1):
                db.execute("""INSERT INTO options(question_id,option_number,text,explanation_zh)
                  VALUES(?,?,?,?) ON CONFLICT(question_id,option_number) DO NOTHING""",
                  (q["id"],i,opt["text"],opt["explanation_zh"]))
            for word in q.get("vocabulary",[]):
                record=db.execute("SELECT id FROM vocabulary WHERE expression=? AND reading=?",
                                  (word["expression"],word.get("reading",""))).fetchone()
                if not record:
                    db.execute("INSERT INTO vocabulary(expression,reading) VALUES(?,?)",
                               (word["expression"],word.get("reading","")))
                    vid=db.execute("SELECT last_insert_rowid()").fetchone()[0]
                else:
                    vid=record[0]
                db.execute("""INSERT INTO question_vocabulary(question_id,vocabulary_id,occurrence_count,evidence)
                  VALUES(?,?,?,'original_practice') ON CONFLICT(question_id,vocabulary_id) DO NOTHING""",
                  (q["id"],vid,word.get("occurrence_count",1)))
            for name in q.get("grammar",[]):
                gid=exam["level"]+":"+name
                db.execute("INSERT INTO grammar(id,expression,level) VALUES(?,?,?) ON CONFLICT(id) DO NOTHING",
                           (gid,name,exam["level"]))
                db.execute("INSERT INTO question_grammar(question_id,grammar_id) VALUES(?,?) ON CONFLICT DO NOTHING",
                           (q["id"],gid))
    db.commit()

if __name__=="__main__":
    from build_jlpt_db import build
    path=ROOT/"database"/"jlpt.sqlite"
    build(path)
    with sqlite3.connect(str(path)) as db:
        db.execute("PRAGMA foreign_keys=ON")
        import_questions(db)
        print("Original questions:",db.execute("SELECT COUNT(*) FROM questions").fetchone()[0])
