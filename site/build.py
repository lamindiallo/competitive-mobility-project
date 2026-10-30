"""Competitive Mobility Project — website v2 generator (D286-D294).
Usage: python -I build.py <data_in dir> <out dir> <version> <date>"""
import sys, os, re, json, html, shutil, unicodedata
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from model import LEAGUES, ORDER, GOALS, BAND_GOALS, band_label, load, ceilings, START, END10, END5, the

IN, OUT, VERSION, DATE = sys.argv[1:5]
E = html.escape
L, NOCH = load(IN)
C = ceilings(L)
CEIL = {(r.country, r.tier, r.band, r.goal): r for r in C.itertuples()}
LAST = {c: int(L[c].Season.max()) for c in L}
NEXT = pd.read_csv(os.path.join(IN, 'tiers_2026_27.csv'))
NEXTT = {(r.country, r.k): r.tier_2026 for r in NEXT.itertuples()}
TCS = pd.read_csv(os.path.join(IN, 'tierC_seasons.csv'))
TC = {'ENG': pd.read_csv(os.path.join(IN, 'england_tierC_prototype.csv')).set_index('k'),
      'FRA': pd.read_csv(os.path.join(IN, 'france_tierC_prototype.csv')).set_index('k')}
FEEDN = pd.read_csv(os.path.join(IN, 'feed_names.csv'))
AUTHOR = 'Lamin Diallo'
# Money-aware ceilings (D301), England and France: precomputed by analysis/clubvalues/money_ceiling.py
MC = pd.read_csv(os.path.join(IN, 'money_ceilings.csv')) if os.path.exists(os.path.join(IN, 'money_ceilings.csv')) else pd.DataFrame()
MCM = pd.read_csv(os.path.join(IN, 'money_ceiling_models.csv')).set_index(['country', 'goal']) if os.path.exists(os.path.join(IN, 'money_ceiling_models.csv')) else pd.DataFrame()
MGOAL = {'top4_5': 'reached the top four within five seasons', 'stay5': 'stayed in the top flight for all of the next five seasons',
         'tf5': 'were in the top flight within five seasons'}
# Gross mobility G (registered result, D167/D213): expected time to reach the top four relative to a league without memory
# or club differences, measured on the whole ladder (England four divisions, elsewhere two)
G = {'ENG': 4.00, 'ESP': 3.44, 'ITA': 3.28, 'GER': 2.56, 'FRA': 2.38}
# How much of a big over-performance against the money survives into the next season
PERS = {}
for _c in ('ENG', 'FRA'):
    _g = TCS[TCS.country == _c].sort_values('season').copy(); _g['nxt'] = _g.groupby('k').places.shift(-1); _g['ns'] = _g.groupby('k').season.shift(-1)
    _g = _g[(_g.ns == _g.season + 1) & (_g.places >= 4)]; PERS[_c] = (_g.places.mean(), _g.nxt.mean(), len(_g))

# ------------------------------------------------------------------ helpers
def season(s): return f'{s}/{(s + 1) % 100:02d}'
def slug(c, k):
    k = unicodedata.normalize('NFKD', k).encode('ascii', 'ignore').decode().lower()
    return f"{c.lower()}-{re.sub(r'[^a-z0-9]+', '-', k).strip('-')}"
def ordinal(n):
    n = int(n); return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"
def times(n): return {0: 'never', 1: 'once', 2: 'twice'}.get(n, f'{n} times')
def plural(n, w, p=None): return f'{n} {w if n == 1 else (p or w + "s")}'
def tiername(c, t): return LEAGUES[c]['tiers'][t]
def phrase(share, n, hits):
    if n < 30: return f'{hits} of {n}'
    if hits == 0: return f'none of {n}'
    if share >= 0.95: return 'almost all'
    if share >= 0.25: return f'about {round(share * 10)} in 10'
    if share < 1 / 30: return f'{hits} of {n}'
    return f'about 1 in {round(1 / share)}'
def icons(share, cls='icons', k=10):
    on = int(round(share * k)) if share == share else 0
    if share > 0 and on == 0 and cls == 'icons': on = 0
    return f'<span class="{cls}" role="img" aria-label="{on} out of {k}">' + ''.join(f'<span class="{"on" if i < on else ""}"></span>' for i in range(k)) + '</span>'
def rng(r): return f'{r.hits} of {r.n} ({r.share:.0%}); likely range {r.lo:.0%}–{r.hi:.0%}, {r.clubs} different clubs'
def how(summary, body): return f'<details class="how"><summary>{E(summary)}</summary><div>{body}</div></details>'

# display names: the 2025/26 official name where the club played in 2025/26
DISPLAY = {}
lines = [l.strip().split('|') for l in open(os.path.join(IN, 'final_tables_2025_26.txt'), encoding='utf-8') if l.strip() and not l.startswith('#')]
for c, t, cl in lines:
    d = L[c]; r = d[(d.Season == 2025) & (d.tier == int(t))].sort_values('pos')
    for k, nm in zip(r.k, cl.split(';')): DISPLAY[(c, k)] = nm
OVERRIDE = {('ENG', 'wimbledon'): 'Wimbledon FC (to 2003/04)', ('GER', '1860 munchen'): '1860 München', ('ESP', 'athletic club b'): 'Athletic Bilbao B',
            ('ESP', 'real burgos'): 'Real Burgos (to 1993/94)', ('ITA', 'inter'): 'Inter Milan'}
def display_name(c, k, g):
    if (c, k) in OVERRIDE: return OVERRIDE[(c, k)]
    if (c, k) in DISPLAY: return DISPLAY[(c, k)]
    return g.sort_values('Season').club.iloc[-1]

# ------------------------------------------------------------------ records
def record(c, k, g):
    g = g.sort_values('Season'); S = g.set_index('Season'); seasons = list(S.index); last = LAST[c]
    R = dict(by_tier={int(t): int((g.tier == t).sum()) for t in sorted(LEAGUES[c]['tiers'])})
    t1 = g[g.tier == 1]
    R['titles'] = [int(s) for s in t1[t1.champ].Season]; R['top4'] = int((t1.pos <= 4).sum())
    R['revoked'] = [int(r.Season) for r in t1.itertuples() if r.pos == 1 and (c, r.Season) in NOCH]
    promo = rele = 0; R['next'] = None
    for s in seasons:
        nt, tr = S.at[s, 'next_tier'], S.at[s, 'tier']
        if s == last:
            known = (c, k) in NEXTT or tr == 1 or (c == 'ENG' and tr <= 2)
            if not known: continue
            R['next'] = int(nt)
        promo += nt < tr; rele += nt > tr
        if s > LEAGUES[c]['start'] and s - 1 not in S.index: promo += 1   # came up from below the divisions covered
    R['promotions'], R['relegations'] = int(promo), int(rele)
    pk = g.loc[g['rank'].idxmin()]; R['peak'] = (int(pk.Season), int(pk.tier), int(pk.pos))
    best = None
    for s in seasons:
        if s + 5 in S.index:
            gain = S.at[s, 'rank'] - S.at[s + 5, 'rank']
            if best is None or gain > best[0]: best = (int(gain), int(s))
    R['climb'] = best
    R['series'] = [(int(r.Season), int(r.tier), int(r.pos), int(r['rank'])) for _, r in g.iterrows()]
    R['last'] = (int(S.at[last, 'tier']), int(S.at[last, 'pos']), S.at[last, 'band']) if last in S.index else None
    w = [s for s in seasons if s > last - 10]
    R['ten'] = dict(top=int(sum(S.at[s, 'tier'] == 1 for s in w)), top4=int(sum(S.at[s, 'tier'] == 1 and S.at[s, 'pos'] <= 4 for s in w)),
                    top6=int(sum(S.at[s, 'tier'] == 1 and S.at[s, 'pos'] <= 6 for s in w)), titles=int(sum(bool(S.at[s, 'champ']) for s in w)),
                    seasons=10)
    return R

clubs = []
for c in ORDER:
    for k, g in L[c].groupby('k'):
        clubs.append(dict(c=c, k=k, name=display_name(c, k, g), slug=slug(c, k), R=record(c, k, g)))
BYKEY = {(x['c'], x['k']): x for x in clubs}

