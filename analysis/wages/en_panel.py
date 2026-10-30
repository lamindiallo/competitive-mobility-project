"""Build the England wage panel from OCR'd Companies House accounts (ch_ocr.py output).
Identification: company number read from the document (or the file name Companies House gave it), matched to the
club's registered company. Season: a financial year ending between May and December of year Y is season Y-1/Y.
A payroll value is used only if its staff-cost note passes its own identity (components = printed total).
The comparison column of the following year's accounts is a second, independent reading of the same figure.
Fallback identification: the download queue aligned to the files (ch_manifest_align.py), used only where OCR read no
company number and the file's own OCR year-end equals the queue entry's date.
Usage: FR_SRC=... python -I en_panel.py <ch_ocr.csv> <out_dir> [manifest_match.csv]"""
import sys, os, re, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'rcm'))
from ladder import eng_ladder
from clubkey import ck

COMPANY = {  # registered company that employs the first-team squad -> ladder key
    '00109244': 'arsenal', '05891280': 'aston villa',   # NSWE Sports Ltd group accounts (D274)
    '06632170': 'bournemouth', '03642327': 'brentford',
    '00081077': 'brighton and hove albion', '00054222': 'burnley', '00109065': 'cardiff city', '01965149': 'chelsea',
    '07270793': 'crystal palace', '00036624': 'everton', '02114486': 'fulham', '01771361': 'huddersfield town',
    '04032392': 'hull city', '00315421': 'ipswich town', '06233875': 'leeds united', '04593477': 'leicester city',
    '00035668': 'liverpool', '06133975': 'luton town', '00040946': 'manchester city', '00095489': 'manchester united',
    '01947851': 'middlesbrough', '00031014': 'newcastle united', '00154044': 'norwich city', '01630402': 'nottingham forest',
    '00060094': 'queens park rangers', '00061564': 'sheffield united', '00053301': 'southampton', '00099885': 'stoke city',
    '00049116': 'sunderland', '00123414': 'swansea city', '00057186': 'tottenham hotspur', '00104194': 'watford',
    '03295063': 'west bromwich albion', '00066516': 'west ham united', '01989823': 'wolverhampton wanderers',
    # Championship regulars 2012-2024 (D254 protocol: tiers 1-2)
    '00027318': 'birmingham city', '00053482': 'blackburn rovers', '03230871': 'bristol city', '00049139': 'derby county',
    '00053703': 'reading', '02509978': 'sheffield wednesday', '01924222': 'millwall', '00039494': 'preston north end',
    '04573250': 'barnsley', '06550400': 'rotherham united', '13161421': 'wigan athletic', '12184224': 'bolton wanderers',
    '00048409': 'blackpool', '01788466': 'charlton athletic', '07612487': 'coventry city'}
EXCLUDED = {'03375789': 'Aston Villa Football Club Ltd: non-playing staff only (~£10m, ~1,400 mostly matchday employees) (D274)',
            '00046572': 'Aston Villa Ltd: holding/property company, 3 employees, turnover £0.7m (D274)'}
QUEUE = {}
MONTHS = {m: i for i, m in enumerate(['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
                                      'september', 'october', 'november', 'december'], 1)}

def ident(row):
    """Company number from the file name (Companies House-named files) or the OCR'd cover; tolerate one misread digit."""
    m = re.match(r'(\d{8})_aa_', str(row.file))
    if m: return m.group(1), 'filename'
    known = list(COMPANY) + list(EXCLUDED)
    try: cands = json.loads(row.company_no) if isinstance(row.company_no, str) and row.company_no.startswith('[') else [[str(row.company_no), 1]]
    except Exception: cands = []
    for c, _ in cands:
        s = re.sub(r'\D', '', str(c).split('.')[0]).zfill(8)
        if s in known: return s, 'ocr_exact'
    for c, _ in cands:
        s = re.sub(r'\D', '', str(c).split('.')[0]).zfill(8)
        close = [k for k in known if sum(a != b for a, b in zip(k, s)) == 1]
        if len(close) == 1: return close[0], 'ocr_1digit'
    q = QUEUE.get(row.file)
    if q: return q, 'download_order'
    return None, None

