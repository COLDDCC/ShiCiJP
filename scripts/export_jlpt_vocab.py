#!/usr/bin/env python3
"""Export read-only vocabulary JSON for the static JLPT site."""
import json
import sqlite3
import tempfile
from pathlib import Path
from build_jlpt_db import build, ROOT, LEVELS

def export(destination=None):
    target = Path(destination) if destination else ROOT / "public" / "jlpt" / "vocabulary" / "data"
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "jlpt.sqlite"
        build(db_path)
        with sqlite3.connect(str(db_path)) as db:
            for level in LEVELS:
                records = db.execute("""
                    SELECT v.id, v.expression, v.reading, v.meaning_en, v.meaning_zh
                    FROM vocabulary v JOIN vocabulary_levels vl ON vl.vocabulary_id=v.id
                    WHERE vl.level=? ORDER BY v.expression, v.reading
                """, (level,)).fetchall()
                payload = {"level": level, "source": "jamsinclair/open-anki-jlpt-decks",
                           "official_exam_appearances_available": False,
                           "words": [{"id": i, "expression": e, "reading": r,
                                      "meaning_en": en, "meaning_zh": zh}
                                     for i,e,r,en,zh in records]}
                path = target / (level.lower() + ".json")
                path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",",":")), encoding="utf-8")
                print(path.relative_to(ROOT), len(records))
if __name__ == "__main__":
    export()
