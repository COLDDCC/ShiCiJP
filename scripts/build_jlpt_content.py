#!/usr/bin/env python3
"""Build the full JLPT reference database and publish evidence-labelled JSON."""
import argparse
import json
import sqlite3
from pathlib import Path

from build_jlpt_db import ROOT, LEVELS, build
from import_jlpt_questions import import_questions


def publish(db_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(db_path)) as con:
        con.execute("PRAGMA foreign_keys=ON")
        for level in LEVELS:
            rows = con.execute("""
                SELECT v.id,v.expression,v.reading,v.meaning_en,v.meaning_zh,
                       COALESCE(p.question_count,0)
                FROM vocabulary v
                JOIN vocabulary_levels vl ON vl.vocabulary_id=v.id
                LEFT JOIN practice_vocabulary_frequency p
                  ON p.vocabulary_id=v.id AND p.level=?
                WHERE vl.level=?
                GROUP BY v.id
                ORDER BY v.expression,v.reading
            """, (level,level)).fetchall()
            words = [{"id":r[0],"expression":r[1],"reading":r[2],
                      "meaning_en":r[3],"meaning_zh":r[4],
                      "original_practice_question_count":r[5]} for r in rows]
            payload = {"level":level,"source":"jamsinclair/open-anki-jlpt-decks",
                       "level_classification":"community_reference_not_official",
                       "official_exam_appearances_available":False,
                       "words":words}
            (destination/(level.lower()+".json")).write_text(
                json.dumps(payload,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
            print(level, len(words), "reference words")
        official = con.execute("SELECT COUNT(*) FROM official_vocabulary_frequency").fetchone()[0]
        assert official == 0, "Unexpected official occurrence data; review source provenance"
        print("Verified official frequency entries:",official)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--db",type=Path,default=ROOT/"database"/"jlpt.sqlite")
    parser.add_argument("--output",type=Path,default=ROOT/"public"/"jlpt"/"vocabulary"/"data")
    args=parser.parse_args()
    build(args.db)
    with sqlite3.connect(str(args.db)) as con:
        con.execute("PRAGMA foreign_keys=ON")
        import_questions(con)
        errors=con.execute("PRAGMA foreign_key_check").fetchall()
        if errors: raise RuntimeError("Foreign key errors: "+repr(errors[:5]))
        print("Original practice questions:",con.execute("SELECT COUNT(*) FROM questions").fetchone()[0])
    publish(args.db,args.output)


if __name__=="__main__":
    main()
