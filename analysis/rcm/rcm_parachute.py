"""Classify large climbs (>=10 ladder places in 3 seasons) by whether resource rank rose and whether the club was parachute-eligible at the start.
Parachute-eligible = in tier 2 at s and in the Premier League in any of s-1..s-3. Usage: FR_SRC=<src> python -I rcm_parachute.py panel.csv"""
import pandas as pd, os, sys
sys.path.insert(0,os.path.dirname(__file__))
from ladder import eng_ladder
from clubkey import ck
lad=eng_ladder(2,1998,2022); lad['k']=lad.club.map(ck)
inPL=set(zip(lad[lad.tier==1].k,lad[lad.tier==1].Season))
P=pd.read_csv(sys.argv[1])
P['parachute']=[(t==2) and any((k,s-j) in inPL for j in (1,2,3)) for k,s,t in zip(P.k,P.Season,P.tier)]
P.to_csv(sys.argv[1],index=False)
R=P.pivot_table(index='k',columns='Season',values='rank'); Q=P.pivot_table(index='k',columns='Season',values='res_rank')
PA=P.pivot_table(index='k',columns='Season',values='parachute'); OK=P.pivot_table(index='k',columns='Season',values='win_ok')
for restrict in (False,True):
    ep=[]
    for s in R.columns:
        if s+3 in R.columns:
            m=R[s].notna()&R[s+3].notna()&Q[s].notna()&Q[s+3].notna()
            if restrict: m=m&(OK[s]==1)&(OK[s+3]==1)
            for k in R.index[m]:
                dr=R.loc[k,s]-R.loc[k,s+3]; dq=Q.loc[k,s]-Q.loc[k,s+3]
                if dr>=10: ep.append((k,s,dr,dq,bool(PA.loc[k,s]==1)))
    E=pd.DataFrame(ep,columns=['club','start','climb','res_change','parachute_at_start'])
    nores=E[E.res_change<=0]
    print(f"{'RESTRICTED' if restrict else 'FULL'}: climbs {len(E)}; no resource gain {len(nores)}; of which parachute {nores.parachute_at_start.sum()}; CLEAN {(~nores.parachute_at_start).sum()}")
    print(nores[~nores.parachute_at_start].to_string(index=False))
