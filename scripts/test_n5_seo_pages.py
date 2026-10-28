#!/usr/bin/env python3
"""Assert N5 HTML output, navigation, canonicals and sitemap are consistent."""
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from build_n5_seo_pages import ROOT, OUT, SOURCE, REFERENCE, SITEMAP, BASE, path_for
def main():
    data=json.loads(SOURCE.read_text(encoding="utf-8"))
    with REFERENCE.open(encoding="utf-8-sig",newline="") as file:
        reference={(r["expression"].strip(),r["reading"].strip()) for r in csv.DictReader(file)}
    expected={}
    for entry in data["entries"]:
        key=(entry.get("variant_of") or entry["expression"],entry["reading"])
        if key in reference and all(str(entry.get(k) or "").strip() for k in ("meaning_zh","example_ja","example_zh")):
            if key in expected:raise AssertionError("duplicate draft reference")
            expected[key]=entry
    assert expected,"No complete N5 drafts"
    index=(OUT/"index.html").read_text(encoding="utf-8")
    assert "<h1>" in index and "draft" not in index.lower()
    paths={"/jlpt/vocabulary/n5/"}
    for key,entry in expected.items():
        url=path_for({"expression":key[0],"reading":key[1]})
        paths.add(url)
        content=(ROOT/"public"/url.strip("/")/"index.html").read_text(encoding="utf-8")
        assert '<link rel="canonical" href="'+BASE+url+'">' in content,url
        assert content.count("<h1") == 1,url
        assert "<title>" in content and 'name="description"' in content,url
        assert "中文草稿" in content and "待复核" in content,url
        assert 'href="'+url+'"' in index,url
    root=ET.parse(SITEMAP).getroot()
    locs=[node.text for node in root.iter() if node.tag.endswith("}loc")]
    assert len(locs)==len(set(locs)),"Duplicate sitemap URLs"
    assert {BASE+p for p in paths}.issubset(set(locs)),"Missing sitemap URL"
    assert '<link rel="canonical" href="'+BASE+'/jlpt/vocabulary/n5/">' in index
    assert all((ROOT/"public"/p.strip("/")/"index.html").is_file() for p in paths)
    print("N5 SEO validation passed:",len(expected),"word pages; index, canonicals, links and sitemap")
if __name__=="__main__":main()