NUMTOK = r'\(?-?\d{1,3}(?:,\d{3})+\)?|\(?-?\d{1,4}\)?'
LABEL = re.compile(r'wages,?\s+(?:(?:and|ond|an|&)\s+)?salar\w*(?:\s+and\s+bonuses)?|benefits?\s+in\s+kind|other\s+employment\s+costs(?:\s*\([^)]{0,40}\))?|social\s+sec\w*(?:\s+costs?)?|national\s+insurance|(?:other\s+)?pen\w{2,5}\s+(?:costs?|contributions?)|(?:cost\s+of\s+)?defined\s+contribution[\w ]{0,30}?(?=\s[\d(])|share[- ]based[\w ]{0,30}?(?=\s[\d(])|termination[\w ]{0,30}?(?=\s[\d(])|redundancy[\w ]{0,30}?(?=\s[\d(])|other\s+(?:staff|employee)[\w ]{0,20}?costs?', re.I)

def _num(t):
    v = int(re.sub(r'[^\d]', '', t)); return -v if t.startswith('(') or t.startswith('-') else v

def _reparse(t):
    m0 = re.search(r'wages,?\s+(?:(?:and|ond|an|&)\s+)?salar', t, re.I)
    if not m0: return None, False, None, False
    t = t[m0.start():]
    labs = list(LABEL.finditer(t))
    comp, compp, tot = [], [], None
    for i, m in enumerate(labs):
        seg = t[m.end(): labs[i + 1].start() if i + 1 < len(labs) else len(t)]
        ns = [_num(x) for x in re.findall(NUMTOK, seg)]
        if len(ns) < 2: return None, False, None, False
        comp.append(ns[0]); compp.append(ns[1])
        if len(ns) >= 4:
            if i + 1 < len(labs) and abs(ns[2] - sum(comp)) <= 2 and abs(ns[3] - sum(compp)) <= 2:
                continue                           # a printed subtotal (e.g. wages + other employment costs); more lines follow
            tot = ns[2:4]; break                   # component pair followed by the totals: the note ends here
    if not tot or len(comp) < 2: return None, False, None, False   # a one-line "identity" is trivially true
    ok = abs(sum(comp) - tot[0]) <= 2 and tot[0] >= 1000
    okp = abs(sum(compp) - tot[1]) <= 2 and tot[1] >= 1000
    return (tot[0] if ok else None), ok, (tot[1] if okp else None), okp

def reparse(text):
    """Second, stricter reading of the saved staff-cost note text: each labelled component takes the two numbers that
    follow it (current, prior); the first label followed by four numbers carries the last component and the printed
    totals. Accepted only if the components sum (±2) to the printed total. If not, one retry replaces '§' and '$'
    (Tesseract's usual misreading of a leading 5) — again accepted only if the identity then holds.
    Returns (total, ok, prior_total, prior_ok)."""
    if not isinstance(text, str): return None, False, None, False
    t = re.sub(r'\((?:note|notes)\s*\d+[a-z]?\)|note\s*\d+', ' ', text, flags=re.I)
    a = _reparse(t)
    if a[1] and a[3]: return a
    b = _reparse(re.sub(r'[§$](?=[\d,])', '5', t))
    return (a[0], a[1], a[2], a[3]) if (a[1] or not b[1]) and (a[3] or not b[3]) else \
           ((a[0], True) if a[1] else (b[0], b[1])) + ((a[2], True) if a[3] else (b[2], b[3]))

def year_end(txt):
    if not isinstance(txt, str): return None
    m = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', re.sub(r'\s+', ' ', txt))
    if not m: return None
    mon = MONTHS.get(m.group(2).lower())
    return (int(m.group(3)), mon) if mon else None

def season_of(ye):
    y, m = ye
    return y - 1 if m >= 5 else y - 2        # FY ending May-Dec Y -> season (Y-1)/Y; Jan-Apr Y -> (Y-2)/(Y-1)

def to_k(v):
    if v is None or (isinstance(v, float) and np.isnan(v)): return None
    return v / 1000.0 if abs(v) > 5_000_000 else float(v)     # statutory notes in £ -> £k

def truthy(v):
    return v is True or (isinstance(v, (bool, np.bool_)) and bool(v)) or (isinstance(v, str) and v.strip().lower() == 'true')

