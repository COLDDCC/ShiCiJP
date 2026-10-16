#!/usr/bin/env python3
"""Editorial integrity checks for published original JLPT questions."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/"database/content/original-practice.json"
published=ROOT/"public/jlpt/practice/questions.json"
data=json.loads(source.read_text(encoding="utf-8"))
assert data==json.loads(published.read_text(encoding="utf-8")), "Published questions are out of sync with source"
assert data["source"]["source_type"]=="original"
seen_exams=set()
seen_questions=set()
total=0
for exam in data["exams"]:
    assert exam["id"] not in seen_exams
    seen_exams.add(exam["id"])
    assert exam["level"] in {"N1","N2","N3","N4","N5"}
    numbers=set()
    for q in exam["questions"]:
        total+=1
        assert q["id"] not in seen_questions
        seen_questions.add(q["id"])
        assert q["number"] not in numbers
        numbers.add(q["number"])
        assert q["stem"].strip() and q["explanation_zh"].strip()
        assert isinstance(q["correct_option"],int) and 1<=q["correct_option"]<=4
        assert len(q["options"])==4
        assert all(o["text"].strip() and o["explanation_zh"].strip() for o in q["options"])
        assert len({o["text"] for o in q["options"]})==4
        assert all(w["expression"].strip() and w.get("occurrence_count",1)>0 for w in q.get("vocabulary",[]))
print("Validated",total,"original questions in",len(seen_exams),"practice sets")
