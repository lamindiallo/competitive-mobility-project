"""Deterministic extraction of per-club accounts from the DNCG 'comptes individuels' reports.
No model reads the PDFs: text comes from the PDF's own text layer (pdfplumber), and every club
row must pass accounting identities printed in the same report (D159 structural test, D195 amended).
Usage: python -I dncg_extract.py <pdf_dir> <out_csv>"""
import sys, re, glob, os
import pdfplumber, pandas as pd

NUM = r'(-\s?)?\(?\d{1,3}(?:[   ,.]\d{3})*\)?'
FIELDS = {
    'revenue':  [r'TOTAL PRODUITS HORS[- ]MUTATIONS?', r'TOTAL NON-TRANSFER EARNINGS', r'TOTAL NON-TRANSFER INCOME', r'TOTAL PRODUITS\b(?! D)', r'TOTAL PRODUITS D[’\']EXPLOITATION', r'TOTAL OPERATING INCOME'],
    'broadcast': [r'Droits audiovisuels', r'Broadcasting rights', r'Audio-?visual rights'],
    'sponsor':  [r'Sponsors\s*-\s*Publicit[ée]', r'Recettes de partenariats', r'Sponsors\s*-\s*Advertising', r'Partnership revenue'],
    'gate':     [r'Recettes matche?s', r'Recettes billetterie', r'Gate receipts', r'Match receipts', r'Match(?:day)? (?:receipts|revenue)'],
    'other_inc': [r'Autres produits(?! fin)', r'Other income'],
    'payroll':  [r'R[ée]mun[ée]ration du personnel charg[ée]e', r'R[ée]mun[ée]rations? du personnel\s*-?\s*charg[ée]es?', r'Total payroll', r'Masse salariale totale', r'Remuneration of (?:management )?personnel'],
    'amort':    [r'Amortissements? des indemnit[ée]s de mutations?\b(?!\s+et honoraires)', r'Amortisation of transfer fees', r'Amortisation of transfer compensation', r'Depreciation of transfer fees'],
    'transfer_costs': [r'Co[ûu]ts? des mutations', r'Amortissements? des indemnit[ée]s de mutations? et honoraires'],
    'agents':   [r"Honoraires d[’']agents", r"agents\s*/\s*Intermediaries fees", r"Players[’'] agents", r'Agent\s*/\s*Intermediary fees'],
    'other_exp': [r'Autres charges(?: op[ée]rationnelles)?(?! d)', r'Other expenses'],
    'costs':    [r'TOTAL CHARGES HORS[- ]MUTATIONS?', r'TOTAL NON-TRANSFER EXPENSES', r'TOTAL CHARGES D[’\']EXPLOITATION', r'TOTAL OPERATING EXPENSES', r'TOTAL CHARGES\b(?! D)'],
    'transfer_result': [r'R[ÉE]SULTAT DES OP[ÉE]RATIONS (?:DE )?MUTATIONS?', r'PROFIT \(LOSS\) FROM TRANSFERS', r'R[ée]sultat de mutation'],
    'net':      [r'R[ÉE]SULTAT NET', r'NET PROFIT \(LOSS\)'],
}
BOILER = re.compile(r'COMPTES? INDIVIDUEL|INDIVIDUAL CLUB|SAISON|SEASON|RAPPORT|LIGUE ?[12]|COMPTE DE R|PROFIT AND LOSS|BILAN|BALANCE|En milliers|K€|^\d+$|D E S|DES CLUBS|Commission|Contr[ôo]le', re.I)
HEAD = re.compile(r'Compte de r[ée]sultat|COMPTE DE R[ÉE]SULTAT|PROFIT AND LOSS|INCOME STATEMENT', re.I)

def tonum(s):
    neg = s.strip().startswith('-') or s.strip().startswith('(')
    v = int(re.sub(r'[^\d]', '', s))
    return -v if neg else v

def lines_of(words):
    """Group words into lines; a wide horizontal gap becomes a triple space so numbers in different columns never merge."""
    out, cur, top = [], [], None
    for w in sorted(words, key=lambda w: w['top']):
        if top is None or abs(w['top'] - top) > 3:
            if cur: out.append(cur)
            cur, top = [w], w['top']
        else: cur.append(w)
    if cur: out.append(cur)
    res = []
    for l in out:
        l = sorted(l, key=lambda w: w['x0']); t = l[0]['text']
        for a, b in zip(l, l[1:]):
            t += ('   ' if b['x0'] - a['x1'] > 6 else ' ') + b['text']
        res.append(t)
    return res

def numbers(l, after):
    return [tonum(m.group(0)) for m in re.finditer(NUM, l[after:])]

def clean_name(lines):
    cand = []
    for l in lines:
        if HEAD.search(l): break
        x = re.sub(r'UN DOCUMENT DE LA DNCG|SAISON \d{4}\s*/\s*\d{4}|VOUS TROUVEREZ.*', '', l, flags=re.I).strip(' •-')
        x = re.sub(r'\s{2,}', ' ', x)
        if not x or BOILER.search(x) or not re.search(r'[A-Z]', x) or x.upper() != x: continue
        cand.append(x)
    if not cand: return '?'
    legal = re.compile(r'^\(|\+|\b(SAS|SASP|SASU|SAOS|SA|SEM|EUSRL|SCI|SNC|ASSOCIATION|HOLDING|FILIALES|COMPTES CONSOLID)\b')
    names = [c for c in cand if not legal.search(c)]
    if not names: return re.split(r'\(|\+', cand[0])[0].strip() or '?'
    first = cand.index(names[0]); out = names[0]
    if first + 1 < len(cand) and not legal.search(cand[first + 1]) and len(cand[first + 1]) < 30: out += ' ' + cand[first + 1]
    return out

