-- ShiCiJP JLPT relational database v1. Run with PRAGMA foreign_keys=ON per connection.
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS sources (
 id TEXT PRIMARY KEY, title TEXT NOT NULL, publisher TEXT,
 source_type TEXT NOT NULL CHECK(source_type IN ('official_public','licensed','community','original','unverified')),
 url TEXT, license TEXT, permission_status TEXT NOT NULL DEFAULT 'review_needed',
 note TEXT
);
CREATE TABLE IF NOT EXISTS vocabulary (
 id INTEGER PRIMARY KEY, expression TEXT NOT NULL, reading TEXT NOT NULL DEFAULT '',
 meaning_en TEXT, meaning_zh TEXT, part_of_speech TEXT,
 UNIQUE(expression,reading)
);
CREATE TABLE IF NOT EXISTS vocabulary_levels (
 vocabulary_id INTEGER NOT NULL REFERENCES vocabulary(id) ON DELETE CASCADE,
 level TEXT NOT NULL CHECK(level IN ('N1','N2','N3','N4','N5')),
 source_id TEXT NOT NULL REFERENCES sources(id),
 PRIMARY KEY(vocabulary_id,level,source_id)
);
CREATE TABLE IF NOT EXISTS exams (
 id TEXT PRIMARY KEY, level TEXT NOT NULL CHECK(level IN ('N1','N2','N3','N4','N5')),
 title TEXT NOT NULL, exam_year INTEGER, session TEXT,
 source_id TEXT NOT NULL REFERENCES sources(id),
 is_official INTEGER NOT NULL DEFAULT 0 CHECK(is_official IN (0,1)),
 publication_status TEXT NOT NULL DEFAULT 'metadata_only'
);
CREATE TABLE IF NOT EXISTS questions (
 id TEXT PRIMARY KEY, exam_id TEXT NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
 section TEXT NOT NULL, question_number INTEGER NOT NULL,
 stem TEXT, correct_option INTEGER CHECK(correct_option BETWEEN 1 AND 4),
 explanation_zh TEXT, difficulty TEXT,
 content_rights TEXT NOT NULL DEFAULT 'metadata_only',
 UNIQUE(exam_id,section,question_number)
);
CREATE TABLE IF NOT EXISTS options (
 question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
 option_number INTEGER NOT NULL CHECK(option_number BETWEEN 1 AND 4),
 text TEXT NOT NULL, explanation_zh TEXT,
 PRIMARY KEY(question_id,option_number)
);
CREATE TABLE IF NOT EXISTS grammar (
 id TEXT PRIMARY KEY, expression TEXT NOT NULL, level TEXT,
 explanation_zh TEXT, example_ja TEXT, example_zh TEXT
);
CREATE TABLE IF NOT EXISTS question_vocabulary (
 question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
 vocabulary_id INTEGER NOT NULL REFERENCES vocabulary(id) ON DELETE CASCADE,
 occurrence_count INTEGER NOT NULL DEFAULT 1 CHECK(occurrence_count > 0),
 evidence TEXT NOT NULL CHECK(evidence IN ('verified_original','licensed_material','original_practice','manual_unverified')),
 PRIMARY KEY(question_id,vocabulary_id)
);
CREATE TABLE IF NOT EXISTS question_grammar (
 question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
 grammar_id TEXT NOT NULL REFERENCES grammar(id) ON DELETE CASCADE,
 PRIMARY KEY(question_id,grammar_id)
);
CREATE INDEX IF NOT EXISTS idx_vocab_expression ON vocabulary(expression);
CREATE INDEX IF NOT EXISTS idx_vocab_reading ON vocabulary(reading);
CREATE INDEX IF NOT EXISTS idx_vocab_levels ON vocabulary_levels(level);
CREATE INDEX IF NOT EXISTS idx_questions_exam ON questions(exam_id);
CREATE INDEX IF NOT EXISTS idx_qv_vocab ON question_vocabulary(vocabulary_id);
-- Only verified original exam evidence contributes to official occurrence counts.
CREATE VIEW IF NOT EXISTS official_vocabulary_frequency AS
 SELECT v.id AS vocabulary_id, v.expression, v.reading, e.level,
 COUNT(DISTINCT q.id) AS question_count, COUNT(DISTINCT e.id) AS paper_count,
 SUM(qv.occurrence_count) AS token_count
 FROM question_vocabulary qv
 JOIN vocabulary v ON v.id=qv.vocabulary_id
 JOIN questions q ON q.id=qv.question_id
 JOIN exams e ON e.id=q.exam_id
 JOIN sources s ON s.id=e.source_id
 WHERE e.is_official=1 AND s.source_type='official_public'
   AND qv.evidence='verified_original'
 GROUP BY v.id,e.level;
CREATE VIEW IF NOT EXISTS practice_vocabulary_frequency AS
 SELECT v.id AS vocabulary_id, e.level, COUNT(DISTINCT q.id) AS question_count
 FROM question_vocabulary qv JOIN vocabulary v ON v.id=qv.vocabulary_id
 JOIN questions q ON q.id=qv.question_id JOIN exams e ON e.id=q.exam_id
 WHERE qv.evidence='original_practice' GROUP BY v.id,e.level;
