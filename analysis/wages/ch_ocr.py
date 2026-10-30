"""OCR Companies House statutory accounts (scanned PDFs) and extract staff costs and turnover.
Deterministic: Tesseract OCR, no language model reads any figure (D253). Every staff-cost figure must satisfy the
note's own identity (components sum to the printed total) or it is not used.
Usage: python -I ch_ocr.py <pdf_dir> <out_csv> [workers] [file_list.txt]
Rescan settings (for files whose staff page was not found): CH_LOW_DPI (default 80), CH_START_FRAC (default 0.3)."""
import sys, os, re, glob, json, subprocess, tempfile
os.environ.setdefault("OMP_THREAD_LIMIT", "1")
from concurrent.futures import ProcessPoolExecutor

LOW_DPI = int(os.environ.get("CH_LOW_DPI", 80)); START_FRAC = float(os.environ.get("CH_START_FRAC", 0.3))
NUM = r'\(?-?\d{1,3}(?:,\d{3})+\)?|\(?-?\d{1,4}\)?'

def ocr_pages(pdf, dpi, first=None, last=None):
    with tempfile.TemporaryDirectory() as td:
        cmd = ['pdftoppm', '-r', str(dpi), '-gray']
        if first: cmd += ['-f', str(first), '-l', str(last)]
        subprocess.run(cmd + [pdf, f'{td}/p'], capture_output=True)
        out = {}
        for fn in sorted(glob.glob(f'{td}/p-*.pgm')):
            n = int(re.search(r'-(\d+)\.pgm$', fn).group(1))
            out[n] = subprocess.run(['tesseract', fn, '-', '--psm', '6'], capture_output=True, text=True).stdout
        return out

def tonum(s):
    neg = s.startswith('(') or s.startswith('-')
    v = int(re.sub(r'[^\d]', '', s)); return -v if neg else v

def nums(line):
    line = re.sub(r'\((?:note|notes)\s*\d+[a-z]?\)|note\s*\d+', ' ', line, flags=re.I)   # note references are not amounts
    out = []
    for x in re.findall(NUM, line):
        d = re.sub(r'[^\d]', '', x)
        if d and (',' in x or len(d) >= 3): out.append(tonum(x))
    return out

def staff_block(text):
    """Return (components, total) for the first year column of the staff-costs note, plus the prior-year column."""
    L = text.splitlines()
    for i, l in enumerate(L):
        if not re.search(r'wages,?\s+(?:and\s+)?salar', l, re.I): continue
        comp, comp_p = [], []
        j = i
        while j < min(i + 10, len(L)):
            ln = L[j]
            if re.search(r'wages,?\s+(?:and\s+)?salar|social security|pension|defined contribution|benefits? in kind|other employment|other (staff|employee)|termination|share[- ]based|severance|long[- ]term incentive|national insurance|redundancy|compensation for loss', ln, re.I):
                v = nums(ln)
                if v: comp.append(v[0]); comp_p.append(v[1] if len(v) > 1 else None)
            elif comp and re.search(r'\d{1,3},\d{3}', ln) and not re.search(r'[a-z]{4,}', ln, re.I):
                v = nums(ln)                                         # the unlabelled total line
                if v: return dict(components=comp, total=v[0], prior_components=comp_p, prior_total=v[1] if len(v) > 1 else None, line=i)
            j += 1
        if comp: return dict(components=comp, total=None, prior_components=comp_p, prior_total=None, line=i)
    return None

def find_turnover(texts):
    for n in sorted(texts):
        for l in texts[n].splitlines():
            if re.match(r'\s*(turnover|revenue)\b', l, re.I):
                v = [x for x in nums(l) if abs(x) >= 1000 and not (1990 <= abs(x) <= 2030)]
                if v: return v[0], (v[1] if len(v) > 1 else None), n
    return None, None, None

