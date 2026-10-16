#!/usr/bin/env python3
"""Build a reproducible local SQLite JLPT database from tracked CSV reference lists."""
import argparse
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEVELS = ("N5", "N4", "N3", "N2", "N1")
SOURCE = "jamsinclair-open-anki-jlpt-decks"

def build(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    con = sqlite3.connect(str(output))
    con.execute("PRAGMA foreign_keys=ON")
    try:
        con.executescript((ROOT / "database" / "schema.sql").read_text(encoding="utf-8"))
        con.execute("""INSERT INTO sources(id,title,publisher,source_type,url,license,permission_status,note)
          VALUES(?,?,?,?,?,?,?,?)""",
          (SOURCE,"open-anki-jlpt-decks","jamsinclair","community",
           "https://github.com/jamsinclair/open-anki-jlpt-decks","MIT","attribution_required",
           "Community reference vocabulary; NOT official exam appearance evidence."))
        for level in LEVELS:
            path = ROOT / "data-src" / (level.lower() + ".csv")
            if not path.exists():
                raise FileNotFoundError(path)
            with path.open(encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    expression = (row.get("expression") or "").strip()
                    reading = (row.get("reading") or "").strip()
                    if not expression:
                        continue
                    con.execute("""INSERT INTO vocabulary(expression,reading,meaning_en)
                      VALUES(?,?,?) ON CONFLICT(expression,reading) DO UPDATE SET
                      meaning_en=COALESCE(vocabulary.meaning_en,excluded.meaning_en)""",
                      (expression, reading, (row.get("meaning") or "").strip() or None))
                    vid = con.execute("SELECT id FROM vocabulary WHERE expression=? AND reading=?",
                                      (expression,reading)).fetchone()[0]
                    con.execute("""INSERT OR IGNORE INTO vocabulary_levels(vocabulary_id,level,source_id)
                                   VALUES(?,?,?)""", (vid,level,SOURCE))
        con.commit()
        errors = con.execute("PRAGMA foreign_key_check").fetchall()
        if errors:
            raise RuntimeError("Foreign key integrity errors: " + repr(errors[:5]))
        print("Database:", output)
        print("Vocabulary:", con.execute("SELECT COUNT(*) FROM vocabulary").fetchone()[0])
        for level in LEVELS:
            print(level, con.execute("SELECT COUNT(*) FROM vocabulary_levels WHERE level=?",
                                     (level,)).fetchone()[0])
        print("Verified official appearances:",
              con.execute("SELECT COUNT(*) FROM official_vocabulary_frequency").fetchone()[0])
    finally:
        con.close()

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=ROOT / "database" / "jlpt.sqlite")
    args = p.parse_args()
    build(args.output)
