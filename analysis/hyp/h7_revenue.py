"""H7 league revenue (D306): read 'big five' league revenues from Deloitte's Annual Review of Football Finance (ARFF) PDFs
without any model reading. Chart values are read from the PDF text layer; each value is attributed to its league by
the colour of the value label (2017, 2018, 2026 editions) or of the line it sits on (2016 edition), matched to the
chart's legend. 2010/11 comes from sentences in the 2012 highlights. Projections are dropped.

Source priority (protocol 2.2): the latest edition reporting a season wins; every other reading of the same season is
kept in the output as a cross-check.
Usage: python h7_revenue.py <folder with the ARFF PDFs> <out.csv>"""
import os, re, sys
import pymupdf, pandas as pd

SRC, OUT = sys.argv[1:3]
rows = []

def spans(pg):
    for b in pg.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            for s in l['spans']:
                t = s['text'].strip()
                if t: yield s['bbox'], t, '%06x' % s['color']

def by_label_colour(fname, page, legend, seasons, actual, edition):
    """Chart with coloured value labels; seasons: list of (x of the value column, season label)."""
    pg = pymupdf.open(os.path.join(SRC, fname))[page - 1]
    for bb, t, col in spans(pg):
        if not re.fullmatch(r'\d{1,2},\d{3}|\d{3}', t) or col not in legend: continue
        x = min(seasons, key=lambda s: abs(s[0] - bb[0]))
        if abs(x[0] - bb[0]) > 6: continue
        rows.append(dict(league=legend[col], season=x[1], revenue_eur_m=int(t.replace(',', '')), edition=edition, file=fname,
                         page=page, method='label colour', projection=x[1] not in actual))

def by_line_colour(fname, page, legend, seasons, actual, edition):
    pg = pymupdf.open(os.path.join(SRC, fname))[page - 1]
    pts = []
    for d in pg.get_drawings():
        col = d.get('color')
        if not col: continue
        h = '%02x%02x%02x' % tuple(int(round(c * 255)) for c in col[:3])
        if h not in legend or d['rect'].y0 > 490: continue
        for it in d['items']:
            for p in it[1:]:
                if hasattr(p, 'x'): pts.append((p.x, p.y, legend[h]))
    for bb, t, col in spans(pg):
        if not re.fullmatch(r'\d,\d{3}', t) or not (280 < bb[0] < 530): continue
        x = min(seasons, key=lambda s: abs(s[0] - bb[0]))
        xc = (bb[0] + bb[2]) / 2; cand = [p for p in pts if abs(p[0] - xc) < 12]
        best = min(cand, key=lambda p: abs(p[1] - (bb[3] + 3)))
        rows.append(dict(league=best[2], season=x[1], revenue_eur_m=int(t.replace(',', '')), edition=edition, file=fname, page=page,
                         method=f'line colour (label {best[1] - bb[3]:+.1f}pt from line)', projection=x[1] not in actual))

# ARFF 2026, chart 3 (p. 13): 1996/97 and 2015/16-2026/27; 2025/26 and 2026/27 projected
L26 = {'002df7': 'England', '007680': 'Spain', '29da72': 'Germany', 'df007c': 'Italy', '00a1e0': 'France'}
S26 = [(71.8, '1996/97')] + [(141.8 + 32.6 * i, f'{2015 + i}/{(16 + i) % 100:02d}') for i in range(12)]
by_label_colour('deloitte-annual-review-of-football-finance-2026.pdf', 13, L26, S26, [s for _, s in S26[:-2]], 'ARFF 2026')
# ARFF 2018, chart 3 (p. 12): 2014/15-2018/19; last two projected. Legend swatches: 002269 England, 00a1e0 France,
# 76bd22 Germany, 006938 Italy, c3d600 Spain (same scheme as the 2017 edition, whose swatches were read from the page)
L17 = {'002269': 'England', '00a1e0': 'France', '76bd22': 'Germany', '006938': 'Italy', 'c3d600': 'Spain'}
by_label_colour('gx-deloitte-annual-review-football-finance-2018 (1).pdf', 12, L17,
                [(469.2, '2014/15'), (511.8, '2015/16'), (554.2, '2016/17'), (596.8, '2017/18'), (639.3, '2018/19')], ['2014/15', '2015/16', '2016/17'], 'ARFF 2018')
by_label_colour('gx-deloitte-annual-review-of-football-finance-2017.pdf', 12, L17,
                [(469.2, '2013/14'), (511.8, '2014/15'), (554.3, '2015/16'), (596.7, '2016/17'), (639.3, '2017/18')], ['2013/14', '2014/15', '2015/16'], 'ARFF 2017')
# ARFF 2016, chart 3 (p. 12): values in black; attributed by the coloured line under each label
L16 = {'203263': 'England', '00aae7': 'France', '8ec73f': 'Germany', '4d8f41': 'Italy', 'c3d931': 'Spain'}
by_line_colour('gx-deloitte-uk-annual-review-of-football-finance-2016.pdf', 12, L16,
               [(291.7, '2012/13'), (348.3, '2013/14'), (405.0, '2014/15'), (461.8, '2015/16'), (518.5, '2016/17')], ['2012/13', '2013/14', '2014/15'], 'ARFF 2016')
# ARFF 2012 highlights (text, p. 1): 2010/11
txt = ' '.join(p.get_text() for p in pymupdf.open(os.path.join(SRC, 'uk-sbg-annual-football-finance-review-2012-highlights.pdf'))).replace('\n', ' ')
pat = {'Germany': r'Bundesliga’s revenue grew 5% to €([\d,]+)m', 'Spain': r'La Liga revenues grew by 5% to €([\d,]+)m',
       'Italy': r'Serie A’s revenues increased by 1% to €([\d,]+)m', 'France': r'drop in revenues to €([\d,]+)m'}
val = {k: int(re.search(v, txt).group(1).replace(',', '')) for k, v in pat.items()}
gap = int(re.search(r'narrowed slightly to €(\d+)m', txt).group(1))
val['England'] = val['Germany'] + gap            # "the gap to the second highest ... the Bundesliga, narrowed slightly to €769m"
for k, v in val.items():
    rows.append(dict(league=k, season='2010/11', revenue_eur_m=v, edition='ARFF 2012 highlights', file='uk-sbg-annual-football-finance-review-2012-highlights.pdf',
                     page=1, method='text' if k != 'England' else 'text (Bundesliga + stated gap)', projection=False))

R = pd.DataFrame(rows)
R['edition_year'] = R.edition.str.extract(r'(\d{4})').astype(int)
A = R[~R.projection].sort_values(['league', 'season', 'edition_year'], ascending=[True, True, False])
best = A.drop_duplicates(['league', 'season']).copy()
chk = A.groupby(['league', 'season']).revenue_eur_m.agg(['min', 'max', 'count'])
best = best.merge(chk, left_on=['league', 'season'], right_index=True)
best['readings'] = best['count']; best['max_revision_pct'] = ((best['max'] - best['min']) / best['max'] * 100).round(2)
best[['league', 'season', 'revenue_eur_m', 'edition', 'file', 'page', 'method', 'readings', 'max_revision_pct']].sort_values(['season', 'league']).to_csv(OUT, index=False)
R.to_csv(OUT.replace('.csv', '_all_readings.csv'), index=False)
print(best.groupby('season').size().to_dict()); print('league-seasons:', len(best))
print(best[best.max_revision_pct > 0][['league', 'season', 'revenue_eur_m', 'min', 'max', 'count']].to_string(index=False))