# ------------------------------------------------------------------ similar clubs (trajectory over the last 15 seasons)
YRS = list(range(2011, 2026)); WT = np.linspace(0.5, 1.5, len(YRS))
def level(c, k, cap):
    S = {s: (t, p) for s, t, p, _ in BYKEY[(c, k)]['R']['series']}; v = []
    for s in YRS:
        if s in S:
            t, p = S[s]; n = int(L[c][(L[c].Season == s) & (L[c].tier == t)].shape[0]); x = (t - 1) + (p - 1) / max(1, n - 1)
        else: x = 4.0
        v.append(min(x, cap))
    return np.array(v)
LV = {(x['c'], x['k']): (level(x['c'], x['k'], 4.0), level(x['c'], x['k'], 2.2)) for x in clubs}
def similar(cl):
    me = (cl['c'], cl['k']); a_full, a_cap = LV[me]
    if (a_full >= 4).sum() > 8: return [], []
    same, other = [], []
    for x in clubs:
        key = (x['c'], x['k'])
        if key == me: continue
        b_full, b_cap = LV[key]
        if x['c'] == cl['c']: same.append((float(np.average(abs(a_full - b_full), weights=WT)), x))
        elif (a_cap < 2).sum() >= 5 and (b_cap < 2).sum() >= 5: other.append((float(np.average(abs(a_cap - b_cap), weights=WT)), x))
    same.sort(key=lambda z: z[0]); other.sort(key=lambda z: z[0])
    return [x for _, x in same[:4]], [x for _, x in other[:3]]

# ------------------------------------------------------------------ charts
def tip(s): return E(s, quote=True)
def trajectory(c, series, series2=None, start=None):
    W, H, l, r, t, b = 760, 300, 40, 16, 14, 30
    lo, hi = start or LEAGUES[c]['start'], LAST[c]
    sizes = L[c][L[c].Season == hi].groupby('tier').size(); maxr = int(sizes.sum())
    x = lambda s: l + (s - lo) / max(1, hi - lo) * (W - l - r)
    y = lambda k: t + (k - 0.5) / maxr * (H - t - b)
    P = [f'<svg viewBox="0 0 {W} {H}" class="chart wide" role="img" aria-label="Finishing position each season">']
    acc = 0
    for i, (tier, n) in enumerate(sizes.items()):
        if i % 2 == 0: P.append(f'<rect class="tierband" x="{l}" y="{y(acc + .5):.1f}" width="{W - l - r}" height="{y(acc + n + .5) - y(acc + .5):.1f}"/>')
        P.append(f'<text class="tierlab" x="{l + 6}" y="{y(acc + .5) + 14:.1f}">{E(tiername(c, tier))}</text>'); acc += n
    step = 4 if hi - lo > 20 else 2
    for i, s in enumerate(range(hi, lo - 1, -step)):
        P.append(f'<text class="ax{" alt" if i % 2 else ""}" x="{x(s):.1f}" y="{H - 8}" text-anchor="middle">{season(s)}</text>')
    P.append(f'<text class="ax" x="{l - 8}" y="{y(1) + 4:.1f}" text-anchor="end">1st</text>')
    for ser, cls in ((series2, '2'), (series, '1')):
        if not ser: continue
        seg, prev = [], None
        for s, tier, pos, rk in ser:
            if s < lo: continue
            if prev is not None and s != prev + 1:
                if len(seg) > 1: P.append(f'<polyline class="s{cls}" points="{" ".join(seg)}"/>')
                seg = []
            seg.append(f'{x(s):.1f},{y(rk):.1f}'); prev = s
        if len(seg) > 1: P.append(f'<polyline class="s{cls}" points="{" ".join(seg)}"/>')
        for s, tier, pos, rk in ser:
            if s < lo: continue
            ti = tier == 1 and pos == 1 and (c, s) not in NOCH
            P.append(f'<circle class="d{cls}{" title" if ti else ""}" cx="{x(s):.1f}" cy="{y(rk):.1f}" r="{6 if ti else 4}"/>')
            P.append(f'<circle class="hit" cx="{x(s):.1f}" cy="{y(rk):.1f}" r="11" data-tip="{tip(f"{season(s)}: {ordinal(pos)} in {the(c, tier)}" + (" — champions" if ti else ""))}"/>')
    P.append('</svg>'); return ''.join(P)

def bars(items, fmt, W=330, unit='', l=92, r=56):
    """Horizontal bars: items = [(label, value, highlight, tooltip)]"""
    rowh = 30; H = rowh * len(items) + 6; mx = max(v for _, v, _, _ in items) or 1
    P = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img">']
    for i, (lab, v, on, tp) in enumerate(items):
        y0 = 4 + i * rowh; w = (W - l - r) * v / mx
        P.append(f'<text class="lab" x="{l - 8}" y="{y0 + 17}" text-anchor="end">{E(lab)}</text>')
        P.append(f'<rect class="bar{" on" if on else ""}" x="{l}" y="{y0 + 5}" width="{max(w, 2):.1f}" height="16" rx="4"/>')
        P.append(f'<text class="val" x="{l + w + 6:.1f}" y="{y0 + 18}">{E(fmt(v))}</text>')
        P.append(f'<rect class="hit" x="0" y="{y0}" width="{W}" height="{rowh}" data-tip="{tip(tp)}"/>')
    P.append('</svg>'); return ''.join(P)

def money_chart(rows, c):
    W, H, l, r, t, b = 760, 280, 40, 16, 14, 30
    lo, hi = int(rows.season.min()), int(rows.season.max()); N = int(rows.N.max())
    x = lambda s: l + (s - lo) / max(1, hi - lo) * (W - l - r) if hi > lo else (l + W - r) / 2
    y = lambda k: t + (k - 0.5) / N * (H - t - b)
    n1 = int(L[c][(L[c].Season == hi) & (L[c].tier == 1)].shape[0])
    P = [f'<svg viewBox="0 0 {W} {H}" class="chart wide" role="img" aria-label="Actual finish against the finish the wage bill normally buys">',
         f'<rect class="tierband" x="{l}" y="{y(.5):.1f}" width="{W - l - r}" height="{y(n1 + .5) - y(.5):.1f}"/>',
         f'<text class="tierlab" x="{l + 6}" y="{y(.5) + 14:.1f}">{E(tiername(c, 1))}</text><text class="tierlab" x="{l + 6}" y="{y(n1 + .5) + 14:.1f}">{E(tiername(c, 2))}</text>',
         f'<text class="ax" x="{l - 8}" y="{y(1) + 4:.1f}" text-anchor="end">1st</text>']
    for i, s in enumerate(range(hi, lo - 1, -2)): P.append(f'<text class="ax{" alt" if i % 2 else ""}" x="{x(s):.1f}" y="{H - 8}" text-anchor="middle">{season(s)}</text>')
    rows = rows.sort_values('season')
    for col, cls in (('exp_lrank', 'sx'), ('lrank', 's1')):
        seg, prev = [], None
        for rr in rows.itertuples():
            if prev is not None and rr.season != prev + 1:
                if len(seg) > 1: P.append(f'<polyline class="{cls}" points="{" ".join(seg)}"/>')
                seg = []
            seg.append(f'{x(rr.season):.1f},{y(getattr(rr, col)):.1f}'); prev = rr.season
        if len(seg) > 1: P.append(f'<polyline class="{cls}" points="{" ".join(seg)}"/>')
    for rr in rows.itertuples():
        P.append(f'<circle class="dx" cx="{x(rr.season):.1f}" cy="{y(rr.exp_lrank):.1f}" r="3.5"/><circle class="d1" cx="{x(rr.season):.1f}" cy="{y(rr.lrank):.1f}" r="4.5"/>')
        tp = f'{season(rr.season)}: finished {ordinal(rr.pos)} in {the(c, rr.tier)}; the wage bill normally buys about {ordinal(max(1, round(rr.exp_lrank)) if rr.exp_lrank <= n1 else max(1, round(rr.exp_lrank - n1)))} in {the(c, 1 if rr.exp_lrank <= n1 else 2)}'
        P.append(f'<rect class="hit" x="{x(rr.season) - 12:.1f}" y="{t}" width="24" height="{H - t - b}" data-tip="{tip(tp)}"/>')
    P.append('</svg>'); return ''.join(P)

