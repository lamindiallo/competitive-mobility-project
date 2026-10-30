"""Parse openfootball Football.TXT season files (CC0) into (home, away, home_goals, away_goals) rows.
Handles both line styles: 'Home  2-1 (1-0)  Away' and 'Home v Away  2-1 (1-0)'. Stops at a play-off section."""
import re

LINE_V = re.compile(r'^\s*(?:\d{1,2}[:.]\d{2}\s+)?(?P<h>.+?)\s+v\s+(?P<a>.+?)\s{2,}(?P<x>\d+)-(?P<y>\d+)(?:\s*\(.*)?$')
LINE_S = re.compile(r'^\s*(?:\d{1,2}[:.]\d{2}\s+)?(?P<h>.+?)\s{2,}(?P<x>\d+)-(?P<y>\d+)(?:\s*\([^)]*\))?\s{2,}(?P<a>.+?)\s*$')

def clean(n):
    return re.sub(r'\s*\[[^\]]*\]\s*$', '', n).strip()

def parse(path):
    rows = []
    for line in open(path, encoding='utf-8'):
        s = line.rstrip('\n')
        if re.match(r'^\s*[▪»=]', s) and re.search(r'play-?offs?|playoff|relegation|promotion', s, re.I) and not re.search(r'matchday|round', s, re.I):
            break
        if re.search(r'\b(postp|abd|canc|awd)\b', s, re.I) and not re.search(r'\d+-\d+', s): continue
        m = LINE_V.match(s) or LINE_S.match(s)
        if not m: continue
        rows.append((clean(m.group('h')), clean(m.group('a')), int(m.group('x')), int(m.group('y'))))
    return rows
