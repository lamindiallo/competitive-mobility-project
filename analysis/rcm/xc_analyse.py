"""Cross-country top-flight resource-conditional statistics, 2006-2022, complete windows (club in tier 1 at s-1 and s-2). Usage: xc_analyse.py xc_panel.csv"""
import sys, numpy as np, pandas as pd, numpy.linalg as la
from scipy.stats import spearmanr, pearsonr
P=pd.read_csv(sys.argv[1]); rng=np.random.default_rng(9)
P=P[P.Season>=2004]
pres=set(zip(P.country,P.ewclub,P.Season))
P['win_ok']=[((c,k,s-1) in pres) and ((c,k,s-2) in pres) for c,k,s in zip(P.country,P.ewclub,P.Season)]
P=P[P.Season>=2006].copy()
P['res']=P.groupby(['country','Season']).R3.rank(ascending=False)
P['res1']=P.groupby(['country','Season']).gin.rank(ascending=False)
P['over']=P.res-P.pos; P['over1']=P.res1-P.pos
def lagc(df,col,lag):
    W=df.pivot_table(index='ewclub',columns='Season',values=col); a=[];b=[]
    for s in W.columns:
        if s+lag in W.columns:
            m=W[s].notna()&W[s+lag].notna(); a+=list(W.loc[m,s]); b+=list(W.loc[m,s+lag])
    return pearsonr(a,b).statistic if len(a)>20 else np.nan
def cycle(df,lead):
    Q=df.pivot_table(index='ewclub',columns='Season',values='res'); R=df.pivot_table(index='ewclub',columns='Season',values='pos')
    OK=df.pivot_table(index='ewclub',columns='Season',values='win_ok'); rows=[]
    for s in Q.columns:
        a,b=(s,s+lead) if lead>0 else (s+lead,s)
        if a in Q.columns and b in Q.columns:
            m=Q[a].notna()&Q[b].notna()&R[s].notna()&(OK[s]==1)
            for k in Q.index[m]: rows.append((k,Q.loc[k,a]-Q.loc[k,b],Q.loc[k,s],R.loc[k,s]))
    D=pd.DataFrame(rows,columns=['k','gain','res','pos'])
    f=lambda D: la.lstsq(np.column_stack([np.ones(len(D)),D.res,D.pos]),D.gain.values,rcond=None)[0][2]
    b=f(D); ks=D.k.unique(); bs=[f(pd.concat([D[D.k==k] for k in rng.choice(ks,len(ks))])) for _ in range(250)]
    lo,hi=np.percentile(bs,[2.5,97.5]); return -b,-hi,-lo
print(f"{'':5s} {'rho':>5s} | {'P(top4 in 5y) by resource rank: 1-4   5-8   9-14  15-20':>52s} | {'persist R1 l1 l3':>17s} | {'cycle fwd [CI]':>20s} {'placebo [CI]':>20s}")
for c in ['ENG','ESP','ITA','GER','FRA']:
    D=P[P.country==c]; S=D[D.win_ok]
    rho=np.mean([spearmanr(g.res,g.pos).statistic for _,g in S.groupby('Season')])
    out=[]
    for s in sorted(D.Season.unique()):
        if s+5>D.Season.max(): continue
        hit=set(D[(D.Season>s)&(D.Season<=s+5)&(D.pos<=4)].ewclub)
        for r in D[(D.Season==s)&D.win_ok].itertuples():
            if r.pos>4: out.append((r.res,r.ewclub in hit))
    O=pd.DataFrame(out,columns=['res','hit'])
    reach=[O[(O.res>=a)&(O.res<b+1)].hit.mean() for a,b in [(1,4),(5,8),(9,14),(15,20)]]
    f=cycle(D,2); p=cycle(D,-2)
    print(f"{c:5s} {rho:5.2f} | {'':14s}"+"  ".join(f"{x:5.2f}" for x in reach)+f" | {lagc(S,'over1',1):+.2f} {lagc(S,'over1',3):+.2f}       | {f[0]:+.2f} [{f[1]:+.2f},{f[2]:+.2f}]  {p[0]:+.2f} [{p[1]:+.2f},{p[2]:+.2f}]")
