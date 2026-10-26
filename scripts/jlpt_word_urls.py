"""Stable canonical URLs shared by N5 exports and static pages."""
import hashlib
import json

N5_BASE = '/jlpt/vocabulary/n5/'


def word_path(word):
    identity = json.dumps((word['expression'], word['reading']), ensure_ascii=False, separators=(',', ':'))
    return N5_BASE + 'w-' + hashlib.sha256(identity.encode('utf-8')).hexdigest()[:16] + '/'
