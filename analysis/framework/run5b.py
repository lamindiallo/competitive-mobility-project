import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from names import *
from alias import ALIAS
from flow import build, key
from patch import parse_of, table_from
import numpy as np, pandas as pd
from run5 import mfpt, esd_ladder, G, t1only, pyr, counts

# --- patch England 2022 (tiers 1-2) from openfootball ---
def eng_2022():
    out=[]
    for f,t in [('1-premierleague',1),('2-championship',2)]:
        tab=table_from(parse_of(f'/tmp/of_eng/2022-23/{f}.txt'))
        tab['pos']=np.arange(1,len(tab)+1); tab['Season']=2022; tab['tier']=t
        out.append(tab[['club','Season','tier','pos']])
    d=pd.concat(out,ignore_index=True); d['k']=[norm(x) for x in d.club]; return d

# --- patch France 1994 tier 1 from schochastics parquet ---
def fra_1994():
    d=pd.read_parquet('/tmp/schochastics_football-data/data/results/games.parquet')
    f=d[d.competition=='france'].copy(); f['date']=pd.to_datetime(f['date'],errors='coerce')
    f['yr']=f['date'].dt.year-(f['date'].dt.month<7).astype(int)
    g=f[f.yr==1994]
    r={}
    for _,x in g.iterrows():
        for tm,gf,ga in ((x.home,x.gh,x.ga),(x.away,x.ga,x.gh)):
            d_=r.setdefault(tm,[0,0,0]); d_[0]+=(3 if gf>ga else (1 if gf==ga else 0)); d_[1]+=gf-ga; d_[2]+=gf
    t=pd.DataFrame([(k,*v) for k,v in r.items()],columns=['club','Pts','GD','GF'])
    t=t.sort_values(['Pts','GD','GF'],ascending=False).reset_index(drop=True)
    t['pos']=np.arange(1,len(t)+1); t['Season']=1994; t['tier']=1
    t['k']=[key('fr',x) for x in t.club]
    return t[['club','Season','tier','pos','k']]

lads={}
for c,f,cc in [('fr','france','FRA'),('es','spain','ESP'),('it','italy','ITA')]:
    lads[cc]=build(c,f)
for c,f,cc in [('eng','england','ENG'),('de','germany','GER')]:
    lads[cc]=esd_ladder(c,f'/tmp/fr/{f}.csv')
lads['ENG']=pd.concat([lads['ENG'],eng_2022()],ignore_index=True)
lads['FRA']=pd.concat([lads['FRA'],fra_1994()],ignore_index=True)

for c in lads:
    l=lads[c]
    print(c,'seasons t1:',len(set(l[l.tier==1].Season)),'t2:',len(set(l[l.tier==2].Season)))

def report():
    print("\n"+"="*84); print("A. TIER-1-ONLY (truncated at the divisional boundary)"); print("="*84)
    print(f"{'country':8s} {'pairs':>6s} {'obs MFPT':>9s} {'null':>7s} {'G':>7s}")
    res={}
    for c in ['ENG','ESP','ITA','GER','FRA']:
        l=lads[c]; r=G(l[l.tier==1],t1only,3,2,0); res[c]={'trunc':r}
        print(f"{c:8s} {r[3]:6d} {r[0]:9.2f} {r[1]:7.2f} {r[2]:7.2f}")
    print("\n"+"="*84); print("B. PYRAMID-WIDE (tiers 1-2) — ALL FIVE"); print("="*84)
    print(f"{'country':8s} {'pairs':>6s} {'obs MFPT':>9s} {'null':>7s} {'G':>7s}")
    for c in ['ENG','ESP','ITA','GER','FRA']:
        r=G(lads[c],pyr,4,2,0); res[c]['pyr']=r
        print(f"{c:8s} {r[3]:6d} {r[0]:9.2f} {r[1]:7.2f} {r[2]:7.2f}")
    print("\n"+"="*84); print("C. TRUNCATION BIAS, LIKE-FOR-LIKE"); print("="*84)
    print(f"{'country':8s} {'truncated':>10s} {'pyramid':>9s} {'ratio':>7s}")
    rs=[]
    for c in ['ENG','ESP','ITA','GER','FRA']:
        a=res[c]['trunc'][0]; b=res[c]['pyr'][0]; rs.append(b/a)
        print(f"{c:8s} {a:10.2f} {b:9.2f} {b/a:7.2f}")
    print(f"{'MEAN':8s} {'':10s} {'':9s} {np.mean(rs):7.2f}   sd={np.std(rs,ddof=1):.2f}  range {min(rs):.2f}-{max(rs):.2f}")
    return res
res=report()

import os
os.makedirs('/tmp/fr/03/ladders',exist_ok=True)
for c in ['ENG','ESP','ITA','GER','FRA']:
    lads[c].sort_values(['Season','tier','pos']).to_csv(f'/tmp/fr/03/ladders/ladder_{c}.csv',index=False)
    print(c, len(lads[c]))
