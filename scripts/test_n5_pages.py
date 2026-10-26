#!/usr/bin/env python3
"""Check generated N5 content, canonical URLs, link graph and reproducibility."""
import html
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

from build_jlpt_db import ROOT
from build_n5_pages import BASE, ORIGIN, build_pages, layout, word_path


class Page(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.h1s = 0
        self.title = ''
        self.in_title = False
        self.canonicals = []
        self.descriptions = []
        self.links = []
        self.text = []
        self.feed(content)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'h1':
            self.h1s += 1
        if tag == 'title':
            self.in_title = True
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonicals.append(attrs.get('href'))
        if tag == 'meta' and attrs.get('name') == 'description':
            self.descriptions.append(attrs.get('content'))
        if tag == 'a':
            self.links.append(attrs.get('href', ''))

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        self.text.append(data)
        if self.in_title:
            self.title += data


class N5PageTests(unittest.TestCase):
    def test_generated_site(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copy(ROOT / 'public/sitemap.xml', root / 'sitemap.xml')
            pages, words = build_pages(root)
            self.assertEqual(len(words), 718)
            self.assertEqual(len(pages), 732)
            titles, descriptions, canonicals = set(), set(), set()
            inbound = set()
            graph = {}
            for path, content in pages.items():
                page = Page(content)
                self.assertEqual(page.h1s, 1, path)
                self.assertEqual(page.canonicals, [ORIGIN + path], path)
                self.assertEqual(len(page.descriptions), 1, path)
                self.assertTrue(page.descriptions[0].strip(), path)
                self.assertNotIn(page.title, titles, path)
                self.assertNotIn(page.descriptions[0], descriptions, path)
                titles.add(page.title)
                descriptions.add(page.descriptions[0])
                canonicals.add(page.canonicals[0])
                self.assertIn('待审核', ''.join(page.text), path)
                self.assertNotIn('noindex', content, path)
                self.assertEqual((root / path.strip('/') / 'index.html').read_text(encoding='utf-8'), content)
                graph[path] = []
                for link in page.links:
                    target = urlparse(urljoin(ORIGIN + path, link))
                    if target.netloc != 'shicijp.com':
                        continue
                    target_path = unquote(target.path)
                    if target_path.startswith(BASE):
                        self.assertIn(target_path, pages, (path, link))
                        inbound.add(target_path)
                        graph[path].append(target_path)
                    else:
                        local = ROOT / 'public' / target_path.lstrip('/')
                        self.assertTrue(local.exists(), (path, link))
            self.assertEqual(inbound, set(pages), 'Every generated page needs an incoming link')
            # Every word is one click from its group, two from the overview.
            reachable = {BASE} | set(graph[BASE])
            for group in graph[BASE]:
                reachable.update(graph[group])
            self.assertEqual(reachable, set(pages))
            for word in words:
                text = ''.join(Page(pages[word_path(word)]).text)
                for field in ('expression', 'reading', 'meaning_zh', 'example_ja', 'example_zh'):
                    self.assertIn(word[field], text, (word['expression'], field))
            ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            urls = [e.text for e in ET.parse(root / 'sitemap.xml').findall('s:url/s:loc', ns)]
            self.assertEqual(len(urls), len(set(urls)))
            self.assertEqual({u for u in urls if u.startswith(ORIGIN + BASE)}, canonicals)
            before = (root / 'sitemap.xml').read_bytes()
            stale = root / BASE.strip('/') / 'w-obsolete/index.html'
            stale.parent.mkdir()
            stale.write_text('obsolete', encoding='utf-8')
            second_pages, _ = build_pages(root)
            self.assertEqual(pages, second_pages)
            self.assertEqual(before, (root / 'sitemap.xml').read_bytes())
            self.assertFalse(stale.exists(), 'Removed words must not leave indexed stale pages')

    def test_stable_paths_distinguish_readings(self):
        a = {'expression': '一日', 'reading': 'いちにち'}
        b = {'expression': '一日', 'reading': 'ついたち'}
        self.assertEqual(word_path(a), word_path(dict(a)))
        self.assertNotEqual(word_path(a), word_path(b))
        self.assertNotIn('?', word_path(a))

    def test_html_is_escaped(self):
        value = '<script>alert("x")</script>'
        page = layout(value, value, BASE, '<h1>Safe</h1>')
        self.assertNotIn(value, page)
        self.assertIn(html.escape(value, quote=True), page)


if __name__ == '__main__':
    unittest.main()