def lines_chart(series, xlabels, highlight, fmt):
    """series = {name: [values]}; highlighted series in accent, others in context grey, all direct-labelled."""
    W, H, l, r, t, b = 520, 280, 40, 92, 12, 28
    vals = [v for s in series.values() for v in s if v == v]; mx = max(vals) * 1.1
    x = lambda i: l + i / (len(xlabels) - 1) * (W - l - r); y = lambda v: t + (1 - v / mx) * (H - t - b)
    P = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img">']
    for g in (0, .1, .2, .3, .4):
        if g <= mx: P.append(f'<line class="grid" x1="{l}" x2="{W - r}" y1="{y(g):.1f}" y2="{y(g):.1f}"/><text class="ax" x="{l - 6}" y="{y(g) + 4:.1f}" text-anchor="end">{g:.0%}</text>')
    for i, lab in enumerate(xlabels): P.append(f'<text class="ax{" alt" if i % 2 else ""}" x="{x(i):.1f}" y="{H - 8}" text-anchor="middle">{E(lab)}</text>')
    ends = []
    for name, v in sorted(series.items(), key=lambda z: z[0] == highlight):
        on = name == highlight
        P.append(f'<polyline class="{"s1" if on else "ctxl"}" points="{" ".join(f"{x(i):.1f},{y(a):.1f}" for i, a in enumerate(v))}"/>')
        for i, a in enumerate(v):
            P.append(f'<circle class="{"d1" if on else "dx"}" cx="{x(i):.1f}" cy="{y(a):.1f}" r="{4.5 if on else 3}"/><circle class="hit" cx="{x(i):.1f}" cy="{y(a):.1f}" r="10" data-tip="{tip(f"{name}, {xlabels[i]}: {fmt(a)}")}"/>')
        ends.append([y(v[-1]), name, on])
    ends.sort();
    for i in range(1, len(ends)):
        if ends[i][0] - ends[i - 1][0] < 15: ends[i][0] = ends[i - 1][0] + 15
    for yy, name, on in ends: P.append(f'<text class="{"lab" if on else "ax"}" x="{W - r + 8}" y="{yy + 4:.1f}">{E(name)}</text>')
    P.append('</svg>'); return ''.join(P)

# ------------------------------------------------------------------ layout
NAV = (('index.html', 'Clubs'), ('leagues.html', 'Leagues'), ('live.html', 'This season'), ('compare.html', 'Compare'), ('about.html', 'How it works'))
TIPJS = ('<div id="tip" role="tooltip"></div><script>(()=>{const t=document.getElementById("tip");'
         'function show(e){const m=e.target.closest("[data-tip]");if(!m){t.style.display="none";return}t.textContent=m.dataset.tip;t.style.display="block";'
         'const r=m.getBoundingClientRect(),x=(e.clientX||r.left+r.width/2),y=(e.clientY||r.top);t.style.left=Math.min(innerWidth-t.offsetWidth-8,x+12)+"px";t.style.top=Math.max(8,y-t.offsetHeight-12)+"px"}'
         'document.addEventListener("mousemove",show);document.addEventListener("focusin",show);document.addEventListener("touchstart",e=>show(e.touches[0]?{target:e.target,clientX:e.touches[0].clientX,clientY:e.touches[0].clientY}:e),{passive:true});'
         'document.querySelectorAll("svg [data-tip]").forEach(n=>n.setAttribute("tabindex","0"));})();</script>')
def page(title, body, rel, desc, here=''):
    nav = ''.join(f'<a href="{rel}{h}"{" aria-current=page" if h == here else ""}>{t}</a>' for h, t in NAV)
    return f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} · Competitive Mobility Project</title><meta name="description" content="{E(desc)}"><link rel="stylesheet" href="{rel}style.css"></head>
