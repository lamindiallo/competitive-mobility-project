"""EXPLORATORY test of H12 (crowding) on the transfer-spend proxy. H12's registered test is on wage data (D222); this run cannot falsify it.
Reach model of xc_cliff.py plus an elite-count covariate: number of OTHER clubs in the league-season spending at least as much as the club
and at least half the largest spender ("near-elite rivals above"). Usage: python -I xc_crowding.py xc_panel.csv"""
import sys, numpy as np, pandas as pd, statsmodels.api as sm
P=pd.read_csv(sys.argv[1]); P=P[P.Season>=2004]
pres=set(zip(P.country,P.ewclub,P.Season))
P['win_ok']=[((c,k,s-1) in pres) and ((c,k,s-2) in pres) for c,k,s in zip(P.country,P.ewclub,P.Season)]
P=P[P.Season>=2006].copy(); P['res']=P.groupby(['country','Season']).R3.rank(ascending=False,method='first')
P['mx']=P.groupby(['country','Season']).R3.transform('max')
ref=P[P.res==4].set_index(['country','Season']).R3
P['rel']=[r/ref.get((c,s),np.nan) if ref.get((c,s),0)>0 else np.nan for r,c,s in zip(P.R3,P.country,P.Season)]
def rivals(g):
    elite=g[g.R3>=0.5*g.mx]
    return g.apply(lambda r:int(((elite.R3>=r.R3)&(elite.ewclub!=r.ewclub)).sum()),axis=1)
P['rivals']=P.groupby(['country','Season'],group_keys=False).apply(rivals)
P['elite_n']=P.groupby(['country','Season']).R3.transform(lambda x:(x>=0.5*x.max()).sum())
out=[]
for (c,s),g in P.groupby(['country','Season']):
    D=P[P.country==c]
    if s+5>D.Season.max(): continue
    hit=set(D[(D.Season>s)&(D.Season<=s+5)&(D.pos<=4)].ewclub)
    for r in g[g.win_ok].itertuples():
        if r.pos>4 and r.rel==r.rel and r.rel>0: out.append((c,r.ewclub,np.log(r.rel),r.rivals,r.elite_n,r.ewclub in hit))
O=pd.DataFrame(out,columns=['country','k','lrel','rivals','elite_n','hit'])
grp=pd.factorize(O.k)[0]; dums=pd.get_dummies(O.country).astype(float).drop(columns='ENG')
def fit(cols,extra=None):
    X=dums.copy()
    for c in cols: X[c]=O[c]
    m=sm.Logit(O.hit.astype(float),sm.add_constant(X)).fit(disp=0,cov_type='cluster',cov_kwds={'groups':grp}); return m
print("League means of near-elite count (clubs spending >= half the largest):",O.groupby('country').elite_n.mean().round(2).to_dict())
for cols in (['lrel'],['lrel','elite_n'],['lrel','rivals']):
    m=fit(cols)
    print(f"\nmodel: league + {cols}   n={len(O)}")
    print("   "+"  ".join(f"{k} {v:+.2f} (p={m.pvalues[k]:.3f})" for k,v in m.params.items() if k!='const'))
