#!/usr/bin/env python3
"""Post-deploy public HTTPS smoke check. Fails CI if production is not accessible."""
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

ORIGIN = 'https://shicijp.com'
PAGES = {
    '/': ('id="searchForm"', 'id="vocab-search"'),
    '/jlpt/vocabulary/n5/': ('rel="canonical"', 'N5'),
    '/jlpt/review/': ('id="review-card"', 'noindex'),
    '/sitemap.xml': ('urlset', '/jlpt/vocabulary/n5/'),
}
def load(path):
    req = urllib.request.Request(ORIGIN + path, headers={'User-Agent':'ShiCiJP-release-smoke/1.0', 'Cache-Control':'no-cache'})
    with urllib.request.urlopen(req, timeout=25) as r:
        if r.status != 200:raise ValueError(f'{path}: HTTP {r.status}')
        return r.read().decode('utf-8')
for path,markers in PAGES.items():
    last = None
    for attempt in range(8):
        try:
            body=load(path)
            for marker in markers:
                if marker not in body: raise ValueError(f'{path}: missing {marker}')
            if path.endswith('sitemap.xml'): ET.fromstring(body)
            print(f'PASS production {ORIGIN + path}')
            break
        except (ValueError, UnicodeError, urllib.error.URLError, TimeoutError) as exc:
            last=exc
            if attempt<7: time.sleep(15)
    else: raise SystemExit(f'FAIL production {path}: {last}')
print('Production smoke checks passed')