<body><header class="top"><div class="wrap"><a class="brand" href="{rel}index.html"><i></i>Competitive Mobility Project</a><nav>{nav}</nav></div></header>
<main class="wrap">{body}</main>
<footer class="wrap foot"><p>Competitive Mobility Project by {AUTHOR} · version {E(VERSION)}, {E(DATE)} · Final tables to {season(2025)}; this season's table is provisional.
Figures come from match results and from clubs' published accounts. No one's individual pay is shown. No club badges are used: they belong to the clubs.
<a href="{rel}data.html">Data and code</a> · <a href="{rel}corrections.html">Report an error</a></p></footer>{TIPJS}</body></html>'''
def write(path, s):
    p = os.path.join(OUT, path); os.makedirs(os.path.dirname(p) or OUT, exist_ok=True); open(p, 'w', encoding='utf-8').write(s)

# ------------------------------------------------------------------ the realistic ceiling
def ceiling_parts(c, tier, b):
    out = []
    for g in (BAND_GOALS[b] if not (b == 'rel' and tier > 1) else ['backup5', 'tf10']):
        if tier >= 3 and g == 'top6_10': continue
        r = CEIL.get((c, tier, b, g))
        if r is not None and r.n: out.append((g, r))
    return out
HOWCEIL = (f'<p>We took every season since {season(START)} in which a club finished in the same part of the same league, and followed each club forward. '
           'The figure is the share that reached each goal. Ten-year goals use finishes from {a} to {b}, five-year goals from {a} to {c}, so every case has had the full time to play out; '
           'results run to the end of {d}.</p><p>It describes what happened to clubs in this position, not a forecast for one club. '
           'A club with much more money or history than is usual for its position has better chances than the figure suggests, which is why the club\'s own record is shown underneath.</p>'
           '<p>The likely range is a 95% interval worked out by resampling clubs rather than seasons, because the same club often appears several times. It is wide where only a few clubs have been in a position, and two leagues whose ranges overlap may not really differ. '
           'Reserve teams such as Barcelona B or Real Madrid Castilla are left out of these counts, because they cannot be promoted into their first team\'s division.</p>'
           ).format(a=season(START), b=season(END10), c=season(END5), d=season(2025))
def ceiling_block(cl, tier, pos, b, when, live=False):
    c, R, nm = cl['c'], cl['R'], cl['name']; parts = ceiling_parts(c, tier, b)
    if not parts: return ''
    g0, r0 = parts[0]
    head = phrase(r0.share, r0.n, r0.hits)
    rows = ''.join(f'<tr><td>{E(GOALS[g][0][0].upper() + GOALS[g][0][1:])}</td><td class="v">{E(phrase(r.share, r.n, r.hits))}{icons(r.share, "mini")}<br><span class="note">{r.hits} of {r.n}; range {r.lo:.0%}–{r.hi:.0%}</span></td></tr>' for g, r in parts[1:])
    lead = (f'<p class="q">{"<span class=live>Provisional</span> " if live else ""}{E(when)}</p>')
    big = f'<p class="headline">{E(head[0].upper() + head[1:])}</p>' if r0.n >= 30 else f'<p class="headline">{E(head)}</p>'
    sent = (f'<p>Of the {r0.n} times a club {E(band_label(c, tier, b))} between {season(r0.first)} and {season(r0.last)}, '
            f'{r0.hits} {GOALS[g0][0]}.</p><p class="note">{E(rng(r0))}.</p>')
    own = own_line(cl, g0, r0) + money_ceiling(cl)
    return (f'<div class="ceiling">{lead}{big}{icons(r0.share)}{sent}'
            + (f'<table class="goals">{rows}</table>' if rows else '') + own
            + how('How do we know?', HOWCEIL + f'<p>Counts: {"; ".join(f"{GOALS[g][0]}: {r.hits} of {r.n}" for g, r in parts)}.</p>') + '</div>')

def pphrase(p):
    if p >= 0.95: return 'almost all'
    if p >= 0.25: return f'about {round(p * 10)} in 10'
    if p < 0.02: return 'fewer than 1 in 50'
    return f'about 1 in {round(1 / p)}'
def money_ceiling(cl):
    c, k, nm = cl['c'], cl['k'], cl['name']
    if MC.empty: return ''
    m = MC[(MC.country == c) & (MC.k == k)]
    if m.empty: return ''
    r0 = m.iloc[0]
    rows = ''
    for r in m.itertuples():
        mm = MCM.loc[(c, r.goal)]
        helps = mm.logloss_with_wages < mm.logloss_position_only
        rows += (f'<tr><td>{E(MGOAL[r.goal][0].upper() + MGOAL[r.goal][1:])}'
                 + ('' if helps else '<br><span class="note">In this league the wage bill adds little here: the figure is close to the one for position alone.</span>')
                 + f'</td><td class="v">{E(pphrase(r.p))}<br><span class="note">range {r.lo:.0%}–{r.hi:.0%}</span></td></tr>')
    return (f'<h3 style="margin-top:18px">Taking its wage bill into account</h3>'
            f'<p class="small">Of clubs in a similar position with a wage bill like {E(nm)}\'s — the {ordinal(r0.wage_rank)} highest of {int(r0.wage_n)} in the top two divisions in {season(int(r0.wage_season))}, '
            f'{r0.relative_wage:.1f} times the average — this share went on to:</p><table class="goals">{rows}</table>'
            + how('How is this worked out?', '<p>A model fitted on every club-season with a published wage bill (England from 2011/12, France from 2008/09) relates each goal to two things: where the club finished and how its wage bill compared with the season\'s average. Five-year goals are used because the wage records are too recent for ten-year ones. '
                  'We checked the model on clubs it had not seen: adding the wage bill makes the figures more accurate for most goals, and where it does not, the page says so. The range comes from refitting the model on clubs drawn at random with replacement. '
                  'Like every figure here, it describes clubs like this one, not a forecast for this club; wage bills include all staff, not only players. This model was added after the registered tests and is descriptive, not one of them.</p>'))

def own_line(cl, g0, r0):
    c, R, nm = cl['c'], cl['R'], cl['name']; T = R['ten']; n = T['seasons']
    if not R['ten']['top'] and not [s for s, *_ in R['series'] if s > LAST[c] - 10]: return ''
    bits = []
    if T['top']: bits.append(f'{T["top"]} of the last {n} seasons in {the(c, 1)}')
    else: bits.append(f'none of the last {n} seasons in {the(c, 1)}')
    if T['top4']: bits.append(f'{plural(T["top4"], "top-four finish", "top-four finishes")}')
    if T['titles']: bits.append(f'{plural(T["titles"], "title")}')
    line = f'<p class="own"><strong>{E(nm)} itself:</strong> {"; ".join(bits)}.</p>'
    # the "much bigger than its position" note (D288)
    note = ''
    own_rate = {'top4_10': T['top4'] / n, 'title10': T['titles'] / n, 'top6_10': T['top6'] / n}.get(g0)
    if g0 in ('top4_10', 'top6_10') and own_rate is not None and own_rate >= 0.3 and own_rate > 2 * r0.share:
        note = f'{E(nm)} has done this far more often than most clubs in this position, so the figure above understates its own chances.'
    if g0 in ('stay5', 'back5', 'up5') and T['top4'] >= 3:
        note = f'{E(nm)} is much bigger than most clubs in this position: it finished in the top four {times(T["top4"])} in the last {n} seasons. The figure above describes typical clubs in this position and understates its chances.'
    tc = TCS[(TCS.country == c) & (TCS.k == cl['k'])].sort_values('season')
    if note and len(tc):
        r = tc.iloc[-1]; note += f' Its wage bill in {season(int(r.season))} was the {ordinal(r.wage_rank)} highest of {int(r.wage_n)} clubs with published accounts in the top two divisions.'
    return line + (f'<p class="flag">{note}</p>' if note else '')

# ------------------------------------------------------------------ against the money
def money_amount(c, v): return (f'£{v / 1000:.0f}m' if v >= 9500 else f'£{v / 1000:.1f}m') if c == 'ENG' else (f'€{v / 1000:.0f}m' if v >= 9500 else f'€{v / 1000:.1f}m')
HOWMONEY = {'ENG': 'Wage bills are the staff costs in each club\'s statutory accounts at Companies House (all staff, not only players), read without any language model and checked against the note\'s own components and the next year\'s accounts. Seasons where two readings disagree by more than 2% are left out.',
            'FRA': 'Wage bills are total payroll including social charges from the DNCG\'s published club accounts, checked against each report\'s own cost totals. Group (consolidated) accounts are left out.'}
def money_block(cl):
    c, k, nm = cl['c'], cl['k'], cl['name']
    if c not in TC:
        return (f'<p class="muted">Not available for {E(LEAGUES[c]["country"])}: wage bills are not published club by club in one place there, so this is shown for England and France only.</p>')
    rows = TCS[(TCS.country == c) & (TCS.k == k)].sort_values('season')
    if len(rows) < 3:
        return f'<p class="muted">Not enough seasons with published wage figures in the top two divisions ({len(rows)}).</p>'
    T = TC[c]; out = ''
    if k in T.index:
        r = T.loc[k]; v = r.places_above_expected
        if r.published_as != 'within the normal range':
            verdict = f'Finished {abs(v):.0f} place{"s" if round(abs(v)) != 1 else ""} {"above" if v > 0 else "below"} its money'
            expl = (f'Over {int(r.seasons)} seasons, {E(nm)} finished on average {abs(v):.1f} places {"higher" if v > 0 else "lower"} than clubs with the same wage bill usually finish. '
                    'The gap is too large to be put down to chance.')
        else:
            verdict = 'About where its money would put it'
            expl = (f'Over {int(r.seasons)} seasons, the average gap was {v:+.1f} places, which is within what chance alone would produce.')
        above = int((rows.places > 0).sum())
        expl += f' It finished above its money in {above} of {len(rows)} seasons with published figures.'
        out += f'<p class="headline">{E(verdict)}</p><p>{expl}</p>'
        if c == 'ENG' and int(r.parachute_seasons) > 0: out += f'<p class="note">{plural(int(r.parachute_seasons), "season")} followed relegation and came with parachute payments; they are included.</p>'
        if c == 'ENG' and bool(r.group_accounts): out += '<p class="note">Wage bill from the group accounts of the club\'s parent company (NSWE Sports Ltd), where football is the whole business.</p>'
    else:
        out += f'<p><strong>No overall verdict:</strong> {len(rows)} seasons with published wage figures, fewer than the eight needed.</p>'
    last = rows.iloc[-1]
    out += (f'<div class="tiles t3"><div class="tile"><b>{money_amount(c, last.pay)}</b><span>wage bill, {season(int(last.season))}</span></div>'
            f'<div class="tile"><b>{ordinal(last.wage_rank)}</b><span>highest of {int(last.wage_n)} clubs with published accounts</span></div>'
            f'<div class="tile"><b>{ordinal(last.pos)}</b><span>finish in {E(the(c, int(last.tier)))}, {season(int(last.season))}</span></div></div>')
    out += (f'<div class="chartbox"><div class="legend"><span style="--c:var(--acc)">Where {E(nm)} finished</span><span style="--c:var(--ctx)">Where its wage bill normally finishes</span></div>'
            f'{money_chart(rows, c)}</div>')
    trs = ''.join(f'<tr><td>{season(int(x.season))}</td><td>{ordinal(x.pos)}, {E(tiername(c, int(x.tier)))}</td><td class="n">{money_amount(c, x.pay)}</td><td class="n">{ordinal(x.wage_rank)} of {int(x.wage_n)}</td><td class="n">{x.places:+.1f}</td></tr>' for x in rows.iloc[::-1].itertuples())
    out += how('Season by season', f'<div class="scroll"><table class="t"><tr><th>Season</th><th>Finish</th><th class="n">Wage bill</th><th class="n">Wage rank</th><th class="n">Places above its money</th></tr>{trs}</table></div>')
    out += how('How do we know?', f'<p>For every season, we compare each club\'s wage bill with the average in the top two divisions, and work out the finish that wage bill usually brings, '
               'allowing for differences between seasons and assuming a bigger wage bill never lowers the expected finish. The gap between that and the actual finish, averaged over the seasons, is the figure above. '
               'An overall verdict needs at least eight seasons, and a signed number is given only when the gap is clearly larger than chance.</p>'
               f'<p>{HOWMONEY[c]}</p><p>On average, most of a big over-performance fades: clubs that finished at least four places above their money (on average {PERS[c][0]:.1f} places) were {PERS[c][1]:+.1f} places the next season, so about {1 - PERS[c][1] / PERS[c][0]:.0%} of it disappeared and the rest persisted. Some clubs beat their money season after season. It mixes good management, luck and resources the measure cannot see, so it is not a score for how well a club is run.</p>')
    return out

# ------------------------------------------------------------------ the story (D290)
def story(cl):
    c, R, nm = cl['c'], cl['R'], cl['name']; ser = R['series']; T = LEAGUES[c]['tiers']
    first = ser[0][0]; n = len(ser); last = LAST[c]
    by = [f'{R["by_tier"][t]} in {the(c, t)}' for t in sorted(R['by_tier']) if R['by_tier'][t]]
    s1 = f'{E(nm)} has played {plural(n, "season")} in the divisions covered here since {season(max(first, LEAGUES[c]["start"]))}: {", ".join(by[:-1]) + (" and " if len(by) > 1 else "") + by[-1]}.'
    # eras: runs in the same division
    runs, cur = [], None
    for s, t, p, rk in ser:
        if cur and cur[0] == t and cur[2] == s - 1: cur[2] = s
        else:
            if cur: runs.append(cur)
            cur = [t, s, s]
    runs.append(cur)
    t, a, b = runs[-1]
    if b == last:
        s2 = f'It has been in {the(c, t)} since {season(a)} ({plural(b - a + 1, "season")})'
        if len(runs) > 1:
            pt, pa, pb = runs[-2]
            if pb == a - 1: s2 += f', after {plural(pb - pa + 1, "season")} in {the(c, pt)}.'
            else: s2 = f'It returned to {the(c, t)} in {season(a)} after {plural(a - pb - 1, "season")} outside the divisions covered' + (f', and has been there for {plural(b - a + 1, "season")}.' if b > a else '.')
        else: s2 += '.'
    else:
        s2 = f'Its last season in the divisions covered was {season(b)}, in {the(c, t)}.'
    s3 = ''
    if R['titles']:
        yrs = [season(s) for s in R['titles']]
        s3 = f'It won {the(c, 1)} {times(len(yrs))}' + (f' ({", ".join(yrs[:-1]) + " and " + yrs[-1] if len(yrs) > 1 else yrs[0]})' if len(yrs) <= 6 else f', most recently in {yrs[-1]}') + '.'
    else:
        ps, pt, pp = R['peak']; s3 = f'Its best finish was {ordinal(pp)} in {the(c, pt)}, in {season(ps)}.'
    s4 = ''
    if R['climb'] and R['climb'][0] >= 15:
        g, s = R['climb']; S = {x[0]: x for x in ser}
        a_, b_ = S[s], S[s + 5]
        s4 = (f'Its biggest climb took five seasons: from {ordinal(a_[2])} in {the(c, a_[1])} in {season(s)} to {ordinal(b_[2])} in {the(c, b_[1])} in {season(s + 5)}.')
    if R['next'] and R['last'] and R['next'] != R['last'][0] and R['next'] <= max(T):
        s2 += f' It {"goes up to" if R["next"] < R["last"][0] else "drops to"} {the(c, R["next"])} for {season(last + 1)}.'
    pr, rl = R['promotions'], R['relegations']
    s5 = ('' if not (pr or rl) else f'It has been promoted {times(pr)} and relegated {times(rl)}.' if pr and rl else
          f'It has been promoted {times(pr)} and never relegated.' if pr else f'It has never been promoted, and has been relegated {times(rl)}.')
    return ' '.join(x for x in (s1, s2, s3, s4, s5) if x)

# ------------------------------------------------------------------ club pages
NAMES = {(x['c'], x['k']): x['name'] for x in clubs}
def status_line(cl):
    c, R = cl['c'], cl['R']; bits = []
    if R['last']:
        t, p, b = R['last']; bits.append(f'{season(LAST[c])}: {ordinal(p)} in {E(the(c, t))}' + {'prom': ', promoted', 'rel': ', relegated', '1': ', champions'}.get(b, ''))
        if R['next'] and R['next'] <= max(LEAGUES[c]['tiers']): bits.append(f'{season(LAST[c] + 1)}: {E(tiername(c, R["next"]))}')
    else:
        bits.append(f'last in the divisions covered in {season(R["series"][-1][0])}')
    return ' · '.join(bits)

for cl in clubs:
    c, R, nm = cl['c'], cl['R'], cl['name']; m = LEAGUES[c]
    if c == 'ESP' and L[c][L[c].k == cl['k']].reserve.any():
        ceil_sec = (f'<h2>How high can {E(nm)} realistically go?</h2><p class="muted">{E(nm)} is a reserve team. Reserve teams cannot be promoted into the division of their '
                    'first team, so no realistic ceiling is given, and reserve teams are left out of the figures for all other clubs.</p>')
    elif R['last']:
        t, p, b = R['last']
        ceil = ceiling_block(cl, t, p, b, f'Based on finishing {ordinal(p)} in {the(c, t)} in {season(LAST[c])}' + {'prom': ' and going up', 'rel': ' and going down'}.get(b, ''))
        ceil_sec = f'<h2>How high can {E(nm)} realistically go?</h2>{ceil}<div id="livebox" data-c="{c}" data-k="{E(cl["k"], quote=True)}"></div>'
    else:
        ceil_sec = (f'<h2>How high can {E(nm)} realistically go?</h2><p class="muted">{E(nm)} was not in the divisions covered in {season(LAST[c])}, '
                    'so there is no current position to start from.</p>')
    tiles = [(len(R['series']), f'seasons since {season(m["start"])}'), (R['by_tier'].get(1, 0), f'seasons in {the(c, 1)}'),
             (len(R['titles']), 'league titles'), (R['top4'], 'top-four finishes'), (R['promotions'], 'promotions'), (R['relegations'], 'relegations')]
    tiles_html = '<div class="tiles">' + ''.join(f'<div class="tile"><b>{v}</b><span>{E(lbl)}</span></div>' for v, lbl in tiles) + '</div>'
    same, other = similar(cl)
    sim = ''
    if same or other:
        card = lambda x: (f'<a href="{x["slug"]}.html">{E(x["name"])}<span>{E(LEAGUES[x["c"]]["country"])} · '
                          + (f'{ordinal(x["R"]["last"][1])} in {E(the(x["c"], x["R"]["last"][0]))}, {season(LAST[x["c"]])}' if x['R']['last'] else 'not in the divisions covered now') + '</span></a>')
        sim = (f'<h2>Clubs with a similar path</h2><p>Clubs whose finishing positions over the last 15 seasons were closest to {E(nm)}\'s, with recent seasons counting more.</p>'
               + (f'<h3>In {E(m["country"])}</h3><div class="similar">' + ''.join(card(x) for x in same) + '</div>' if same else '')
               + (f'<h3>Elsewhere in Europe</h3><div class="similar">' + ''.join(card(x) for x in other) + '</div>' if other else '')
               + f'<p><a href="../compare.html?a={cl["slug"]}{"&b=" + same[0]["slug"] if same else ""}">Compare {E(nm)} with another club</a></p>')
    src = [f'Final tables to {season(LAST[c])}. ' + ('Top-flight positions follow the official classification, including head-to-head tie-breaks and point deductions. ' if c in ('ENG', 'ESP', 'ITA') else '')
           + ('Lower-division positions before 2025/26 are worked out from match results and can differ from official tables where points were deducted.' if c == 'ENG' else 'Positions are worked out from match results.' if c in ('GER', 'FRA') else 'Second-division positions before 2025/26 are worked out from match results.')]
    src += [f'{season(y)}: finished first, but the title was revoked and not reassigned.' for y in R['revoked']]
    src += ['Relegations include dropping out of the divisions covered.']
    body = f'''<p class="crumb"><a href="../leagues/{c.lower()}.html">{E(m["country"])}</a></p>