def cover(texts):
    """Company-number candidates and year-end dates found anywhere in the document (resolved later against the club list)."""
    from collections import Counter
    t = ' '.join(texts[n] for n in sorted(texts))
    near = re.findall(r'(?:company|registered|registration)[^\n]{0,40}?(?:number|no\.?)[^\d\n]{0,10}([0-9OS]{6,8})', t, re.I)
    anyn = re.findall(r'\b(0\d{7})\b', t)
    cands = Counter([x.replace('O', '0').replace('S', '5').zfill(8) for x in near] * 3 + anyn)
    ye = Counter(re.sub(r'\s+', ' ', m) for m in re.findall(r'(?:year|period)\s+ended\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})', t, re.I))
    return json.dumps(cands.most_common(5)), (ye.most_common(1)[0][0] if ye else None)

def npages(pdf):
    out = subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout
    m = re.search(r'Pages:\s+(\d+)', out); return int(m.group(1)) if m else 0

def page(pdf, n, dpi):
    return ocr_pages(pdf, dpi, n, n).get(n, '')

def process(pdf):
    N = npages(pdf)
    res = dict(file=os.path.basename(pdf), pages=N, staff_page=None)
    head = ocr_pages(pdf, 150, 1, min(N, 2))                                  # identity from the cover
    lo_start = max(1, int(N * START_FRAC))
    low = ocr_pages(pdf, LOW_DPI, lo_start, N)                                    # one batch over the back 70%
    co, ye = cover(head)
    if not ye or not co:
        co2, ye2 = cover({**head, **low}); co = co or co2; ye = ye or ye2
    res.update(company_no=co, year_end=ye)
    strong = [n for n in sorted(low) if re.search(r'wages\s+(?:and|ond|an|&)\s|wages,\s+salar', low[n], re.I)]
    weak = [n for n in sorted(low) if n not in strong and re.search(r'social\s+sec|pension\s+costs|staff\s+costs|payroll\s+costs|employee\s+(?:costs|benefit)|wages', low[n], re.I)]
    for n in (strong + weak)[:5]:
        hi = page(pdf, n, 300)
        b = staff_block(hi)
        if not b: continue
        ok = b['total'] is not None and abs(sum(b['components']) - b['total']) <= 2
        okp = b['prior_total'] is not None and None not in b['prior_components'] and abs(sum(b['prior_components']) - b['prior_total']) <= 2
        hl = '\n'.join(hi.splitlines()[max(0, b['line'] - 6): b['line'] + 1])
        unit = 'GBP_k' if re.search(r"£\s*'?000|£000|£'000|£ thousand", hl, re.I) else ('GBP' if re.search(r'£', hl) else 'unknown')
        res.update(staff_unit=unit, staff_page=n, staff_components=json.dumps(b['components']), staff_total=b['total'], staff_ok=ok,
                   prior_components=json.dumps(b['prior_components']), prior_total=b['prior_total'], prior_ok=okp,
                   staff_text=re.sub(r'\s+', ' ', '\n'.join(hi.splitlines()[max(0, b['line'] - 3): b['line'] + 9]))[:600])
        if ok and okp: break
    tv = tvp = tp = None
    for n in sorted(low):
        if n > lo_start + int(N * 0.25): break
        t = low[n]
        if re.search(r'(profit and loss account|income statement|statement of (?:comprehensive )?income)', t, re.I) and re.search(r'\b(turnover|revenue)\b', t, re.I):
            tv, tvp, tp = find_turnover({n: page(pdf, n, 250)})
            if tv: break
    res.update(turnover=tv, turnover_prior=tvp, turnover_page=tp)
    return res

if __name__ == '__main__':
    import pandas as pd
    pdf_dir, out = sys.argv[1], sys.argv[2]; w = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    prior = pd.read_csv(out) if os.path.exists(out) else pd.DataFrame()
    done = set(prior.file) if len(prior) else set()
    only = set(open(sys.argv[4]).read().split('\n')) if len(sys.argv) > 4 else None
    pdfs = [p for p in sorted(glob.glob(os.path.join(pdf_dir, '*.pdf'))) if os.path.basename(p) not in done and (only is None or os.path.basename(p) in only)]
    rows = []
    with ProcessPoolExecutor(w) as ex:
        for r in ex.map(process, pdfs):
            rows.append(r); print(json.dumps({k: r.get(k) for k in ('file', 'company_no', 'year_end', 'staff_total', 'staff_ok', 'prior_total', 'prior_ok', 'turnover')}), flush=True)
            pd.concat([prior, pd.DataFrame(rows)], ignore_index=True).to_csv(out, index=False)
