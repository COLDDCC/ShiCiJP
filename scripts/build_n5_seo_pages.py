#!/usr/bin/env python3
"""Build crawlable N5 vocabulary pages from reference CSV and labelled Chinese drafts."""
import csv
import hashlib
import html
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://shicijp.com"
OUT = ROOT / "public/jlpt/vocabulary/n5"
SOURCE = ROOT / "database/content/vocabulary-zh-reviewed.json"
REFERENCE = ROOT / "data-src/n5.csv"
SITEMAP = ROOT / "public/sitemap.xml"
GROUPS = [("a","あ行","あいうえお"),("ka","か行","かきくけこ"),("sa","さ行","さしすせそ"),("ta","た行","たちつてと"),("na","な行","なにぬねの"),("ha","は行","はひふへほ"),("ma","ま行","まみむめも"),("ya","や行","やゆよ"),("ra","ら行","らりるれろ"),("wa","わ行","わをん")]
CSS = """<style>:root{color-scheme:light dark}body{font-family:system-ui,-apple-system,'Noto Sans JP',sans-serif;margin:0;background:Canvas;color:CanvasText;line-height:1.75}a{color:#176a93}a:focus-visible{outline:3px solid #ec991b;outline-offset:3px}.wrap{max-width:960px;margin:auto;padding:22px 18px 75px}header{border-bottom:1px solid #aaa5;padding:14px 18px}header nav{max-width:960px;margin:auto;display:flex;gap:20px;flex-wrap:wrap}h1{font-size:clamp(1.8rem,4vw,2.7rem);line-height:1.3}h2{margin:32px 0 8px}.muted{opacity:.76}.pill{display:inline-block;border:1px solid #8887;border-radius:20px;padding:3px 12px;font-size:.88rem}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,235px),1fr));gap:10px;padding:0;list-style:none}.card{border:1px solid #9996;border-radius:12px;padding:13px 16px}.card a{font-weight:700;font-size:1.12rem}.card small{display:block}.crumb{font-size:.9rem}.example{border-left:3px solid #4685a8;padding-left:16px}.groupnav{display:flex;gap:8px;flex-wrap:wrap}.groupnav a{border:1px solid #8887;border-radius:9px;padding:5px 10px}ruby rt{font-size:.5em}footer{border-top:1px solid #aaa5;margin-top:45px;padding-top:18px;font-size:.9rem}@media(max-width:380px){.wrap{padding-left:14px;padding-right:14px}}</style>"""
def esc(value): return html.escape(str(value or ""), quote=True)
def path_for(entry):
    identity=json.dumps((entry["expression"],entry["reading"]),ensure_ascii=False,separators=(",",":"))
    return "/jlpt/vocabulary/n5/w-" + hashlib.sha256(identity.encode()).hexdigest()[:16] + "/"
def group_for(reading):
    first=reading[:1]
    if not first:return "other"
    o=ord(first)
    if 0x30A1<=o<=0x30F6:first=chr(o-0x60)
    for ident,_,chars in GROUPS:
        if first in chars:return ident
    return "other"
def page(title,description,path,body):
    return ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>'+esc(title)+'</title><meta name="description" content="'+esc(description)+'">'
        '<link rel="canonical" href="'+BASE+esc(path)+'">'
        '<meta name="robots" content="index,follow">'+CSS+'</head><body>'
        '<header><nav><a href="/">拾词 · 文本分析</a><a href="/jlpt/">JLPT 学习</a>'
        '<a href="/jlpt/vocabulary/">词汇搜索</a><a href="/jlpt/vocabulary/n5/">N5 词汇</a></nav></header>'
        '<main class="wrap">'+body+'</main></body></html>')
