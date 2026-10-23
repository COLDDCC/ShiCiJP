#!/usr/bin/env python3
"""Editorial regressions and negative tests; passing is not linguistic approval."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from audit_jlpt_coverage import inspect
from build_jlpt_db import ROOT
from build_jlpt_content import build_content
from export_jlpt_vocab import export


class DraftQualityTests(unittest.TestCase):
    def setUp(self):
        self.source = json.loads((ROOT / "database/content/vocabulary-zh-reviewed.json").read_text(encoding="utf-8"))

    def audit(self, content):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "data-src", root / "data-src")
            target = root / "database/content/vocabulary-zh-reviewed.json"
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
            return inspect(root)

    def test_rejects_empty_or_non_text_content(self):
        for field in ("meaning_zh", "example_ja", "example_zh"):
            for value in ("", " \t\n", None, 123):
                with self.subTest(field=field, value=value):
                    content = copy.deepcopy(self.source)
                    content["entries"][0][field] = value
                    self.assertIn(f"entry 1: missing {field}", self.audit(content)["issues"])

    def test_rejects_missing_reading(self):
        content = copy.deepcopy(self.source)
        content["entries"][0]["reading"] = " "
        self.assertIn("entry 1: missing reading", self.audit(content)["issues"])

    def test_rejects_approved_status_for_drafts(self):
        content = copy.deepcopy(self.source)
        content["review_status"] = "approved"
        self.assertIn("Chinese drafts must retain draft_editorial_review status", self.audit(content)["issues"])

    def test_corrected_examples_keep_sense_and_reading(self):
        entries = {(e["expression"], e["reading"]): e for e in self.source["entries"]}
        # Ten pages is a quantity, not page ten; とお needs the traditional counter context.
        page = entries[("ページ", "ページ")]
        self.assertIn("十ページ", page["example_ja"])
        self.assertIn("十页内容", page["example_zh"])
        ten = entries[("十", "(〜を) とお")]
        self.assertIn("十（とお）", ten["example_ja"])
        self.assertIn("十个橘子", ten["example_zh"])
        # Avoid January/one month and そと/ほか ambiguity in beginner examples.
        self.assertIn("ひと月", entries[("一月", "ひとつき")]["example_ja"])
        self.assertIn("ほかに", entries[("外", "ほか")]["example_ja"])

    def test_both_export_commands_preserve_complete_drafts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_content(root / "test.sqlite", root / "unified")
            export(root / "standalone")
            for level in ("n1", "n2", "n3", "n4", "n5"):
                unified = json.loads((root / "unified" / (level + ".json")).read_text(encoding="utf-8"))
                standalone = json.loads((root / "standalone" / (level + ".json")).read_text(encoding="utf-8"))
                self.assertEqual(unified, standalone, level)
                self.assertEqual(standalone["review_status"], "draft_editorial_review")
                if level == "n5":
                    self.assertEqual(len(standalone["words"]), 718)
                    for word in standalone["words"]:
                        for field in ("meaning_zh", "example_ja", "example_zh"):
                            self.assertTrue(word[field].strip(), (word["expression"], field))


if __name__ == "__main__":
    unittest.main()
