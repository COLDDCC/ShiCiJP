#!/usr/bin/env python3
"""Generate crawlable N5 pages from the same database export as the vocabulary UI."""
import argparse
import hashlib
import html
import json
import re
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

from build_jlpt_content import build_content
from build_jlpt_db import ROOT

ORIGIN = 'https://shicijp.com'
BASE = '/jlpt/vocabulary/n5/'
GROUPS = {
    'numbers': ('数字与日期', '数字、数量、日期与时长读法'),
    'affixes': ('前缀与后缀', '敬语前缀、量词与接尾表达'),
    'loanwords': ('片假名词', '日常生活中的外来语'),
    'a': ('あ行', 'あ・い・う・え・お 开头的读音'),
    'ka': ('か行', 'か・き・く・け・こ（含浊音）'),
    'sa': ('さ行', 'さ・し・す・せ・そ（含浊音）'),
    'ta': ('た行', 'た・ち・つ・て・と（含浊音）'),
    'na': ('な行', 'な・に・ぬ・ね・の 开头的读音'),
    'ha': ('は行', 'は・ひ・ふ・へ・ほ（含浊音、半浊音）'),
    'ma': ('ま行', 'ま・み・む・め・も 开头的读音'),
    'ya': ('や行', 'や・ゆ・よ 开头的读音'),
    'ra': ('ら行', 'ら・り・る・れ・ろ 开头的读音'),
    'wa': ('わ行', 'わ 开头的读音'),
}


def esc(value):
    return html.escape(str(value), quote=True)


def key(word):
    return (word['expression'], word['reading'])


def word_path(word):
    identity = json.dumps(key(word), ensure_ascii=False, separators=(',', ':'))
    return BASE + 'w-' + hashlib.sha256(identity.encode('utf-8')).hexdigest()[:16] + '/'


def category(word):
    expression = unicodedata.normalize('NFKC', word['expression'])
    reading = unicodedata.normalize('NFKC', word['reading'])
    if any(c in expression for c in ('~', '〜', '～')):
        return 'affixes'
    if re.fullmatch(r'[一二三四五六七八九十百千万零]+(?:日|つ|人|月|歳)?', expression):
        return 'numbers'
    if '\u30a1' <= reading[0] <= '\u30fa':
        return 'loanwords'
    first = reading[0]
    for group, chars in [('a', 'あいうえお'), ('ka', 'かきくけこがぎぐげご'),
                         ('sa', 'さしすせそざじずぜぞ'), ('ta', 'たちつてとだぢづでど'),
                         ('na', 'なにぬねの'), ('ha', 'はひふへほばびぶべぼぱぴぷぺぽ'),
                         ('ma', 'まみむめも'), ('ya', 'やゆよ'), ('ra', 'らりるれろ'), ('wa', 'わ')]:
        if first in chars:
            return group
    raise ValueError('Unclassified reading: ' + repr(key(word)))


def layout(title, description, path, body):
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | 拾词</title><meta name="description" content="{esc(description)}">
<link rel="canonical" href="{ORIGIN}{path}"><link rel="icon" href="/favicon.ico">
<link rel="stylesheet" href="/css/style.css"><link rel="stylesheet" href="/jlpt/vocabulary/n5-pages.css">
<script src="/jlpt/vocabulary/n5-pages.js" defer></script></head><body>
<header class="n5-header"><a class="n5-brand" href="/">拾词</a><nav aria-label="主导航"><a href="/jlpt/">学习中心</a><a href="/jlpt/vocabulary/">词库搜索</a></nav></header>
<main class="n5-main">{body}</main>
<footer class="n5-footer">社区参考词表，不是官方固定考试清单。中文释义与例句为草稿，待审核。</footer>
</body></html>\n'''


def crumbs(*items):
    links = ['<a href="/jlpt/">学习中心</a>']
    links.extend(f'<a href="{path}">{esc(label)}</a>' for path, label in items)
    return '<nav class="n5-crumbs" aria-label="面包屑">' + '<span aria-hidden="true"> / </span>'.join(links) + '</nav>'


def source_note():
    return '''<details class="n5-source"><summary>来源与审核状态</summary>