def write_page(path,content):
    target=ROOT/"public"/path.strip("/")/"index.html"
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(content,encoding="utf-8")
def build():
    editorial=json.loads(SOURCE.read_text(encoding="utf-8"))
    if editorial.get("review_status")!="draft_editorial_review":
        raise ValueError("Review status changed: verify editorial policy before publishing")
    ref={}
    with REFERENCE.open(encoding="utf-8-sig",newline="") as fh:
        for row in csv.DictReader(fh):
            key=(row["expression"].strip(),row["reading"].strip())
            if key[0] and key[1]:ref[key]=row
    entries={}
    for draft in editorial["entries"]:
        target=(draft.get("variant_of") or draft["expression"],draft["reading"])
        if target not in ref:continue
        if not all(isinstance(draft.get(f),str) and draft[f].strip() for f in ("meaning_zh","example_ja","example_zh")):continue
        if target in entries:raise ValueError("Duplicate target: "+repr(target))
        entries[target]={**draft,"expression":target[0],"reading":target[1]}
    if not entries:raise ValueError("No eligible entries; refusing an empty public directory")
    groups={ident:[] for ident,_,_ in GROUPS}
    groups["other"]=[]
    words=sorted(entries.values(),key=lambda x:(x["reading"],x["expression"]))
    urls=["/jlpt/vocabulary/n5/"]
    for item in words:
        url=path_for(item);urls.append(url)
        groups[group_for(item["reading"])].append(item)
        title=item["expression"]+"（"+item["reading"]+"）是什么意思？N5 日语单词 | 拾词"
        description=item["expression"]+" 的日语读音、中文参考释义和日中双语例句。社区 JLPT N5 参考词汇，中文内容尚待编辑审核。"
        body=('<p class="crumb"><a href="/jlpt/vocabulary/n5/">N5 词汇</a> / '+esc(item["expression"])+'</p>'
          +'<h1 lang="ja">'+esc(item["expression"])+'</h1><p><span class="pill">JLPT N5 · 社区参考</span> <span class="pill">中文草稿 · 待复核</span></p>'
          +'<p><strong>读音：</strong><span lang="ja">'+esc(item["reading"])+'</span></p>'
          +'<h2>中文释义</h2><p>'+esc(item["meaning_zh"])+'</p>'
          +'<h2>日语例句</h2><div class="example"><p lang="ja">'+esc(item["example_ja"])+'</p><p>'+esc(item["example_zh"])+'</p></div>'
          +'<p class="muted">此词属于社区整理的 JLPT N5 参考集合，并非官方指定词表。中文释义及例句处于编辑草稿阶段，可能有误。</p>'
          +'<p><a href="/jlpt/vocabulary/n5/#'+group_for(item["reading"])+'">← 返回词汇分类</a> · <a href="/">用文本分析器查词</a></p>')
        write_page(url,page(title,description,url,body))
    nav='<nav class="groupnav" aria-label="五十音分类">'+''.join('<a href="#'+k+'">'+v+'</a>' for k,v,_ in GROUPS if groups[k])+('</nav>')
    cards=[]
    for key,label,_ in GROUPS+[("other","其他","")]:
        subset=groups[key]
        if not subset:continue
        cards.append('<section id="'+key+'"><h2>'+label+' <small>('+str(len(subset))+')</small></h2><ul class="cards">'
          +''.join('<li class="card"><a lang="ja" href="'+path_for(x)+'">'+esc(x["expression"])+'</a><small lang="ja">'+esc(x["reading"])+'</small><small>'+esc(x["meaning_zh"])+'</small></li>' for x in subset)
          +'</ul></section>')
    body='<p class="crumb"><a href="/jlpt/">JLPT 学习</a> / N5 词汇</p><h1>JLPT N5 日语词汇表：五十音分类与中文例句</h1>'
    body+='<p>按五十音浏览 '+str(len(words))+' 条有中文草稿的 N5 参考词汇，点击即可查看假名、中文释义和双语例句。</p>'
    body+='<p class="muted">参考集合共 '+str(len(ref))+' 条，当前展示 '+str(len(words))+' 条中文内容完整的草稿；尚未完成逐条人工审核，不等同于官方 N5 词表或审核通过率。</p>'+nav+''.join(cards)
    body+='<footer>资料来自社区整理的 <a href="https://github.com/jamsinclair/open-anki-jlpt-decks">JLPT 词表</a>；内容标记为待审校草稿。<a href="/jlpt/vocabulary/">搜索其他级别词汇</a>。</footer>'
    write_page("/jlpt/vocabulary/n5/",page("JLPT N5 日语单词表 · 五十音分类、中文例句 | 拾词","按五十音浏览 JLPT N5 参考日语单词，查看读音、中文草稿释义和日中双语例句。","/jlpt/vocabulary/n5/",body))
    ns="http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("",ns)
    tree=ET.parse(SITEMAP)
    root=tree.getroot()
    for node in list(root):
        loc=node.find("{"+ns+"}loc")
        if loc is not None and loc.text and loc.text.startswith(BASE+"/jlpt/vocabulary/n5/"):
            root.remove(node)
    for url in urls:
        el=ET.SubElement(root,"{"+ns+"}url")
        ET.SubElement(el,"{"+ns+"}loc").text=BASE+url
    tree.write(SITEMAP,encoding="utf-8",xml_declaration=True)
    print("Published",len(words),"N5 draft pages plus index; reference rows:",len(ref))
if __name__=="__main__":build()
