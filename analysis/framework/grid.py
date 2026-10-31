import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from depth import eng_ladder, trans, fp
from run5b import lads

SPECS={
 'top4 | 5-10 | 11-20   (prize, K=3)':      ([4,10],),
 'top1 | 2-6 | 7-20     (title-focused)':   ([1,6],),
 'top6 | 7-13 | 14-20   (equal thirds)':    ([6,13],),
 'top4 | 5-8 | 9-14 | 15-20  (K=4)':        ([4,8,14],),
}
def statef(bounds,pyramid):
    def f(r):
        if r.tier!=1: return len(bounds)+1
        for i,b in enumerate(bounds):
            if r.pos<=b: return i
        return len(bounds)
    return f

print("="*92)
print("F. IS THE 2.54 FACTOR SPECIFICATION-DEPENDENT?   tiers 1-2, 1992-2024, source = lowest tier-1 state")
print("="*92)
print(f"{'specification':38s} " + ' '.join(f'{c:>9s}' for c in ['ENG','ESP','ITA','GER','FRA']))
allr=[]
for name,(bounds,) in SPECS.items():
    row=[]
    for c in ['ENG','ESP','ITA','GER','FRA']:
        l=lads[c]
        nb=len(bounds)          # index of lowest tier-1 state
        t=fp(trans(l[l.tier==1],statef(bounds,False),nb+1),nb,0)
        p=fp(trans(l,statef(bounds,True),nb+2),nb,0)
        row.append(p/t); allr.append(p/t)
    print(f"{name:38s} " + ' '.join(f'{x:9.2f}' for x in row))
print("-"*92)
print(f"{'ALL SPECIFICATIONS, ALL COUNTRIES':38s}  mean {np.mean(allr):.2f}   sd {np.std(allr,ddof=1):.2f}   range {min(allr):.2f}-{max(allr):.2f}   n={len(allr)}")
