"""Identify Companies House downloads whose cover page did not OCR, from the order in which they were downloaded.
The browser recorded the download queue (company number + 'made up to' date, in order). Files are aligned to that
queue in time order by dynamic programming, allowing for failed downloads (queue entries with no file). A file is
assigned only if the year-end date read by OCR from the file itself equals the queue entry's date, and any company
number OCR did read agrees. Agreement on files OCR did identify is reported as the method's check.
Usage: python -I ch_manifest_align.py <ch_ocr.csv> <pass1_order.txt> <manifest23.txt> <out.csv>"""
import sys, re, json
import numpy as np, pandas as pd

MONTHS = {m: i for i, m in enumerate(['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
                                      'september', 'october', 'november', 'december'], 1)}

def ocr_ye(t):
    if not isinstance(t, str): return None
    m = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', t)
    if not m or m.group(2).lower() not in MONTHS: return None
    return (int(m.group(3)) % 100, MONTHS[m.group(2).lower()])

def ocr_co(cell, known):
    try: c = json.loads(cell) if isinstance(cell, str) and cell.startswith('[') else []
    except Exception: c = []
    for x, _ in c:
        s = re.sub(r'\D', '', str(x)).zfill(8)
        if s in known: return s
    return None

def align(files, queue, ev):
    """Needleman-Wunsch: files (time order) vs queue (download order). ev[f] = (co, ye)."""
    n, m = len(files), len(queue); NEG = -1e9
    S = np.full((n + 1, m + 1), NEG); S[0, :] = -1.0 * np.arange(m + 1); S[:, 0] = -2.0 * np.arange(n + 1)
    bt = np.zeros((n + 1, m + 1), dtype=np.int8)
    def sc(f, q):
        co, ye = ev[f]; s = 0.5
        if co: s += 3 if co == q[0] else -6
        if ye: s += 3 if ye == q[1] else -4
        return s
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            opts = (S[i - 1, j - 1] + sc(files[i - 1], queue[j - 1]), S[i, j - 1] - 1.0, S[i - 1, j] - 2.0)
            k = int(np.argmax(opts)); S[i, j] = opts[k]; bt[i, j] = k
    i, j, pairs = n, m, []
    while i > 0 and j > 0:
        k = bt[i, j]
        if k == 0: pairs.append((i - 1, j - 1)); i -= 1; j -= 1
        elif k == 1: j -= 1
        else: i -= 1
    pairs = pairs[::-1]
    # local repair: downloads that finished out of order are skipped by a monotone alignment. An unmatched file may take
    # an unmatched queue entry lying between its matched neighbours' entries (±3), if the OCR year-end matches and the
    # candidate is unique.
    fi = {a: b for a, b in pairs}; used = set(fi.values())
    for a in range(n):
        if a in fi or not ev[files[a]][1]: continue
        lo = max([fi[x] for x in fi if x < a], default=0) - 3; hi = min([fi[x] for x in fi if x > a], default=m) + 3
        co, ye = ev[files[a]]
        c = [j for j in range(max(lo, 0), min(hi, m - 1) + 1) if j not in used and queue[j][1] == ye and (co is None or queue[j][0] == co)]
        if len(c) == 1: fi[a] = c[0]; used.add(c[0])
    return [(files[a], queue[b]) for a, b in sorted(fi.items())]

if __name__ == '__main__':
    ocr, p1, m23, out = sys.argv[1:5]
    D = pd.read_csv(ocr)
    q1 = [(a.zfill(8), (int(b[:2]), int(b[2:]))) for a, b in (x.split(':') for x in open(p1).read().strip().split(','))]
    q23 = [(x[:8], (int(x[8:10]), int(x[10:12]))) for x in open(m23).read().strip().split(',') if x]
    known = {c for c, _ in q1 + q23}
    ev = {r.file: (ocr_co(r.company_no, known), ocr_ye(r.year_end)) for r in D.itertuples()}
    num = sorted([f for f in ev if re.match(r'companies_house_document \((\d+)\)\.pdf$', f)], key=lambda f: int(re.search(r'\((\d+)\)', f).group(1)))
    num = [f for f in num if int(re.search(r'\((\d+)\)', f).group(1)) >= 8]
    ts = sorted([f for f in ev if f.startswith('companies_house_document - ')], key=lambda f: re.search(r' - ([\d-]+T[\d.]+)\.pdf', f).group(1))
    pairs = align(num, q1[:93], ev) + align(ts, q1[93:] + q23, ev)
    rows = []
    for f, (co, (yy, mm)) in pairs:
        oco, oye = ev[f]
        ok = (oye == (yy, mm)) and (oco is None or oco == co)
        rows.append(dict(file=f, queue_company=co, queue_made_up=f'20{yy:02d}-{mm:02d}', ocr_company=oco,
                         ocr_ye=None if not oye else f'20{oye[0]:02d}-{oye[1]:02d}', confirmed=ok))
    R = pd.DataFrame(rows); R.to_csv(out, index=False)
    chk = R[R.ocr_company.notna()]
    print(f'{len(R)} files aligned of {len(num) + len(ts)}; queue entries {93 + len(q1) - 93 + len(q23)}')
    print(f'check on OCR-identified files: company agrees {int((chk.ocr_company == chk.queue_company).sum())}/{len(chk)}; '
          f'year-end agrees {int((chk.ocr_ye == chk.queue_made_up).sum())}/{int(chk.ocr_ye.notna().sum())}')
    un = R[R.ocr_company.isna()]
    print(f'files without an OCR company number: {len(un)}; confirmed by year-end: {int(un.confirmed.sum())}')
