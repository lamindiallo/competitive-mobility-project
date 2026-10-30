"""Sensitivity of the England era pattern to the top-flight boundary rule (four tiers). Point estimates only. Usage: FR_SRC=<src> python -I trend_sens.py"""
import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(HERE,'..','rcm'))
from trend_eng import pairs_of, G
from ladder import eng_ladder
from clubkey import ck
lad=eng_ladder(4,1958,2024); lad['k']=lad.club.map(ck)
rules={'champion | 2-6 | 7-end':(1,6),'top 4 | 5-10 | 11-end (primary)':(4,10),'top 6 | 7-12 | 13-end':(6,12),'top 2 | 3-8 | 9-end':(2,8)}
eras=[(1958,1969),(1970,1980),(1981,1991),(1992,2002),(2003,2013),(2014,2023)]
print(f"{'rule':34s} "+" ".join(f"{a}-{b+1:>4d}" for a,b in eras))
for name,(x,y) in rules.items():
    d=lad.copy(); d['st']=d.apply(lambda r:(0 if r.pos<=x else (1 if r.pos<=y else 2)) if r.tier==1 else 1+r.tier,axis=1); PR=pairs_of(d)
    gs=[G([PR[s] for s in range(a,b+1) if s in PR],K=6,reps=150)[2] for a,b in eras]
    print(f"{name:34s} "+" ".join(f"{g:9.2f}" for g in gs))
