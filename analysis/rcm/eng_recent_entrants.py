"""England's recent top-four outsider entries, using eordo/transfermarkt-data (Premier League transfers to 2025/26) to extend the
resource proxy past ewenme's 2022/23 end. Step 1 cross-checks the two transfer sources on overlapping club-seasons.
Usage: FR_SRC=<src> python -I eng_recent_entrants.py"""
import os, sys, glob, numpy as np, pandas as pd
from scipy.stats import spearmanr
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from clubkey import ck
from ladder import eng_ladder
SRC=os.environ['FR_SRC']
E=pd.concat([pd.read_csv(f) for f in glob.glob(f'{SRC}/eordo_transfermarkt-data/premier_league/*.csv')])
E['k']=E.club.map(ck); E['fee']=pd.to_numeric(E.fee,errors='coerce').fillna(0)/1e6
ein=E[E.movement=='in']; g_e=ein.groupby(['k','season']).fee.sum(); g_es=ein[ein.window=='summer'].groupby(['k','season']).fee.sum()
W=pd.read_csv(f'{SRC}/ewenme_transfers/data/premier-league.csv'); W['season']=W.season.str[:4].astype(int); W['k']=W.club_name.map(ck)
W['fee']=pd.to_numeric(W.fee_cleaned,errors='coerce').fillna(0); g_w=W[W.transfer_movement=='in'].groupby(['k','season']).fee.sum()
both=pd.concat([g_e.rename('eordo'),g_w.rename('ewenme')],axis=1).dropna()
both=both[(both.index.get_level_values(1)>=2006)&(both.index.get_level_values(1)<=2021)]
rhos=[spearmanr(g.eordo,g.ewenme).statistic for _,g in both.groupby(level=1)]
print(f"[cross-check] PL club-season gross spend, 2006-2021: within-season Spearman rho mean {np.mean(rhos):.3f} (min {min(rhos):.3f}); n={len(both)}")
lad=eng_ladder(1,2016,2024); lad['k']=lad.club.map(ck)
rows=[]
for s in range(2018,2025):
    clubs=lad[lad.Season==s].k
    R3={k:float(g_es.get((k,s),0))+float(g_e.get((k,s-1),0))+float(g_e.get((k,s-2),0)) for k in clubs}
    rk=pd.Series(R3).rank(ascending=False)
    for k in clubs: rows.append((k,s,rk[k],R3[k]))
P=pd.DataFrame(rows,columns=['k','Season','res','R3'])
P=P.merge(lad[['k','Season','pos']],on=['k','Season'])
top=set(zip(lad[lad.pos<=4].k,lad[lad.pos<=4].Season))
full=eng_ladder(1,2005,2024); full['k']=full.club.map(ck); topall=set(zip(full[full.pos<=4].k,full[full.pos<=4].Season))
print("\nTop-four entries 2019/20-2024/25 (England), resource rank on eordo R3:")
for r in P[P.pos<=4].sort_values('Season').itertuples():
    if (r.k,r.Season-1) in topall: continue
    out=not any((r.k,r.Season-j) in topall for j in range(2,11))
    prev=P[(P.k==r.k)&(P.Season==r.Season-3)]
    gain=(prev.res.iloc[0]-r.res) if len(prev) else np.nan
    print(f"  {r.Season}/{str(r.Season+1)[2:]}  {r.k:22s} finish {int(r.pos)}  resource rank {int(r.res):2d}  3-season resource-rank gain {gain:+.0f}  outsider={out}  R3=EUR {r.R3:.0f}m")
