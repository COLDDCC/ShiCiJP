# N5 draft quality pass — 2026-10-24

Status remains `draft_editorial_review`. This focused editorial pass does not
constitute a complete linguistic review of all 718 reference entries.

The database, content, coverage, synchronization, variant/export tests and full
database-to-JSON build were executed locally. N5 remains 718/718 reference words.
There is one additional unmatched apple draft (`りんご`), kept outside the database.

## Corrections

| Entry | Issue addressed |
| --- | --- |
| ページ | Distinguish reading ten pages from reading page ten in the Chinese translation. |
| 十 / (〜を) とお | Replace ordinary counting (`十まで`, normally じゅう) with a traditional item-counting example and an explicit reading. |
| 一月 / ひとつき | Write `ひと月` in the example to distinguish one month from January. |
| 外 / ほか | Use kana in the example to avoid beginners reading 外 as そと. Reference spelling stays intact. |
| 留学生 | Explicitly state studying in Japan instead of inferring that location from 日本の留学生. |
| 死ぬ | Use a pet fish as a natural beginner context; a plant example is better taught with 枯れる. |
| ～前 | Demonstrate the time sense with 寝る前 and a direct Chinese translation. |
| 方 / かた | Explain that the method sense attaches to a verb stem, unlike the polite noun for a person. |

## Safeguards

- Audit rejects blank, whitespace-only and non-text meanings/examples, missing
  readings, and a status that incorrectly represents this draft collection as approved.
- All five database exports carry the draft review status.
- The standalone vocabulary export now uses the unified content builder; it
  previously overwrote translated exports with bare reference rows without examples.
- Both export commands are checked for identical N1–N5 output, including all
  718 complete N5 drafts and the review label.
- Negative tests exercise malformed content and an incorrect approval status.
- Targeted regressions cover the corrected quantity and reading ambiguities.
- CI includes the quality tests and watches the standalone vocabulary exporter.

These checks establish structural integrity and retain specific corrections;
they do not automatically establish that every sentence is idiomatic or accurate.
Continue with contextual checks of counters, dates, polysemy and translations
before treating N5 as reviewed or expanding N4 at scale.