<h1>{E(nm)}</h1><p class="lede">{status_line(cl)}</p>
{ceil_sec}
<h2>The story so far</h2><div class="story"><p>{story(cl)}</p></div>
<div class="chartbox"><div class="legend"><span style="--c:var(--acc)">Final position each season</span><span style="--c:var(--ink)">Ringed dots are titles</span></div>{trajectory(c, R["series"])}</div>
{how("How to read this chart", "<p>Every club in the divisions covered is placed on one ladder each season: the champions are 1st, and the top club of the second division comes straight after the bottom club of the first. Shaded bands are the divisions. Hover over or tap a dot for the season.</p>")}
{tiles_html}
<h2>Against the money</h2>{money_block(cl)}
{sim}
<h2>Sources</h2><ul class="small">{"".join(f"<li>{s}</li>" for s in src)}
<li>All figures can be downloaded on the <a href="../data.html">data page</a>. Spotted a mistake? <a href="../corrections.html?page={E(cl["slug"])}">Report it with a source</a>.</li></ul>
<script src="../live.js"></script>'''
    write(f'clubs/{cl["slug"]}.html', page(nm, body, '../', f'{nm}: how high the club can realistically go, its story, and how it does against its wage bill.'))

# ------------------------------------------------------------------ league statistics
def bottom_half_rows(c, a, b):
    d = L[c]; S = {(r.k, r.Season): r for r in d.itertuples()}; out = []
    for r in d[(d.tier == 1) & (d.Season >= a) & (d.Season <= b)].itertuples():
        if r.pos <= r.N / 2: continue
        out.append(dict(k=r.k, hit=float(any((x := S.get((r.k, r.Season + i))) is not None and x.tier == 1 and x.pos <= 4 for i in range(1, 11)))))
    return pd.DataFrame(out)
def bottom_half_rate(c, a, b):
    g = bottom_half_rows(c, a, b); n = len(g); hits = int(g.hit.sum()) if n else 0
    return hits / n if n else float('nan'), n, hits
from model import club_interval
BHCI = {c: club_interval(bottom_half_rows(c, 2004, 2015), 'hit') for c in ORDER}
PERIODS = [(1994, 1999, '1994–99'), (2000, 2005, '2000–05'), (2006, 2010, '2006–10'), (2011, 2015, '2011–15')]
BH = {c: [bottom_half_rate(c, a, b)[0] for a, b, _ in PERIODS] for c in ORDER}
BH0415 = {c: bottom_half_rate(c, 2004, 2015) for c in ORDER}
def distinct_top4(c, a, b):
    t = L[c][(L[c].tier == 1) & (L[c].Season >= a) & (L[c].Season <= b) & (L[c].pos <= 4)]; return t.k.nunique()
DT = {c: (distinct_top4(c, 2000, 2009), distinct_top4(c, 2016, 2025)) for c in ORDER}
CH = {c: L[c][L[c].champ] for c in ORDER}
def cname(c): return LEAGUES[c]['country']
TOPN = {c: tiername(c, 1) for c in ORDER}

for c in ORDER:
    m = LEAGUES[c]; d = L[c]; ch = CH[c]
    champs = ch.groupby('k').size().sort_values(ascending=False)
    last10 = ch[ch.Season > LAST[c] - 10]
    champ_list = ', '.join(f'<a href="../clubs/{slug(c, k)}.html">{E(NAMES[(c, k)])}</a> ({n})' for k, n in champs.items())
    bh = BH0415[c]
    ceil_rows = ''
    for tier in sorted(m['tiers']):
        for b in ['1', '2-4', '5-7', '8-12', '13+', 'rel', 'prom', 'top', 'bot']:
            parts = ceiling_parts(c, tier, b)
            if not parts: continue
            ceil_rows += f'<tr><td>{E(band_label(c, tier, b)[0].upper() + band_label(c, tier, b)[1:])}</td><td>' + '<br>'.join(f'{E(GOALS[g][0])}: <strong>{E(phrase(r.share, r.n, r.hits))}</strong> <span class="note">({r.hits} of {r.n}; range {r.lo:.0%}–{r.hi:.0%})</span>' for g, r in parts) + '</td></tr>'
    money = ''
    if c in TC:
        T = TC[c]; s = T[T.published_as != 'within the normal range'].sort_values('places_above_expected', ascending=False)
        money = (f'<h2>Who beat their money?</h2><p>Of {len(T)} clubs with at least eight seasons of published wage figures in the top two divisions, these finished clearly above or below what their wage bill usually buys. Every other club finished about where its money would put it.</p>'
                 '<div class="scroll"><table class="t"><tr><th>Club</th><th class="n">Places above or below, on average</th><th class="n">Seasons</th></tr>'
                 + ''.join(f'<tr><td><a href="../clubs/{slug(c, k)}.html">{E(NAMES.get((c, k), r.club))}</a></td><td class="n">{r.places_above_expected:+.1f}</td><td class="n">{int(r.seasons)}</td></tr>' for k, r in s.iterrows())
                 + '</table></div>' + how('How do we know?', '<p>See any club page under "Against the money" for the method. A club is listed only when its average gap is clearly larger than chance would produce.</p>'))
    groups = {}
    for x in sorted([x for x in clubs if x['c'] == c], key=lambda x: x['name']):
        groups.setdefault(x['R']['last'][0] if x['R']['last'] else 99, []).append(x)
    lists = ''.join(f'<h3>{E(tiername(c, t) + " in " + season(LAST[c]) if t != 99 else "Formerly in the divisions covered")}</h3><ul class="clubs">'
                    + ''.join(f'<li><a href="../clubs/{x["slug"]}.html">{E(x["name"])}</a></li>' for x in groups[t]) + '</ul>' for t in sorted(groups))
    body = f'''<p class="crumb"><a href="../leagues.html">Leagues</a></p><h1>How open is {E(the(c, 1))}?</h1>
