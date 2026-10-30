"""Map DNCG club pages onto the French ladder (03 Data/ladders/ladder_FRA.csv) and build the France wage panel.
Matching: per season, one-to-one assignment of DNCG names to ladder clubs in tiers 1-2 (Hungarian on name
similarity). Every match below the similarity threshold is listed for manual review; none is accepted silently.
Usage: python -I dncg_panel.py <dncg_raw.csv> <ladder_FRA.csv> <names_2017_18_ocr.csv> <out_dir>"""
import sys, re, unicodedata, difflib, os
import numpy as np, pandas as pd
from scipy.optimize import linear_sum_assignment

STOP = {'fc', 'sc', 'as', 'ac', 'rc', 'us', 'sco', 'ogc', 'fco', 'losc', 'sa', 'sas', 'sasp', 'saos', 'eusrl', 'association',
        'football', 'club', 'olympique', 'stade', 'de', 'du', 'la', 'le', 'les', 'en', 'avant', 'f', 'c', 'a', 's', 'et', 'd',
        'filiales', 'promotion', 'holding', 'sci', 'groupe', 'products', 'merchandising', 'sese', 'psg', 'asse', 'chaudron', 'vert',
        'osc', 'af', 'hsc', 'ggfc', 'es', 'ea', 'cs', 'lb', 'aube', 'champagne', 'ardennes', 'metropole', 'sasu', 'auvergne',
        'esperance', 'sportive', 'racing', 'tg', 'gaillard', 'thonon', 'alsace', 'aveyron', 'herault', 'berrichonne', 'cote', 'or', 'malherbe'}
ALIAS = {'losc': 'lille', 'psg': 'paris saint germain', 'fbbp 01': 'bourg peronnas', 'estac': 'troyes', 'gfca': 'gazelec ajaccio',
         'havre ac': 'le havre', 'stade malherbe caen': 'caen', 'en avant de guingamp': 'guingamp', 'ea guingamp': 'guingamp',
         'la berrichonne de chateauroux': 'chateauroux', 'quevilly rouen metropole': 'quevilly rouen', 'dfco': 'dijon',
         'dijon football cote d or': 'dijon', 'red star fc': 'red star', 'tours fc': 'tours', 'losc lille metropole': 'lille',
         'rc str asbourg alsace': 'strasbourg', 'olympique lyonnais': 'lyon', 'olympique lyon': 'lyon', 'olympique de marseille': 'marseille',
         'olympique marseille': 'marseille', 'nimes olympique': 'nimes', 'rc lens': 'lens', 'racing club de lens': 'lens'}

def norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'\(.*$', '', s)                                   # legal-form tails in brackets
    s = re.sub(r'\+.*$', '', s)                                   # "+ ASSE PRODUCTS ..." perimeter tails
    s = re.sub(r'[^a-z0-9 ]', ' ', s); s = re.sub(r'\s+', ' ', s).strip()
    return ALIAS.get(s, s)

def core(s):
    toks = [t for t in norm(s).split() if t not in STOP]
    return ' '.join(toks) or norm(s)

def sim(a, b):
    a, b = core(a), core(b)
    if not a or not b: return 0.0
    r = difflib.SequenceMatcher(None, a, b).ratio()
    ta, tb = set(a.split()), set(b.split())
    j = len(ta & tb) / max(len(ta | tb), 1)
    sub = 1.0 if (a in b or b in a) else 0.0
    return max(r, j, 0.9 * sub)

if __name__ == '__main__':
    raw, lad_fn, names17, out = sys.argv[1:5]
    os.makedirs(out, exist_ok=True)
    d = pd.read_csv(raw)
    nm = pd.read_csv(names17)
    m17 = dict(zip(nm.page, nm.club))
    d.loc[d.season == 2017, 'club'] = d.loc[d.season == 2017, 'page'].map(m17).fillna(d.loc[d.season == 2017, 'club'])
    # Lyon IFRS pages: keep the page whose financial year ends on 30 June of season+1
    if 'ifrs' in d:
        ly = d.ifrs.fillna(False).astype(bool)
        keep = ~ly | d.apply(lambda r: isinstance(r.get('period_end'), str) and r['period_end'].endswith(str(r.season + 1)[2:]), axis=1)
        d = d[keep]
    ov = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dncg_name_overrides.csv'))
    for _, o in ov.iterrows():
        m = (d.season == o.season) & (d.page == o.page) & d.club.astype(str).str.startswith(o.orig)
        d.loc[m, 'club'] = o.club; d.loc[m, 'header'] = o.club; d.loc[m, 'name_override'] = o.evidence
    lad = pd.read_csv(lad_fn)
    rows, review = [], []
    for s, g in d.groupby('season'):
        L = lad[(lad.Season == s) & lad.tier.isin([1, 2])].reset_index(drop=True)
        g = g.reset_index(drop=True)
        def hsim(row, lc):
            base = sim(row['club'], lc)
            h = norm(row.get('header', '') if isinstance(row.get('header', ''), str) else '')
            toks = [x for x in core(lc).split() if len(x) > 2]
            if toks and all(re.search(r'\b' + re.escape(x) + r'\b', h) for x in toks): base = max(base, 0.95)
            return base
        S = np.array([[hsim(g.iloc[i], b) for b in L.club] for i in range(len(g))])
        ri, ci = linear_sum_assignment(-S)
        for i, j in zip(ri, ci):
            r = g.iloc[i].to_dict(); r.update(k=L.k[j], ladder_club=L.club[j], tier=int(L.tier[j]), pos=int(L.pos[j]), match_sim=round(S[i, j], 3))
            rows.append(r)
            if S[i, j] < 0.75: review.append((s, g.club[i], L.club[j], round(S[i, j], 3)))
            if S[i, j] < 0.5: rows[-1]['match_rejected'] = True
        unmatched = set(range(len(L))) - set(ci)
        for j in unmatched: review.append((s, '-- NO DNCG PAGE --', L.club[j], None))
    P = pd.DataFrame(rows)
    # cross-report verification: the next season's report prints this season as its comparison column
    nxt = P[['season', 'k', 'prior_payroll']].dropna().copy(); nxt['season'] -= 1
    nxt = nxt.rename(columns={'prior_payroll': 'payroll_next_report'})
    P = P.merge(nxt, on=['season', 'k'], how='left')
    P['xreport_agree'] = (P.payroll - P.payroll_next_report).abs() <= 2
    use_next = (~P.costs_ok.astype(bool) | P.nonstandard.fillna(False).astype(bool)) & P.payroll_next_report.notna() & ~P.xreport_agree
    P['payroll_source'] = np.where(use_next, 'next_report_comparative', np.where(P.costs_ok.astype(bool), 'own_report_identity_checked',
                          np.where(P.consolidated.fillna(False).astype(bool), 'consolidated_group_unverified', 'own_report_unverified')))
    P.loc[use_next, 'payroll'] = P.loc[use_next, 'payroll_next_report']
    P.loc[P.payroll_source.eq('own_report_unverified') & P.xreport_agree.fillna(False), 'payroll_source'] = 'own_report_xreport_checked'
    P.to_csv(f'{out}/france_wage_panel_raw.csv', index=False)
    pd.DataFrame(review, columns=['season', 'dncg_name', 'ladder_club', 'sim']).to_csv(f'{out}/france_match_review.csv', index=False)
    print(len(P), 'club-seasons matched;', len(review), 'items for review')
    for x in review: print(x)