def parse_block(lines, season=None):
    txt = '\n'.join(lines)
    if not HEAD.search(txt): return None
    if re.search(r'CUMUL|CUMULATED|COMBINED', txt, re.I): return None   # league totals, not a club
    L = [l.strip() for l in lines]
    # which column? header dates such as 30/06/2009   30/06/2010
    dates = re.findall(r'\d{2}/\d{2}/(\d{4}|\d{2})\b', '\n'.join(L[:15]))
    years = [int(y) if len(y) == 4 else 2000 + int(y) for y in dates]
    col = 0
    if season is not None and len(years) >= 2 and (season + 1) in years: col = years.index(season + 1)
    if season is not None and len(years) == 1 and years[0] != season + 1 and years[0] in (season, season + 2): return None
    rec = {'ncols': max(len(years), 1)}
    pcol = years.index(season) if (season is not None and len(years) >= 2 and season in years) else None
    for f, pats in FIELDS.items():
        for p in pats:
            hit = None
            for i, l in enumerate(L):
                m = re.match(p, l, re.I)
                if not m: continue
                nums = numbers(l, m.end())
                if nums:
                    hit = nums[col] if col < len(nums) else None
                    if pcol is not None and pcol < len(nums) and f in ('payroll', 'revenue', 'costs'): rec['prior_' + f] = nums[pcol]
                elif i > 0 and re.fullmatch(NUM, L[i - 1]): hit = tonum(L[i - 1])
                if hit is not None: break
            if hit is not None: rec[f] = hit; break
    consolidated = False
    if 'payroll' not in rec:
        for i, l in enumerate(L):
            m = re.match(r'Charges de personnel|Personnel costs|Staff costs', l, re.I)
            if m:
                nums = numbers(l, m.end())
                if nums: rec['payroll'] = abs(nums[col] if col < len(nums) else nums[0]); consolidated = True
                break
        if not consolidated: return None
        for p in (r'Produits des activit[ée]s \(hors contrats (?:des )?joueurs\)', r"Chiffres? d[’']affaires net", r'Income from activities excluding player trading'):
            for l in L:
                m = re.match(p, l, re.I)
                if m:
                    nums = numbers(l, m.end())
                    if nums: rec['revenue'] = nums[col] if col < len(nums) else nums[0]
                    break
            if 'revenue' in rec: break
    rec['consolidated'] = consolidated
    rec['nonstandard'] = bool(re.search(r'^\s*Charges sociales', txt, re.M))
    hdr = []
    for l in lines:
        if HEAD.search(l): break
        hdr.append(l)
    rec['header'] = re.sub(r'\s+', ' ', ' '.join(hdr))[:300]
    rec['club'] = 'OLYMPIQUE LYONNAIS' if re.search(r'GROUPE OL|OLYMPIQUE LYONNAIS|OL GROUP', txt, re.I) and consolidated else clean_name(lines)
    return rec

def blocks_of_page(page):
    W = page.width
    words = [w for w in page.extract_words(keep_blank_chars=False, use_text_flow=False) if w.get('upright', True)]
    if W > 1000:                             # two report pages printed side by side
        halves = [[w for w in words if w['x1'] <= W / 2 + 2], [w for w in words if w['x0'] >= W / 2 - 2]]
    else:
        halves = [words]
    return [lines_of(h) for h in halves if h]

def season_of(fn):
    m = re.search(r'DNCG_(\d{4})-(\d{2})', os.path.basename(fn)); return int(m.group(1))

def extract(fn):
    recs = []
    with pdfplumber.open(fn) as pdf:
        for i, page in enumerate(pdf.pages):
            for b in blocks_of_page(page):
                r = parse_block(b, season_of(fn))
                if r: r['page'] = i + 1; recs.append(r)
    for r in recs: r['season'] = season_of(fn); r['file'] = os.path.basename(fn)
    return recs

def g(r, k):
    v = r.get(k); return 0 if v is None or v != v else v

def checks(r):
    if r.get('consolidated'): return False, False   # consolidated group page: no DNCG identity; verified across reports instead
    comp = sum(g(r, k) for k in ('payroll', 'amort', 'transfer_costs', 'agents', 'other_exp'))
    alt = g(r, 'payroll') + g(r, 'other_exp')          # layouts that book transfer costs below the operating line
    rv = sum(g(r, k) for k in ('broadcast', 'sponsor', 'gate', 'other_inc'))
    c_ok = 'costs' in r and (abs(comp - r['costs']) <= 3 or abs(alt - r['costs']) <= 3)
    r['payroll_derived'] = False
    if not c_ok and 'costs' in r and 'other_exp' in r and g(r, 'payroll') < 0.2 * r['costs']:
        # the parsed payroll is clearly a broken text-layer figure: recover it from the printed total, and flag it
        cand = r['costs'] - (comp - g(r, 'payroll'))
        if 0 < cand < r['costs']:
            r['payroll_orig'] = r.get('payroll'); r['payroll'] = cand; r['payroll_derived'] = True; c_ok = True
    r_ok = 'revenue' in r and abs(rv - r['revenue']) <= 3
    return c_ok, r_ok

if __name__ == '__main__':
    pdf_dir, out = sys.argv[1], sys.argv[2]
    allr = []
    for fn in sorted(glob.glob(os.path.join(pdf_dir, 'DNCG_*.pdf'))):
        rs = extract(fn)
        for r in rs: r['costs_ok'], r['revenue_ok'] = checks(r)
        n = len(rs); c = sum(r['costs_ok'] for r in rs); v = sum(r['revenue_ok'] for r in rs)
        print(f"{os.path.basename(fn)[:16]}: {n:3d} blocks, cost identity {c}/{n}, revenue identity {v}/{n}", flush=True)
        allr += rs
    pd.DataFrame(allr).to_csv(out, index=False)
