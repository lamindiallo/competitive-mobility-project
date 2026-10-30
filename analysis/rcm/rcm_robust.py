import sys, numpy as np, pandas as pd
from scipy.stats import spearmanr, pearsonr
import numpy.linalg as la
P=pd.read_csv(sys.argv[1]); rng=np.random.default_rng(5)
def lagcorr(P,col,lag):
    W=P.pivot_table(index='k',columns='Season',values=col); a=[];b=[]
    for s in W.columns:
        if s+lag in W.columns:
            m=W[s].notna()&W[s+lag].notna(); a+=list(W.loc[m,s]); b+=list(W.loc[m,s+lag])
    return pearsonr(a,b).statistic,len(a)
# --- (a) virtuous cycle, controlling for resource rank and ladder rank at t
print("="*84); print("4b. VIRTUOUS CYCLE, PROPERLY: regress resource-rank gain (t->t+2) on resource rank_t and ladder rank_t"); print("="*84)
Q=P.pivot_table(index='k',columns='Season',values='res_rank'); R=P.pivot_table(index='k',columns='Season',values='rank')
T=P.pivot_table(index='k',columns='Season',values='tier')
rows=[]
for s in Q.columns:
    if s+2 in Q.columns:
        m=Q[s].notna()&Q[s+2].notna()&R[s].notna()
        for k in Q.index[m]: rows.append((k,s,Q.loc[k,s]-Q.loc[k,s+2],Q.loc[k,s],R.loc[k,s],T.loc[k,s]))
D=pd.DataFrame(rows,columns=['k','s','gain','res','rank','tier'])
def ols(D,cols):
    X=np.column_stack([np.ones(len(D))]+[D[c].values for c in cols]); y=D.gain.values
    b=la.lstsq(X,y,rcond=None)[0]; return b
b=ols(D,['res','rank'])
# cluster bootstrap by club
ks=D.k.unique(); bs=[]
for _ in range(500):
    pick=rng.choice(ks,len(ks)); Db=pd.concat([D[D.k==k] for k in pick]); bs.append(ols(Db,['res','rank'])[2])
lo,hi=np.percentile(bs,[2.5,97.5])
print(f"  coef on ladder rank_t (holding resource rank fixed): {b[2]:+.3f}  95% CI [{lo:+.3f},{hi:+.3f}]")
print(f"  -> finishing 1 place HIGHER than a same-resourced club is followed by a resource-rank gain of {-b[2]:.2f} places two seasons later")
b2=ols(D.assign(t1=(D.tier==1).astype(float)),['res','rank','t1'])
print(f"  adding a Premier-League dummy: coef on rank {b2[2]:+.3f}, on PL membership {b2[3]:+.3f}  (how much of the cycle is promotion itself)")

# --- (b),(c) persistence under alternative resource definitions
print("\n"+"="*84); print("2b. OVER-PERFORMANCE PERSISTENCE UNDER ALTERNATIVE RESOURCE MEASURES"); print("="*84)
alt=P.copy()
alt['R1']=alt.gin   # same-season gross spend only (not predetermined; sensitivity only)
for name,col in [('R3 gross, 3-season (primary)','R3'),('N3 net, 3-season','N3'),('R1 gross, same season','R1')]:
    alt['rr']=alt.groupby('Season')[col].rank(ascending=False); alt['ov']=alt.rr-alt['rank']
    rho=np.mean([spearmanr(g.rr,g['rank']).statistic for _,g in alt.groupby('Season')])
    ac=[lagcorr(alt,'ov',l)[0] for l in (1,2,3,5)]
    print(f"  {name:32s} rho={rho:.2f}   persistence lag1 {ac[0]:+.2f}  lag2 {ac[1]:+.2f}  lag3 {ac[2]:+.2f}  lag5 {ac[3]:+.2f}")

# --- (d) reach table, sorted, with bootstrap CI
print("\n"+"="*84); print("5b. RESOURCE-CONDITIONAL REACH, with club-cluster bootstrap 95% CIs"); print("="*84)
bands=[(1,6),(7,12),(13,22),(23,33),(34,44)]
out=[]
for s in sorted(P.Season.unique()):
    if s+5>P.Season.max(): continue
    hit=set(P[(P.Season>s)&(P.Season<=s+5)&(P['rank']<=6)].k)
    for r in P[P.Season==s].itertuples():
        if r.rank>6: out.append((r.k,r.res_rank,r.k in hit))
O=pd.DataFrame(out,columns=['k','res','hit'])
for lo_,hi_ in bands:
    sub=O[(O.res>=lo_)&(O.res<=hi_+0.5)]
    ks=sub.k.unique(); bs=[]
    for _ in range(1000):
        pick=rng.choice(ks,len(ks)); bs.append(pd.concat([sub[sub.k==k] for k in pick]).hit.mean())
    l,h=np.percentile(bs,[2.5,97.5])
    print(f"  resource rank {lo_:2d}-{hi_:2d}:  P(top-6 within 5 seasons) = {sub.hit.mean():.3f}  [{l:.3f},{h:.3f}]   n={len(sub)}, clubs={len(ks)}")

# --- (e) Championship disclosure check
print("\n"+"="*84); print("6. MEASUREMENT: is the weak Championship fit money mattering less, or money measured worse?"); print("="*84)
for t in (1,2):
    sub=P[P.tier==t]; zero=(sub.R3==0).mean()
    print(f"  tier {t}: share of club-seasons with ZERO recorded 3-season spend: {zero:.0%}")
