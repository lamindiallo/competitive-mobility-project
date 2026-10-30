"""Prototype per-club values, England tiers 1-4, 1992/93-2024/25 (results-based) + interim proxy-based ranks (D207 working rule: ranks only).
Usage: FR_SRC=<src> python -I club_values_eng.py <rcm_panel.csv> <outdir>"""
import os, sys, numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(HERE,'..','rcm')); sys.path.insert(0,os.path.join(HERE,'..','trend'))
from ladder import eng_ladder
from clubkey import ck
from trend_eng import state, mfpt
lad=eng_ladder(4,1992,2024); lad['k']=lad.club.map(ck); lad['st']=lad.apply(state,axis=1)
last=lad.Season.max()
# league-level transition matrix 2014-2024 (latest era) for "expected wait from where the club stands now"
ss=sorted(lad.Season.unique()); C=np.zeros((6,6))
for a,b in zip(ss,ss[1:]):
    if a<2014: continue
    A=lad[lad.Season==a].drop_duplicates('k').set_index('k').st; B=lad[lad.Season==b].drop_duplicates('k').set_index('k').st
    ix=A.index.intersection(B.index); np.add.at(C,(A[ix].values.astype(int),B[ix].values.astype(int)),1)
P=C/C.sum(1,keepdims=True); wait={i:(0.0 if i==0 else mfpt(P,i,0)) for i in range(6)}
STATE_NAME={0:'Top-flight top 4',1:'Top flight 5th-10th',2:'Top flight 11th-last',3:'Tier 2',4:'Tier 3',5:'Tier 4'}
rows=[]
for k,g in lad.groupby('k'):
    g=g.sort_values('Season'); name=g.club.iloc[-1]
    r=g.set_index('Season')['rank']
    best5=None
    for s in r.index:
        if s+5 in r.index:
            d=r[s]-r[s+5]
            if best5 is None or d>best5[0]: best5=(d,s)
    moves=[abs(r[s+1]-r[s]) for s in r.index if s+1 in r.index]
    cur=g[g.Season==last]
    rows.append(dict(club=name,key=k,seasons=len(g),
        seasons_t1=int((g.tier==1).sum()),seasons_t2=int((g.tier==2).sum()),seasons_t3=int((g.tier==3).sum()),seasons_t4=int((g.tier==4).sum()),
        top4_finishes=int(((g.tier==1)&(g.pos<=4)).sum()),titles=int(((g.tier==1)&(g.pos==1)).sum()),
        peak_rank=int(r.min()),peak_season=f"{int(r.idxmin())}/{str(int(r.idxmin())+1)[2:]}",floor_rank=int(r.max()),
        best_5yr_climb=int(best5[0]) if best5 else np.nan,best_5yr_climb_from=f"{best5[1]}/{str(best5[1]+1)[2:]}" if best5 else '',
        mean_abs_move=round(float(np.mean(moves)),2) if moves else np.nan,
        current_season=f"{last}/{str(last+1)[2:]}" if len(cur) else '',
        current_state=STATE_NAME[int(cur.st.iloc[0])] if len(cur) else 'outside the four tiers',
        expected_wait_top4_from_current=round(wait[int(cur.st.iloc[0])],1) if len(cur) else np.nan))
V=pd.DataFrame(rows)
# interim proxy-based: mean over-performance (resource rank - ladder rank), England tiers 1-2, 2006-2022, complete windows, >=5 club-seasons
R=pd.read_csv(sys.argv[1]); R=R[R.win_ok]
op=R.groupby('k').over.agg(['mean','size','std']); op=op[op['size']>=5]
op['se']=op['std']/np.sqrt(op['size'])
V=V.merge(op[['mean','size','se']].rename(columns={'mean':'beat_money_mean_places','size':'beat_money_seasons','se':'beat_money_se'}),left_on='key',right_index=True,how='left')
V['beat_money_mean_places']=V.beat_money_mean_places.round(1); V['beat_money_se']=V.beat_money_se.round(1)
V=V.sort_values(['seasons_t1','top4_finishes','seasons'],ascending=False)
out=sys.argv[2]; V.to_csv(f'{out}/england_club_values_prototype.csv',index=False)
print(f"clubs: {len(V)}   expected wait to top four by current state (2014-24 matrix): "+", ".join(f"{STATE_NAME[i]} {wait[i]:.0f}" for i in range(1,6)))
pd.set_option('display.width',250); pd.set_option('display.max_columns',30)
print(V[['club','seasons_t1','top4_finishes','titles','peak_rank','best_5yr_climb','best_5yr_climb_from','current_state','expected_wait_top4_from_current','beat_money_mean_places','beat_money_se','beat_money_seasons']].head(25).to_string(index=False))
print("\nTop 10 by 'beat the money' (interim proxy, >=5 complete-window seasons):")
print(V.dropna(subset=['beat_money_mean_places']).sort_values('beat_money_mean_places',ascending=False)[['club','beat_money_mean_places','beat_money_se','beat_money_seasons']].head(10).to_string(index=False))
print("\nBottom 5:"); print(V.dropna(subset=['beat_money_mean_places']).sort_values('beat_money_mean_places')[['club','beat_money_mean_places','beat_money_se','beat_money_seasons']].head(5).to_string(index=False))
