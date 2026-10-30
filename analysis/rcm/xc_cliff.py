"""Is England's positional cliff a spending cliff? (1) shape of the spending distribution by league; (2) reach vs relative spend, pooled, with league effects.
Usage: python -I xc_cliff.py xc_panel.csv"""
import sys, numpy as np, pandas as pd
import statsmodels.api as sm
P=pd.read_csv(sys.argv[1]); P=P[P.Season>=2004]
pres=set(zip(P.country,P.ewclub,P.Season))
P['win_ok']=[((c,k,s-1) in pres) and ((c,k,s-2) in pres) for c,k,s in zip(P.country,P.ewclub,P.Season)]
P=P[P.Season>=2006].copy(); P['res']=P.groupby(['country','Season']).R3.rank(ascending=False,method='first')
# (1) spending shape: R3 of rank r relative to rank 1, averaged over seasons
print("(1) Mean 3-season spend of the club at each resource rank, as a share of the 4th-largest spender")
ref=P[P.res==4].set_index(['country','Season']).R3
P['rel']=[r/ref.get((c,s),np.nan) if ref.get((c,s),0)>0 else np.nan for r,c,s in zip(P.R3,P.country,P.Season)]
tab=P[P.res<=12].groupby(['country','res']).rel.median().unstack()
print(tab.round(2).to_string())
print("\n    'Big-spender count' = mean number of clubs per season spending at least 50% of the largest spender:")
P['rel1']=P.R3/P.groupby(['country','Season']).R3.transform('max')
print((P[P.rel1>=0.5].groupby(['country','Season']).size().groupby('country').mean()).round(2).to_string())
# (2) reach on relative spend, pooled
out=[]
for (c,s),g in P.groupby(['country','Season']):
    if s+5>P[P.country==c].Season.max(): continue
    D=P[P.country==c]; hit=set(D[(D.Season>s)&(D.Season<=s+5)&(D.pos<=4)].ewclub)
    for r in g[g.win_ok].itertuples():
        if r.pos>4 and r.rel==r.rel and r.rel>0: out.append((c,r.ewclub,np.log(r.rel),r.ewclub in hit))
O=pd.DataFrame(out,columns=['country','k','lrel','hit'])
X=pd.get_dummies(O.country,drop_first=False).astype(float).drop(columns='ENG'); X['lrel']=O.lrel; X=sm.add_constant(X)
m0=sm.Logit(O.hit.astype(float),sm.add_constant(pd.get_dummies(O.country).astype(float).drop(columns='ENG'))).fit(disp=0,cov_type='cluster',cov_kwds={'groups':pd.factorize(O.k)[0]})
m1=sm.Logit(O.hit.astype(float),X).fit(disp=0,cov_type='cluster',cov_kwds={'groups':pd.factorize(O.k)[0]})
print("\n(2) Logit: reached top four within 5 seasons (clubs not currently top four). England is the reference. Club-clustered SEs.")
print("    league effects WITHOUT relative spend:   "+"  ".join(f"{k} {v:+.2f} (p={m0.pvalues[k]:.3f})" for k,v in m0.params.items() if k!='const'))
print("    league effects WITH log relative spend:  "+"  ".join(f"{k} {v:+.2f} (p={m1.pvalues[k]:.3f})" for k,v in m1.params.items() if k not in('const','lrel')))
print(f"    log relative spend coefficient: {m1.params['lrel']:+.2f} (p={m1.pvalues['lrel']:.4f});  n={len(O)}")
