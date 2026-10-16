# JLPT database v1

This directory is the **source-of-truth schema**, not a hosted production database. The existing ShiCiJP website is static. Build a local SQLite file with:

```bash
python3 scripts/build_jlpt_db.py
```

The command imports `data-src/n1.csv` through `n5.csv` into `database/jlpt.sqlite`. It is repeatable and intentionally replaces the generated database. **Do not manually edit the generated SQLite file**; keep curated corrections/imports as versioned input files before adding them to the build process.

## Tables

- `sources`: source, license, permission status and URL.
- `vocabulary`: one record per expression + reading, with optional Chinese translation and POS.
- `vocabulary_levels`: many-to-many reference level membership, preserving source.
- `exams`: papers with year/session, provenance and official status.
- `questions`, `options`: individual items, answer and explanations.
- `grammar`, `question_grammar`: grammar links.
- `question_vocabulary`: evidence-backed vocabulary occurrence in a question.

## Frequency rules

`official_vocabulary_frequency` counts only entries linked to an official-public source, an exam flagged official, and a question-word link flagged `verified_original`. The view distinguishes unique question appearances, unique papers and token occurrences. This is **observed frequency in the verified sample**, not the probability of appearance in future JLPT exams.

`practice_vocabulary_frequency` is separate and cannot inflate official frequency. Importing a community reference word list does **not** create exam occurrence records. No unverified year, exam number, question, answer or citation is fabricated.

## Licensing and editorial checks

Only store full question texts when the license or permission allows it. For restricted originals, store bibliographic references and independently written commentary rather than copying the question. Review explanations and translations before publishing. JLPT does not publish a fixed exhaustive official level-by-level vocabulary list.

## Static deployment

Do not expose a writable SQLite file through GitHub Pages. This database is a local build/editing foundation. A future exporter can produce read-only JSON slices for the existing static `public/jlpt/` frontend. A future backend, if needed, can reuse this schema with migrations.

## Example queries

```sql
PRAGMA foreign_keys=ON;
SELECT v.expression, v.reading, v.meaning_en
FROM vocabulary v JOIN vocabulary_levels vl ON vl.vocabulary_id=v.id
WHERE vl.level='N5' ORDER BY v.expression LIMIT 20;

SELECT * FROM official_vocabulary_frequency WHERE level='N1'
ORDER BY question_count DESC LIMIT 20;
```

## Unified content build (recommended)

Run `npm run build:jlpt-content` to rebuild the local SQLite database from the
five tracked community vocabulary CSV files **and** the reviewed original practice
questions, then publish read-only JSON for each level under
`public/jlpt/vocabulary/data/{n1,n2,n3,n4,n5}.json`.

The exported `original_practice_question_count` measures only the number of
**our own** questions referencing a word at that level. It is **not** a count
of official JLPT appearances. The exporter explicitly sets
`official_exam_appearances_available: false`. No official frequency should
be displayed until verified exam evidence is imported with rights review.

The existing website vocabulary page still reads the tracked CSV files;
this JSON export is a database-backed integration format for the next stage.
Do not claim the static website is already reading the exported JSON.

Run `npm run test:jlpt-content` before publishing updated questions.

### Completion criteria

- N1–N5 vocabulary source and level provenance retained, with separately
  reviewed Chinese definitions and examples; never invent missing meanings.
- Every published question has a source, rights status, answer, full option
  explanations and links to vocabulary/grammar.
- Grammar explanations and examples are reviewed, not empty placeholders.
- Official frequency and original-practice frequency remain separate.
- Automated database integrity tests and real browser testing pass before launch.