if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
    if len(sys.argv) > 3:
        MM = pd.read_csv(sys.argv[3]); MM = MM[MM.confirmed.astype(bool)]
        QUEUE.update({f: str(c).zfill(8) for f, c in zip(MM.file, MM.queue_company)})
    d = pd.read_csv(src)
    rows, log = [], []
    for r in d.itertuples(index=False):
        co, how = ident(r)
        ye = year_end(r.year_end)
        if co is None or ye is None:
            log.append((r.file, 'unidentified', co, r.year_end)); continue
        if co in EXCLUDED: log.append((r.file, 'excluded_entity', co, r.year_end)); continue
        s = season_of(ye)
        st, sok, pt, pok = r.staff_total, truthy(r.staff_ok), r.prior_total, truthy(r.prior_ok)
        how2 = 'first_reading'
        if not (sok and pok):
            t2, ok2, p2, okp2 = reparse(getattr(r, 'staff_text', None))
            if not sok and ok2: st, sok, how2 = t2, True, 'second_reading'
            if not pok and okp2: pt, pok = p2, True
        r = r._replace(staff_total=st, staff_ok=sok, prior_total=pt, prior_ok=pok)
        if truthy(r.staff_ok):
            rows.append(dict(company_no=co, k=COMPANY[co], season=s, payroll_k=to_k(r.staff_total), turnover_k=to_k(r.turnover),
                             source='own_year', file=r.file, id_method=how, reading=how2, ye=f'{ye[0]}-{ye[1]:02d}'))
        if truthy(r.prior_ok):
            rows.append(dict(company_no=co, k=COMPANY[co], season=s - 1, payroll_k=to_k(r.prior_total), turnover_k=to_k(r.turnover_prior),
                             source='next_year_comparative', file=r.file, id_method=how, ye=f'{ye[0]}-{ye[1]:02d}'))
        if not truthy(r.staff_ok) and not truthy(r.prior_ok): log.append((r.file, 'no_identity_pass', co, r.year_end))
    R = pd.DataFrame(rows)
    # one value per club-season: own-year reading preferred; the comparative is the cross-check
    own = R[R.source == 'own_year'].drop_duplicates(['k', 'season'])
    comp = R[R.source == 'next_year_comparative'].drop_duplicates(['k', 'season'])[['k', 'season', 'payroll_k', 'turnover_k']]
    P = own.merge(comp.rename(columns={'payroll_k': 'payroll_comparative', 'turnover_k': 'turnover_comparative'}), on=['k', 'season'], how='outer')
    only_comp = P.payroll_k.isna() & P.payroll_comparative.notna()
    P.loc[only_comp, 'payroll_k'] = P.loc[only_comp, 'payroll_comparative']
    P.loc[only_comp, 'turnover_k'] = P.loc[only_comp, 'turnover_comparative']
    P['source'] = np.where(only_comp, 'next_year_comparative_only', np.where(P.payroll_comparative.notna(), 'own_year_crosschecked', 'own_year'))
    for c in ('payroll_k', 'payroll_comparative'): P[c] = P[c].abs()     # some notes print costs in brackets
    P['xcheck_diff_pct'] = np.where(P.source == 'own_year_crosschecked',
                                    (P.payroll_k - P.payroll_comparative).abs() / P.payroll_k * 100, np.nan)  # only two independent readings count
    P['flag_xcheck_conflict'] = P.xcheck_diff_pct > 2      # two independent readings disagree: restatement or misread; excluded from tests until read by hand
    P.loc[(P.turnover_k < 1000) | (P.turnover_k > 2_000_000), 'turnover_k'] = np.nan     # OCR picked a year or a note number
    P['ratio_wage_turnover'] = P.payroll_k / P.turnover_k
    P['flag_implausible'] = (P.ratio_wage_turnover < 0.25) | (P.ratio_wage_turnover > 2.0) | (P.payroll_k < 2000)
    lad = eng_ladder(4, 2010, 2024); lad['k'] = lad.club.map(ck)
    P = P.merge(lad[['k', 'Season', 'tier', 'pos']].rename(columns={'Season': 'season'}), on=['k', 'season'], how='left')
    P = P.sort_values(['season', 'tier', 'pos'])
    P.to_csv(f'{out}/england_wage_panel.csv', index=False)
    pd.DataFrame(log, columns=['file', 'issue', 'company_no', 'year_end']).to_csv(f'{out}/england_ocr_issues.csv', index=False)
    print(len(P), 'club-seasons;', P.k.nunique(), 'clubs; seasons', int(P.season.min()), '-', int(P.season.max()))
    print(P.source.value_counts().to_dict())
    xc = P.xcheck_diff_pct.dropna(); print(f'cross-checked {len(xc)}: exact (<0.1%) {int((xc < 0.1).sum())}, within 2% {int((xc < 2).sum())}')
    print('cross-check conflicts (excluded from tests):', int(P.flag_xcheck_conflict.sum()))
    print('implausible flags', int(P.flag_implausible.sum()), '| unmatched to ladder', int(P.tier.isna().sum()))
    print('issues', pd.Series([x[1] for x in log]).value_counts().to_dict())
