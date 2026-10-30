"""Cross-source audit (D213 standard): engsoccerdata vs openfootball/england club sets and final positions, tiers 1-4, 2000/01-2021/22.
Usage: FR_SRC=<src> python -I audit_eng_sources.py"""
import os, sys, numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from ladder import table_from, parse_of, eng_ladder
from clubkey import ck
SRC=os.environ['FR_SRC']
OF_ALIAS={'cheltenham town':'cheltenham','macclesfield town':'macclesfield','chester city':'chester','accrington stanley':'accrington','aldershot town':'aldershot','stevenage':'stevenage borough'}
names={1:['1-premierleague'],2:['2-championship','2-division1'],3:['3-league1','3-division2'],4:['4-league2','4-division3']}
esd=eng_ladder(4,2000,2021); esd['k']=esd.club.map(ck)
tot=0; setmis=[]; posmis=[]; missing=[]
for s in range(2000,2022):
    d=f"{SRC}/openfootball_england/{s}-{str(s+1)[2:]}"
    for t in (1,2,3,4):
        f=next((f"{d}/{n}.txt" for n in names[t] if os.path.exists(f"{d}/{n}.txt")),None)
        if f is None: missing.append((s,t)); continue
        rows=parse_of(f)
        if not rows: missing.append((s,t)); continue
        of=table_from(rows); of['k']=of.club.map(ck).replace(OF_ALIAS); of['pos']=np.arange(1,len(of)+1)
        e=esd[(esd.Season==s)&(esd.tier==t)]
        A=set(e.k); B=set(of.k); tot+=1
        if A!=B: setmis.append((s,t,sorted(A-B),sorted(B-A)))
        else:
            m=e.set_index('k').pos.to_dict(); n=of.set_index('k').pos.to_dict()
            diff=[(k,m[k],n[k]) for k in m if m[k]!=n[k]]
            if diff: posmis.append((s,t,diff))
print(f"tier-seasons compared: {tot}; missing in openfootball: {len(missing)} {missing[:6]}")
print(f"club-set mismatches: {len(setmis)}")
for x in setmis[:40]: print("  ",x)
print(f"same clubs, different positions: {len(posmis)}")
for x in posmis[:15]: print("  ",x)
