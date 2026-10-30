import sys, numpy as np, pandas as pd
from scipy.stats import spearmanr, pearsonr
P=pd.read_csv(sys.argv[1]); rng=np.random.default_rng(11)
print("="*84); print("1. HOW MUCH OF POSITION DOES (TRANSFER-SPEND) RESOURCE RANK EXPLAIN?  England t1-2, 2006-2022"); print("="*84)
rs=[spearmanr(g.res_rank,g['rank']).statistic for _,g in P.groupby('Season')]
r1=[spearmanr(g.res_rank,g['rank']).statistic for _,g in P[P.tier==1].groupby('Season')]
r2=[spearmanr(g.res_rank,g['rank']).statistic for _,g in P[P.tier==2].groupby('Season')]
print(f"  Spearman(resource rank, ladder rank), 44-club ladder: mean {np.mean(rs):.3f}  (range {min(rs):.2f}-{max(rs):.2f})  -> rho^2 {np.mean(rs)**2:.2f}")
print(f"  within Premier League only:  mean {np.mean(r1):.3f}    within Championship only: mean {np.mean(r2):.3f}")

print("\n"+"="*84); print("2. IS OVER-PERFORMANCE PERSISTENT?  (over = resource rank - ladder rank; + = beats its money)"); print("="*84)
W=P.pivot_table(index='k',columns='Season',values='over')
for lag in [1,2,3,5]:
    a=[];b=[]
    for s in W.columns:
        if s+lag in W.columns:
            m=W[s].notna()&W[s+lag].notna(); a+=list(W.loc[m,s]); b+=list(W.loc[m,s+lag])
    r=pearsonr(a,b).statistic
    # null: shuffle over within season
    nulls=[]
    for _ in range(300):
        Wn=W.copy()
        for s in Wn.columns:
            m=Wn[s].notna(); Wn.loc[m,s]=rng.permutation(Wn.loc[m,s].values)
        aa=[];bb=[]
        for s in Wn.columns:
            if s+lag in Wn.columns:
                m=Wn[s].notna()&Wn[s+lag].notna(); aa+=list(Wn.loc[m,s]); bb+=list(Wn.loc[m,s+lag])
        nulls.append(pearsonr(aa,bb).statistic)
    p=np.mean(np.abs(nulls)>=abs(r))
    print(f"  lag {lag}: autocorr {r:+.3f}  (n={len(a)})   null sd {np.std(nulls):.3f}   p={p:.3f}")

print("\n"+"="*84); print("3. DECISION-DRIVEN CLIMBS: clubs rising >=10 ladder places over 3 seasons"); print("="*84)
R=P.pivot_table(index='k',columns='Season',values='rank'); Q=P.pivot_table(index='k',columns='Season',values='res_rank')
ep=[]
for s in R.columns:
    if s+3 in R.columns:
        m=R[s].notna()&R[s+3].notna()&Q[s].notna()&Q[s+3].notna()
        for k in R.index[m]:
            dr=R.loc[k,s]-R.loc[k,s+3]; dq=Q.loc[k,s]-Q.loc[k,s+3]
            if dr>=10: ep.append((k,s,dr,dq))
E=pd.DataFrame(ep,columns=['k','start','climb','res_climb'])
print(f"  climbs: {len(E)}   resource rank did NOT improve: {(E.res_climb<=0).sum()} ({(E.res_climb<=0).mean():.0%})   improved by <half the climb: {(E.res_climb<E.climb/2).mean():.0%}")
print("  examples (resource rank fell or flat):")
print(E[E.res_climb<=0].sort_values('climb',ascending=False).head(8).to_string(index=False))

print("\n"+"="*84); print("4. VIRTUOUS CYCLE: does over-performance at t predict a resource-rank gain t -> t+2?"); print("="*84)
a=[];b=[]
for s in W.columns:
    if s+2 in Q.columns:
        m=W[s].notna()&Q[s].notna()&Q[s+2].notna()
        a+=list(W.loc[m,s]); b+=list(Q.loc[m,s]-Q.loc[m,s+2])
print(f"  corr(over_t, resource-rank gain t->t+2) = {pearsonr(a,b).statistic:+.3f}  (n={len(a)})")

print("\n"+"="*84); print("5. RESOURCE-CONDITIONAL REACH: P(top-6 PL within 5 seasons | starting resource band)"); print("="*84)
P['band']=pd.cut(P.res_rank,[0,6,12,22,33,44],labels=['res 1-6','res 7-12','res 13-22','res 23-33','res 34-44'])
out=[]
for s in sorted(P.Season.unique()):
    if s+5>P.Season.max(): continue
    cur=P[P.Season==s]
    fut=P[(P.Season>s)&(P.Season<=s+5)&(P['rank']<=6)]
    hit=set(fut.k)
    for r in cur.itertuples():
        if r.rank>6: out.append((r.band,r.k in hit,r.tier))
O=pd.DataFrame(out,columns=['band','hit','tier'])
print(O.groupby('band',observed=True).hit.agg(['mean','size']).rename(columns={'mean':'P(top6 in 5y)','size':'n'}).round(3).to_string())
