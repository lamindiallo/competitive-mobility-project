"""England restricted to two tiers (K=4), era estimates, for like-for-like comparison with Germany. Usage: FR_SRC=<src> python -I trend_eng2.py"""
import os, sys, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(HERE,'..','rcm'))
from trend_eng import pairs_of
from trend_eras import era_G
from ladder import eng_ladder
from clubkey import ck
e2=eng_ladder(2,1958,2024); e2['k']=e2.club.map(ck)
e2['st']=e2.apply(lambda r:(0 if r.pos<=4 else (1 if r.pos<=10 else 2)) if r.tier==1 else 3,axis=1); P2=pairs_of(e2)
for a,b in [(1958,1969),(1970,1980),(1981,1991),(1992,2002),(2003,2013),(2014,2023)]:
    o,n,g,lo,hi,np_=era_G(P2,range(a,b+1),4); print(f"ENG 2-tier {a}-{b+1}: MFPT {o:6.1f} null {n:5.1f} G {g:5.2f} [{lo:.2f},{hi:.2f}]")
