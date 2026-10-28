#!/usr/bin/env python3
"""Block production deploys if generated SEO pages replace interactive learning pages."""
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[1] / "public"
index = (ROOT / "index.html").read_text(encoding="utf-8")
n5 = (ROOT / "jlpt/vocabulary/n5/index.html").read_text(encoding="utf-8")
review = (ROOT / "jlpt/review/index.html").read_text(encoding="utf-8")
assert 'id="searchForm"' in index and 'id="input"' in index, "Text analyzer must remain on homepage"
assert 'id="vocab-search"' in index and 'id="vocab-matches"' in index, "Homepage instant search missing"
assert 'href="/jlpt/review/"' in index, "Homepage review entry missing"
assert 'n5-grid' in n5 and '/jlpt/review/' in n5, "N5 directory navigation missing"
assert 'id="review-card"' in review and 'id="review-known"' in review
entries = list((ROOT / "jlpt/vocabulary/n5").glob("w-*/index.html"))
assert entries, "N5 word pages not built"
for file in entries:
    data = file.read_text(encoding="utf-8")
    assert 'data-review-action="learning"' in data, f"Missing review interaction: {file}"
    assert 'data-review-action="known"' in data, f"Missing known-word interaction: {file}"
    assert 'name="description"' in data and 'rel="canonical"' in data, f"Missing SEO metadata: {file}"
locs = [x.text for x in ET.parse(ROOT / "sitemap.xml").iter() if x.tag.endswith("}loc")]
assert len(locs) == len(set(locs)), "Duplicate URLs in sitemap"
for file in entries:
    canonical = "https://shicijp.com/jlpt/vocabulary/n5/" + file.parent.name + "/"
    assert canonical in locs, f"Sitemap missing {canonical}"
print(f"PASS: homepage, N5 directory, review and {len(entries)} interactive word pages; sitemap")
