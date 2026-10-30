"""Non-overlapping era estimates of pyramid-wide G: England (4 tiers, 1958-2024) and Germany (2 tiers, 1981-2024; 2. Bundesliga ran as two regional groups before 1981).
Also distinct top-four finishers and top-four concentration by era. Usage: FR_SRC=<src> python -I trend_eras.py"""
import os, sys, numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(HERE,'..','rcm'))
from trend_eng import G, pairs_of, mfpt
from ladder import eng_ladder, table_from, norm
from clubkey import ck
SRC=os.environ['FR_SRC']; rng=np.random.default_rng(81)
def ger_ladder(lo=1981,hi=2024):
    df=pd.read_csv(f'{SRC}/jalapic_engsoccerdata/data-raw/germany.csv',low_memory=False)
    df=df[(df.tier<=2)&(df.Season>=lo)&(df.Season<=hi)]; out=[]
    for (s,t),g in df.groupby(['Season','tier']):
        tab=table_from(zip(g.home,g.visitor,g.hgoal,g.vgoal),wp=3 if s>=1995 else 2)
        tab['pos']=np.arange(1,len(tab)+1); tab['Season']=s; tab['tier']=t; out.append(tab)
    d=pd.concat(out,ignore_index=True); d['k']=d.club.map(norm); return d
def st_eng(r): return (0 if r.pos<=4 else (1 if r.pos<=10 else 2)) if r.tier==1 else 1+r.tier
def st_ger(r): return (0 if r.pos<=4 else (1 if r.pos<=10 else 2)) if r.tier==1 else 3
def era_G(PR,yrs,K):
    prs=[PR[y] for y in yrs if y in PR]; o,n,g=G(prs,K=K,reps=200); bs=[]
    for _ in range(150):
        pick=rng.integers(0,len(prs),len(prs)); r=G([prs[i] for i in pick],K=K,reps=40)[2]
        if r==r: bs.append(r)
    return o,n,g,np.percentile(bs,2.5),np.percentile(bs,97.5),len(prs)
def top4(lad,yrs):
    t=lad[(lad.tier==1)&(lad.pos<=4)&(lad.Season.isin(yrs))]
    vc=t.k.value_counts(); return t.k.nunique(), vc.head(4).sum()/len(t)
eng=eng_ladder(4,1958,2024); eng['k']=eng.club.map(ck); eng['st']=eng.apply(st_eng,axis=1); PE=pairs_of(eng)
ger=ger_ladder(); ger['st']=ger.apply(st_ger,axis=1); PG=pairs_of(ger)
print("ENGLAND, four tiers. G = MFPT(top-flight 11th-last -> top 4) / permutation null")
print(f"{'era':11s} {'pairs':>5s} {'MFPT':>7s} {'null':>6s} {'G':>6s} {'95% CI':>15s} | {'distinct top-4':>14s} {'share of top-4 places held by 4 most frequent':>45s}")
for a,b in [(1958,1969),(1970,1980),(1981,1991),(1992,2002),(2003,2013),(2014,2023)]:
    yrs=range(a,b+1); o,n,g,lo,hi,np_=era_G(PE,yrs,6); d,sh=top4(eng,range(a,b+2))
    print(f"{a}-{b+1:<6d} {np_:5d} {o:7.1f} {n:6.1f} {g:6.2f} [{lo:5.2f},{hi:5.2f}] | {d:14d} {sh:45.2f}")
print("\nGERMANY, two tiers (K=4)")
for a,b in [(1981,1991),(1992,2002),(2003,2013),(2014,2023)]:
    yrs=range(a,b+1); o,n,g,lo,hi,np_=era_G(PG,yrs,4); d,sh=top4(ger,range(a,b+2))
    print(f"{a}-{b+1:<6d} {np_:5d} {o:7.1f} {n:6.1f} {g:6.2f} [{lo:5.2f},{hi:5.2f}] | {d:14d} {sh:45.2f}")
