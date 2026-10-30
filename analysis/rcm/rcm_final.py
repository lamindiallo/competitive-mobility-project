"""Resource-Conditional Mobility, England tiers 1-2, interim transfer-spend proxy. Usage: rcm_final.py panel.csv [restricted]"""
import sys, numpy as np, pandas as pd
from scipy.stats import spearmanr, pearsonr
import numpy.linalg as la
P=pd.read_csv(sys.argv[1]); RESTRICT=len(sys.argv)>2; rng=np.random.default_rng(5)
ok=P.win_ok if RESTRICT else pd.Series(True,index=P.index)
print(f"#### SAMPLE: {'complete resource windows only' if RESTRICT else 'all club-seasons'}  (n={ok.sum()})")
S=P[ok]
rs=[spearmanr(g.res_rank,g['rank']).statistic for _,g in S.groupby('Season')]
r1=[spearmanr(g.res_rank,g['rank']).statistic for _,g in S[S.tier==1].groupby('Season')]
r2=[spearmanr(g.res_rank,g['rank']).statistic for _,g in S[S.tier==2].groupby('Season')]
print(f"[1] rho ladder {np.mean(rs):.3f} | within PL {np.mean(r1):.3f} | within Championship {np.mean(r2):.3f}")
def lagc(df,col,lag):
    W=df.pivot_table(index='k',columns='Season',values=col); a=[];b=[]
    for s in W.columns:
        if s+lag in W.columns:
            m=W[s].notna()&W[s+lag].notna(); a+=list(W.loc[m,s]); b+=list(W.loc[m,s+lag])
    return pearsonr(a,b).statistic
X=P.copy(); X['rr1']=X.groupby('Season').gin.rank(ascending=False); X['ov1']=X.rr1-X['rank']
print("[2] persistence  R3: "+"  ".join(f"lag{l} {lagc(S,'over',l):+.2f}" for l in (1,2,3,5))+
      "   | R1: "+"  ".join(f"lag{l} {lagc(X[ok],'ov1',l):+.2f}" for l in (1,2,3,5)))
R=P.pivot_table(index='k',columns='Season',values='rank'); Q=P.pivot_table(index='k',columns='Season',values='res_rank')
OK=P.pivot_table(index='k',columns='Season',values='win_ok')
ep=[]
for s in R.columns:
    if s+3 in R.columns:
        m=R[s].notna()&R[s+3].notna()&Q[s].notna()&Q[s+3].notna()
        if RESTRICT: m=m&(OK[s]==1)&(OK[s+3]==1)
        for k in R.index[m]:
            dr=R.loc[k,s]-R.loc[k,s+3]; dq=Q.loc[k,s]-Q.loc[k,s+3]
            if dr>=10: ep.append((k,s,int(dr),dq))
E=pd.DataFrame(ep,columns=['club','start','climb','res_change'])
print(f"[3] climbs>=10 in 3 seasons: {len(E)}; with NO resource-rank gain: {(E.res_change<=0).sum()} ({(E.res_change<=0).mean():.0%}); resource gain < half the climb: {(E.res_change<E.climb/2).mean():.0%}")
print(E[E.res_change<=0].sort_values('climb',ascending=False).to_string(index=False))
T=P.pivot_table(index='k',columns='Season',values='tier'); rows=[]
for s in Q.columns:
    if s+2 in Q.columns:
        m=Q[s].notna()&Q[s+2].notna()&R[s].notna()
        if RESTRICT: m=m&(OK[s]==1)&(OK[s+2]==1)
        for k in Q.index[m]: rows.append((k,Q.loc[k,s]-Q.loc[k,s+2],Q.loc[k,s],R.loc[k,s],float(T.loc[k,s]==1)))
D=pd.DataFrame(rows,columns=['k','gain','res','rank','pl'])
def ols(D,cols):
    Xm=np.column_stack([np.ones(len(D))]+[D[c].values for c in cols]); return la.lstsq(Xm,D.gain.values,rcond=None)[0]
b=ols(D,['res','rank','pl']); ks=D.k.unique(); bs=[]
for _ in range(400):
    pick=rng.choice(ks,len(ks)); bs.append(ols(pd.concat([D[D.k==k] for k in pick]),['res','rank','pl'])[2])
lo,hi=np.percentile(bs,[2.5,97.5])
print(f"[4] virtuous cycle: resource-rank gain per place of over-performance = {-b[2]:.2f}  95% CI [{-hi:.2f},{-lo:.2f}]  (controls: resource rank, PL membership)")
out=[]
for s in sorted(P.Season.unique()):
    if s+5>P.Season.max(): continue
    hit=set(P[(P.Season>s)&(P.Season<=s+5)&(P['rank']<=6)].k)
    for r in P[(P.Season==s)&ok].itertuples():
        if r.rank>6: out.append((r.k,r.res_rank,r.k in hit))
O=pd.DataFrame(out,columns=['k','res','hit'])
for lo_,hi_ in [(1,6),(7,12),(13,22),(23,33),(34,44)]:
    sub=O[(O.res>=lo_)&(O.res<hi_+1)]; ks=sub.k.unique(); bs=[]
    for _ in range(600):
        pick=rng.choice(ks,len(ks)); bs.append(pd.concat([sub[sub.k==k] for k in pick]).hit.mean())
    l,h=np.percentile(bs,[2.5,97.5])
    print(f"[5] resource rank {lo_:2d}-{hi_:2d}: P(top-6 in 5 seasons) {sub.hit.mean():.3f} [{l:.3f},{h:.3f}]  n={len(sub)} clubs={len(ks)}")