<p class="lede">{E(m["country"])} · {" · ".join(E(v) for v in m["tiers"].values())} · {season(m["start"])} to {season(LAST[c])}</p>
<div class="tiles"><div class="tile"><b>{G[c]:.1f}×</b><span>as long to reach the top four as in a league where the past did not matter</span></div>
<div class="tile"><b>{champs.size}</b><span>different champions since {season(m["start"])}</span></div>
<div class="tile"><b>{last10.k.nunique()}</b><span>different champions in the last ten seasons</span></div>
<div class="tile"><b>{DT[c][1]}</b><span>different clubs in the top four, 2016/17–2025/26</span></div>
<div class="tile"><b>{DT[c][0]}</b><span>different clubs in the top four, 2000/01–2009/10</span></div></div>
<p class="small">Champions: {champ_list}.</p>
<h2>Can a bottom-half club reach the top four?</h2>
<p>Of the {bh[1]} times a club finished in the bottom half of {E(the(c, 1))} between {season(2004)} and {season(2015)}, <strong>{bh[2]}</strong> reached the top four within the next ten seasons: {E(phrase(bh[0], bh[1], bh[2]))} (likely range {BHCI[c][0]:.0%}–{BHCI[c][1]:.0%}).</p>
<div class="grid2"><div class="chartbox"><p class="small"><strong>The same question in each league</strong> (finishes 2004/05–2015/16)</p>
{bars([(cname(x), BH0415[x][0], x == c, f"{cname(x)}: {BH0415[x][2]} of {BH0415[x][1]}; likely range {BHCI[x][0]:.0%}–{BHCI[x][1]:.0%}") for x in ORDER], lambda v: f"{v:.0%}")}</div>
<div class="chartbox"><p class="small"><strong>Over time</strong>: share reaching the top four within ten seasons, by when the bottom-half finish happened</p>
{lines_chart({cname(x): BH[x] for x in ORDER}, [p[2] for p in PERIODS], cname(c), lambda v: f"{v:.0%}")}</div></div>
{how("How do we know?", "<p>Every bottom-half finish in the top division was followed forward ten seasons. The periods are short, so single seasons move the lines; the project's registered tests, which use the whole ladder and every season, are on the <a href='../about.html'>How it works</a> page.</p>")}
<h2>Realistic ceilings in {E(m["country"])}</h2><p>What happened next to clubs in each position (finishes from {season(START)}; ten-year goals to {season(END10)}, five-year goals to {season(END5)}).</p>
<div class="scroll"><table class="t"><tr><th>Clubs that…</th><th>…and then</th></tr>{ceil_rows}</table></div>
{money}
<h2>All clubs</h2>{lists}'''
    write(f'leagues/{c.lower()}.html', page(f'How open is {the(c, 1)}?', body, '../', f'How open is {the(c, 1)}? Champions, top-four turnover and realistic ceilings by position.', 'leagues.html'))

write('leagues.html', page('Leagues', '<h1>Leagues</h1><p class="lede">Five countries, every division in which clubs move between the top and the rest.</p><div class="similar">'
      + ''.join(f'<a href="leagues/{c.lower()}.html">{E(TOPN[c])}<span>{E(cname(c))} · {CH[c].k.nunique()} champions since {season(LEAGUES[c]["start"])} · bottom half to top four: {E(phrase(*BH0415[c]))}</span></a>' for c in ORDER)
      + '</div>', '', 'The five leagues compared.', 'leagues.html'))

# ------------------------------------------------------------------ home
idx = json.dumps([[x['name'], cname(x['c']), x['slug'], (f'{ordinal(x["R"]["last"][1])} in {the(x["c"], x["R"]["last"][0])}' if x['R']['last'] else '')]
                  for x in sorted(clubs, key=lambda x: (x['R']['last'] is None, x['name']))], ensure_ascii=False)
PROM = {c: CEIL[(c, 2, 'prom', 'stay5')] for c in ORDER}; REL = {c: CEIL[(c, 1, 'rel', 'back5')] for c in ORDER}
pers = PERS
ENGB = BH0415['ENG']
home = f'''<section class="hero"><h1>How far can your club climb?</h1>
<p class="lede">Every club in the top divisions of England, Spain, Italy, Germany and France since the early 1990s: how high clubs like yours have realistically gone, the story of each club, and — in England and France — whether it beats its money.</p>
<div class="search"><input id="q" type="search" placeholder="Type a club, e.g. Brentford, Lens, Bologna" autocomplete="off" aria-label="Find a club"><ul id="res" class="results"></ul></div>
<div class="chips">{"".join(f'<a href="leagues/{c.lower()}.html">{E(TOPN[c])}</a>' for c in ORDER)}<a href="live.html">This season so far</a></div></section>
<h2>What "mobility" means here</h2>
<p>Mobility is how easily a club can move up over the years — above all, into the top four. We compare each league with an imaginary one in which last season's position told you nothing about the next and every club had the same chance. In England, reaching the top four takes about <strong>4 times longer</strong> than in that imaginary league; in France about <strong>2.4 times</strong>.</p>
<div class="chartbox" style="max-width:560px">{bars([(cname(x), G[x], x == "ENG", f"{cname(x)}: {G[x]:.2f} times as long as in a league without memory") for x in ORDER], lambda v: f"{v:.1f}×", W=420)}</div>
{how("How is this worked out?", "<p>Every club is placed on one ladder each season, covering England's four divisions and the top two elsewhere. We measure how long, on average, it takes clubs to reach the top four, and compare that with the same calculation for a league in which positions are reshuffled at random every season. The ratio is 1 when a league is as open as pure chance. The test and its rejection rule were written down before the result was computed; see <a href='about.html'>How it works</a>.</p>")}
<p class="kicker">Three things the numbers show</p>
<div class="finds">
<div class="find"><h3>From the bottom half to the top four is a long shot — longest in England</h3>
<p>Of clubs finishing in the bottom half of the Premier League (2004/05–2015/16), {E(phrase(*ENGB))} reached the top four within ten years ({ENGB[2]} of {ENGB[1]}). In the Bundesliga it was {E(phrase(*BH0415["GER"]))} ({BH0415["GER"][2]} of {BH0415["GER"][1]}). The same clubs recur, so the likely ranges are wide: England {BHCI["ENG"][0]:.0%}–{BHCI["ENG"][1]:.0%}, Germany {BHCI["GER"][0]:.0%}–{BHCI["GER"][1]:.0%}.</p>
{bars([(cname(x), BH0415[x][0], x == "ENG", f"{cname(x)}: {BH0415[x][2]} of {BH0415[x][1]}") for x in ORDER], lambda v: f"{v:.0%}")}</div>
<div class="find"><h3>Going up is easier than staying up</h3>
<p>Only about 1 in 3 promoted clubs stayed in the top flight for the next five seasons. About half of relegated clubs were back within five.</p>
{bars([(cname(x), PROM[x].share, True, f"{cname(x)}: {PROM[x].hits} of {PROM[x].n} promoted clubs stayed up five seasons") for x in ORDER], lambda v: f"{v:.0%}")}<p class="note">Share of promoted clubs that stayed up for five seasons (promoted 2004/05–2020/21).</p></div>
<div class="find"><h3>Beating your money: most of it fades, some of it sticks</h3>
<p>Clubs that finished well above what their wage bill usually buys (on average {pers["ENG"][0]:.0f} places in England) were still about {pers["ENG"][1]:.0f} places above it the next season: roughly two-thirds faded, a third stayed. A few clubs, Brentford among them, beat their money almost every season. France is similar.</p>
<div class="legend"><span style="--c:var(--acc)">That season</span><span style="--c:var(--ctx)">The next season</span></div>{bars([("England", pers["ENG"][0], True, f"England: {pers['ENG'][2]} cases, average that season"), ("", pers["ENG"][1], False, "England: average the next season"), ("France", pers["FRA"][0], True, f"France: {pers['FRA'][2]} cases, average that season"), ("", pers["FRA"][1], False, "France: average the next season")], lambda v: f"+{v:.1f}", r=48)}<p class="note">Average places above what the wage bill usually buys.</p></div>
</div>
{how("How do we know?", f"<p>Positions come from every league table since the early 1990s; outcomes are followed forward for ten or five seasons, so recent finishes are not counted until their time has passed. Wage bills come from clubs' published accounts (England: Companies House; France: the DNCG). Over-performance here means finishing at least four places above what the wage bill usually buys. If it were pure luck, the next season would be back to zero on average; it is not, so part of it reflects something lasting about the club. More on the <a href='about.html'>How it works</a> page.</p>")}
<script>const C={idx};const q=document.getElementById('q'),r=document.getElementById('res');
const n=s=>s.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();
q.addEventListener('input',()=>{{const v=n(q.value.trim());r.innerHTML='';if(v.length<2)return;C.filter(c=>n(c[0]).includes(v)).slice(0,12).forEach(c=>{{const li=document.createElement('li'),a=document.createElement('a'),s=document.createElement('span');a.href='clubs/'+c[2]+'.html';a.textContent=c[0];s.textContent=c[1]+(c[3]?' · '+c[3]:'');a.appendChild(s);li.appendChild(a);r.appendChild(li);}});}});
q.addEventListener('keydown',e=>{{if(e.key==='Enter'){{const a=r.querySelector('a');if(a)location.href=a.href;}}}});</script>'''
write('index.html', page('How far can your club climb?', home, '', 'How far can your club climb? Realistic ceilings, club stories and wage bills for every club in five European leagues.', 'index.html'))

# ------------------------------------------------------------------ JSON for the compare page and the live tracker
os.makedirs(os.path.join(OUT, 'data'), exist_ok=True)
CJ = [dict(n=x['name'], c=x['c'], s=x['slug'], y=[[a, b, p, round((b - 1) + (p - 1) / max(1, int(L[x['c']][(L[x['c']].Season == a) & (L[x['c']].tier == b)].shape[0]) - 1), 3)] for a, b, p, _ in x['R']['series']],
           t=len(x['R']['titles']), f=x['R']['top4'], u=x['R']['promotions'], d=x['R']['relegations'], tf=x['R']['by_tier'].get(1, 0)) for x in clubs]
json.dump(dict(tiers={c: LEAGUES[c]['tiers'] for c in ORDER}, the={c: {t: the(c, t) for t in LEAGUES[c]['tiers']} for c in ORDER}, clubs=CJ), open(os.path.join(OUT, 'data', 'clubs.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
CEJ = {}
for r in C.itertuples():
    CEJ.setdefault(r.country, {}).setdefault(str(r.tier), {}).setdefault(r.band, []).append([r.goal, GOALS[r.goal][0], r.n, r.hits, round(r.share, 4), r.first, r.last, r.lo, r.hi])
LBL = {c: {str(t): {b: band_label(c, t, b) for b in BAND_GOALS} for t in LEAGUES[c]['tiers']} for c in ORDER}
FN = {}
for r in FEEDN.itertuples():
    if (r.country, r.k) in BYKEY: FN.setdefault(r.country, {})[r.team] = [BYKEY[(r.country, r.k)]['slug'], BYKEY[(r.country, r.k)]['name'], r.k]
json.dump(dict(ceilings=CEJ, labels=LBL, feed=FN, tiers={c: LEAGUES[c]['tiers'] for c in ORDER}, the={c: {t: the(c, t) for t in LEAGUES[c]['tiers']} for c in ORDER}, country={c: cname(c) for c in ORDER}),
          open(os.path.join(OUT, 'data', 'ceilings.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
snap = os.path.join(IN, 'live_snapshot.json')
if os.path.exists(snap): shutil.copy(snap, os.path.join(OUT, 'data', 'live_snapshot.json'))

# ------------------------------------------------------------------ static parts: compare, live, about, data, corrections
def part(name, rel=''):
    return open(os.path.join(HERE, name), encoding='utf-8').read().replace('{{VERSION}}', E(VERSION)).replace('{{DATE}}', E(DATE)).replace('{{START}}', season(START)).replace('{{END10}}', season(END10)).replace('{{END5}}', season(END5))
write('compare.html', page('Compare two clubs', part('compare.html.part'), '', 'Compare the paths of two clubs.', 'compare.html'))
write('live.html', page('This season so far', part('live.html.part'), '', 'The 2026/27 tables so far, with what clubs in each position have gone on to do. Provisional.', 'live.html'))
write('about.html', page('How it works', part('about.html.part'), '', 'How the figures on this site are produced, what they mean and what they do not.', 'about.html'))
write('corrections.html', page('Corrections', part('corrections.html.part'), '', 'Report an error.'))

lad = pd.concat([L[c].assign(country=c)[['country', 'Season', 'tier', 'pos', 'club', 'k', 'band']] for c in ORDER]).rename(columns={'Season': 'season_start', 'k': 'club_key', 'band': 'position_band'})
lad.sort_values(['country', 'season_start', 'tier', 'pos']).to_csv(os.path.join(OUT, 'data', 'positions_five_leagues.csv'), index=False)
C.to_csv(os.path.join(OUT, 'data', 'realistic_ceilings.csv'), index=False)
rec = pd.DataFrame([dict(country=x['c'], club=x['name'], club_key=x['k'], seasons=len(x['R']['series']), **{f'seasons_tier{t}': n for t, n in x['R']['by_tier'].items()},
                         titles=len(x['R']['titles']), top4=x['R']['top4'], promotions=x['R']['promotions'], relegations=x['R']['relegations']) for x in clubs])
rec.to_csv(os.path.join(OUT, 'data', 'club_records.csv'), index=False)
for c in TC: TC[c].reset_index().drop(columns=['group_accounts'], errors='ignore').to_csv(os.path.join(OUT, 'data', f'against_the_money_{c.lower()}.csv'), index=False)
TCS.rename(columns={'k': 'club_key', 'season': 'season_start', 'lrank': 'ladder_position', 'N': 'clubs_in_top_two', 'exp_lrank': 'position_wage_bill_usually_buys', 'places': 'places_above',
                    'pay': 'wage_bill_thousands_gbp_or_eur'}).to_csv(os.path.join(OUT, 'data', 'against_the_money_by_season.csv'), index=False)
for f in ('england_wage_panel.csv', 'france_wage_panel.csv'):
    pass
EP = pd.read_csv(os.path.join(IN, 'england_wage_panel.csv')); FP = pd.read_csv(os.path.join(IN, 'france_wage_panel.csv'))
EP[['k', 'season', 'payroll_k', 'ye', 'company_no', 'source', 'xcheck_diff_pct', 'flag_xcheck_conflict']].rename(columns={
    'k': 'club_key', 'season': 'season_start', 'payroll_k': 'staff_costs_gbp_thousands', 'ye': 'financial_year_end', 'company_no': 'companies_house_number',
    'source': 'reading', 'xcheck_diff_pct': 'difference_from_next_year_comparative_pct', 'flag_xcheck_conflict': 'readings_conflict'}).to_csv(os.path.join(OUT, 'data', 'payroll_england.csv'), index=False)
FP[['k', 'ladder_club', 'season', 'payroll_keur', 'payroll_source', 'consolidated', 'file', 'page']].rename(columns={
    'k': 'club_key', 'ladder_club': 'club', 'season': 'season_start', 'payroll_keur': 'payroll_eur_thousands', 'payroll_source': 'check', 'consolidated': 'group_perimeter',
    'file': 'dncg_report', 'page': 'report_page'}).to_csv(os.path.join(OUT, 'data', 'payroll_france.csv'), index=False)
for f in ('official_position_changes.csv', 'final_tables_2025_26.txt', 'code.zip', 'money_ceilings.csv', 'money_ceiling_models.csv'):
    if os.path.exists(os.path.join(IN, f)): shutil.copy(os.path.join(IN, f), os.path.join(OUT, 'data', f))
REPO = os.path.dirname(HERE)   # in the repository layout, zip the code that produced this site (D271)
if not os.path.exists(os.path.join(OUT, 'data', 'code.zip')) and os.path.isdir(os.path.join(REPO, 'analysis')):
    import zipfile
    with zipfile.ZipFile(os.path.join(OUT, 'data', 'code.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
        for top in ('analysis', 'site', 'api', 'docs'):
            for root, dirs, fs in os.walk(os.path.join(REPO, top)):
                dirs[:] = [d for d in dirs if d != '__pycache__']
                for f in sorted(fs):
                    if not f.endswith('.pyc'): z.write(os.path.join(root, f), os.path.relpath(os.path.join(root, f), REPO))
        for f in ('README.md', 'package.json', 'vercel.json'):
            if os.path.exists(os.path.join(REPO, f)): z.write(os.path.join(REPO, f), f)
files = [('positions_five_leagues.csv', 'Final position of every club, every season (England four divisions, elsewhere two), with its position band'),
         ('realistic_ceilings.csv', 'What happened next to clubs in each position band: counts, shares, 95% ranges from resampling clubs, number of different clubs, and the seasons used (reserve teams excluded)'),
         ('club_records.csv', 'Each club\'s record: seasons by division, titles, top-four finishes, promotions, relegations'),
         ('final_tables_2025_26.txt', 'The official 2025/26 final tables used'),
         ('official_position_changes.csv', 'Every top-flight position changed from the results-based table to the official classification, with the reason'),
         ('against_the_money_eng.csv', 'England: each club\'s average places above or below what its wage bill usually buys, with 95% intervals'),
         ('against_the_money_fra.csv', 'France: the same'),
         ('money_ceilings.csv', 'England and France: the realistic ceiling taking the wage bill into account, for each club in a position where it applies, with 95% ranges'),
         ('money_ceiling_models.csv', 'The models behind those figures, with the out-of-sample check against position alone'),
         ('against_the_money_by_season.csv', 'England and France, season by season: finish, the finish the wage bill usually buys, wage bill and its rank'),
         ('payroll_england.csv', 'England: club staff costs (£000) from Companies House accounts, with company number, year end and the cross-check'),
         ('payroll_france.csv', 'France: club payroll (€000) from the DNCG\'s published accounts, with report and page'),
         ('code.zip', 'The code that produces every figure')]
dl = ''.join(f'<tr><td><a href="data/{f}" download>{f}</a></td><td>{E(d)}</td></tr>' for f, d in files if os.path.exists(os.path.join(OUT, 'data', f)))
write('data.html', page('Data and code', f'''<h1>Data and code</h1><p class="lede">Everything on this site can be checked and reproduced from these files. Version {E(VERSION)}, {E(DATE)}.</p>
<div class="scroll"><table class="t"><tr><th>File</th><th>Contents</th></tr>{dl}</table></div>{'' if os.path.exists(os.path.join(OUT, 'data', 'code.zip')) else '<p class="note">The code archive will be added before the site is made public.</p>'}
<h2>Sources</h2><ul><li>Match results 1992/93–2024/25: the engsoccerdata and football-data compilations; England 2022/23 from openfootball. Final tables 2025/26: the official tables as published on each league's Wikipedia page, checked against openfootball's results for the top divisions and the Championship.</li>
<li>This season (2026/27): tables from <a href='https://www.football-data.org'>football-data.org</a>, provisional; openfootball's public-domain files as a fallback.</li>
<li>England wage bills: statutory accounts at Companies House. France wage bills: the DNCG's annual reports on club accounts.</li></ul>
<h2>Who made this</h2><p>The Competitive Mobility Project is by {AUTHOR}. The code and data are on <a href="https://github.com/lamindiallo/competitive-mobility-project">GitHub</a>, including the <a href="https://github.com/lamindiallo/competitive-mobility-project/blob/main/docs/Hypothesis_Register.md">register of tests</a> written before the results were computed.</p>
<h2>What is not here</h2><ul><li>The original filings: they are public at their sources and cited row by row.</li><li>Transfer-market valuations or anything derived from them.</li><li>Anyone's individual pay.</li><li>Club badges: they are the clubs' property.</li></ul>''', '', 'Downloads.'))
shutil.copy(os.path.join(HERE, 'style.css'), os.path.join(OUT, 'style.css')); shutil.copy(os.path.join(HERE, 'live.js'), os.path.join(OUT, 'live.js'))
print(len(clubs), 'club pages;', sum(1 for x in clubs if x['c'] in TC and x['k'] in TC[x['c']].index), 'with an against-the-money verdict')
