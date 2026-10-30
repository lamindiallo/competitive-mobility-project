"""Falsification test for the virtuous cycle: does over-performance at t predict resource-rank change FORWARD (t->t+2) but not BACKWARD (t-2->t)?
Controls: resource rank at t, PL membership at t. Club-cluster bootstrap. Usage: python -I rcm_placebo.py panel.csv"""
import sys, pandas as pd, numpy as np, numpy.linalg as la
P=pd.read_csv(sys.argv[1]); rng=np.random.default_rng(3)
Q=P.pivot_table(index='k',columns='Season',values='res_rank'); R=P.pivot_table(index='k',columns='Season',values='rank')
T=P.pivot_table(index='k',columns='Season',values='tier'); OK=P.pivot_table(index='k',columns='Season',values='win_ok')
X=P.copy(); X['rr1']=X.groupby('Season').gin.rank(ascending=False); Q1=X.pivot_table(index='k',columns='Season',values='rr1')
def run(Qm,lead):
    rows=[]
    for s in Qm.columns:
        a,b=(s,s+lead) if lead>0 else (s+lead,s)
        if a in Qm.columns and b in Qm.columns:
            m=Qm[a].notna()&Qm[b].notna()&R[s].notna()&Qm[s].notna()&(OK[s]==1)
            for k in Qm.index[m]: rows.append((k,Qm.loc[k,a]-Qm.loc[k,b],Qm.loc[k,s],R.loc[k,s],float(T.loc[k,s]==1)))
    D=pd.DataFrame(rows,columns=['k','gain','res','rank','pl'])
    f=lambda D: la.lstsq(np.column_stack([np.ones(len(D)),D.res,D['rank'],D.pl]),D.gain.values,rcond=None)[0][2]
    b=f(D); ks=D.k.unique(); bs=[f(pd.concat([D[D.k==k] for k in rng.choice(ks,len(ks))])) for _ in range(300)]
    lo,hi=np.percentile(bs,[2.5,97.5]); return -b,-hi,-lo,len(D)
for name,Qm in [('R3',Q),('R1',Q1)]:
    f=run(Qm,2); p=run(Qm,-2)
    print(f"{name}: forward {f[0]:+.2f} [{f[1]:+.2f},{f[2]:+.2f}]   placebo {p[0]:+.2f} [{p[1]:+.2f},{p[2]:+.2f}]")