<p>等级、表记与读音来自 <a href="https://github.com/jamsinclair/open-anki-jlpt-decks">open-anki-jlpt-decks</a>（MIT）。中文释义、例句及翻译由拾词整理，仍待审核。未核实的官方真题出现次数不展示为考频。</p></details>'''


def render(words):
    ordered = sorted(words, key=lambda w: (unicodedata.normalize('NFKC', w['reading']), w['expression']))
    groups = {g: [w for w in ordered if category(w) == g] for g in GROUPS}
    pages = {}
    cards = ''.join(f'<a class="n5-card" href="{BASE}group-{g}/"><strong>{label}</strong><span>{len(groups[g])} 词 · {desc}</span></a>'
                    for g, (label, desc) in GROUPS.items() if groups[g])
    pages[BASE] = layout('N5 日语单词：中文释义、读音与例句',
        f'按读音、数字日期和前后缀浏览 {len(words)} 条 N5 社区参考词汇，直接查看中文释义、日语例句与翻译；中文内容待审核。', BASE,
        crumbs() + f'<p class="n5-eyebrow">JLPT N5 · {len(words)} 条参考词汇</p><h1>N5 单词，按组学习。</h1>'
        '<p class="n5-lead">先选一组，再看读音、中文释义与例句。</p><span class="n5-badge">中文草稿 · 待审核</span>'
        '<nav class="n5-grid" aria-label="N5 单词分类">' + cards + '</nav>' + source_note())
    for group, members in groups.items():
        if not members:
            continue
        label = GROUPS[group][0]
        path = BASE + 'group-' + group + '/'
        rows = ''.join(f'<li data-word><a href="{word_path(w)}"><strong lang="ja">{esc(w["expression"])}</strong>'
                       f'<span lang="ja">{esc(w["reading"])}</span><span>{esc(w["meaning_zh"])}</span><span aria-hidden="true">→</span></a></li>' for w in members)
        pages[path] = layout(f'N5 {label}单词：读音、中文释义与例句',
            f'N5 {label}分类包含 {len(members)} 条参考词汇。查看假名、中文释义与双语例句，中文内容为待审核草稿。', path,
            crumbs((BASE, 'N5 单词')) + f'<p class="n5-eyebrow">N5 · {len(members)} 条参考词汇</p><h1>{label}单词</h1>'
            '<span class="n5-badge">中文草稿 · 待审核</span>'
            '<div class="n5-filter" hidden><label for="word-filter">在本组查找</label><input id="word-filter" type="search" placeholder="日语、假名或中文" autocomplete="off">'
            f'<p id="filter-status" role="status" aria-live="polite">{len(members)} 条词汇</p></div>'
            f'<ul class="n5-words">{rows}</ul><p id="filter-empty" hidden>没有找到匹配词汇，试试其他写法。</p>' + source_note())
        for i, word in enumerate(members):
            wpath = word_path(word)
            links = []
            if i:
                prev = members[i - 1]
                links.append(f'<a rel="prev" href="{word_path(prev)}">← {esc(prev["expression"])}</a>')
            if i + 1 < len(members):
                nxt = members[i + 1]
                links.append(f'<a rel="next" href="{word_path(nxt)}">{esc(nxt["expression"])} →</a>')
            body = crumbs((BASE, 'N5 单词'), (path, label))
            body += f'<p class="n5-eyebrow">N5 · 社区参考词汇</p><article class="n5-word"><h1 lang="ja">{esc(word["expression"])}</h1>'
            body += f'<p class="n5-reading" lang="ja">{esc(word["reading"])}</p><span class="n5-badge">中文草稿 · 待审核</span>'
            body += f'<h2>中文释义</h2><p class="n5-meaning">{esc(word["meaning_zh"])}</p><h2>例句</h2>'
            body += f'<p class="n5-example" lang="ja">{esc(word["example_ja"])}</p><p>{esc(word["example_zh"])}</p></article>'
            body += '<nav class="n5-word-nav" aria-label="同组词汇">' + ''.join(links) + '</nav>' + source_note()
            if wpath in pages:
                raise ValueError('Duplicate canonical path: ' + wpath)
            pages[wpath] = layout(f'{word["expression"]}（{word["reading"]}）是什么意思？N5 单词',
                f'{word["expression"]}的读音：{word["reading"]}；中文释义：{word["meaning_zh"]}。查看日语例句和中文翻译。N5 社区参考词汇，中文内容待审核。', wpath, body)
    return pages


def build_pages(public_root):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        build_content(root / 'jlpt.sqlite', root / 'data')
        payload = json.loads((root / 'data/n5.json').read_text(encoding='utf-8'))
    if payload['review_status'] != 'draft_editorial_review':
        raise ValueError('N5 pages must preserve draft status')
    words = payload['words']
    if len({key(w) for w in words}) != len(words):
        raise ValueError('Duplicate N5 reference keys')
    for word in words:
        for field in ('expression', 'reading', 'meaning_zh', 'example_ja', 'example_zh'):
            if not isinstance(word.get(field), str) or not word[field].strip():
                raise ValueError(f'Incomplete N5 word: {key(word)} / {field}')
    pages = render(words)
    destination = public_root / BASE.strip('/')
    expected = {public_root / path.strip('/') / 'index.html' for path in pages}
    if destination.exists():
        for old in destination.rglob('index.html'):
            if old not in expected:
                old.unlink()
    for path, content in pages.items():
        target = public_root / path.strip('/') / 'index.html'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')
    # Retain existing site URLs, replacing only this generator's namespace.
    sitemap = public_root / 'sitemap.xml'
    ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    tree = ET.parse(sitemap)
    document = tree.getroot()
    for item in list(document):
        loc = item.find(f'{{{ns}}}loc')
        if loc is not None and (loc.text or '').startswith(ORIGIN + BASE):
            document.remove(item)
    for path in sorted(pages):
        item = ET.SubElement(document, f'{{{ns}}}url')
        ET.SubElement(item, f'{{{ns}}}loc').text = ORIGIN + path
    ET.register_namespace('', ns)
    tree.write(sitemap, encoding='utf-8', xml_declaration=True)
    print(f'N5 static pages: {len(words)} words, {len(pages) - len(words) - 1} groups; {len(pages)} canonical URLs')
    return pages, words


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--public-root', type=Path, default=ROOT / 'public')
    args = parser.parse_args()
    build_pages(args.public_root)


if __name__ == '__main__':
    main()
