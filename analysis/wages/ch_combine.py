"""Combine the first OCR pass with the rescan (CH_LOW_DPI=130, CH_START_FRAC=0.15) of files whose staff page was not found.
A rescan row replaces the first-pass row only if it found a staff page; identification fields fall back to the first pass.
Usage: python -I ch_combine.py <ch_ocr.csv> <ch_rescan.csv> <out.csv>"""
import sys
import pandas as pd

a, b, out = sys.argv[1:4]
A = pd.read_csv(a); B = pd.read_csv(b)
B = B[B.staff_page.notna()].set_index('file')
A = A.set_index('file')
n = 0
for f, r in B.iterrows():
    if f not in A.index: continue
    keep = {c: A.at[f, c] for c in ('company_no', 'year_end') if pd.isna(r.get(c)) or r.get(c) in ('[]', '')}
    for c in B.columns:
        if c in A.columns: A.at[f, c] = r[c]
    for c, v in keep.items(): A.at[f, c] = v
    A.at[f, 'rescanned'] = True; n += 1
A.reset_index().to_csv(out, index=False)
print(f'{n} rows replaced from the rescan; {len(A)} rows written')
