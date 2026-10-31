import numpy as np, pandas as pd
from scipy.optimize import nnls
D=pd.read_csv('/tmp/fr/03/country_mobility_panel.csv')
UNITS=['ITA','ESP','ENG','GER','FRA','SCO']
def series(out,smooth=3):
    piv=D.pivot(index='Season',columns='country',values=out)[UNITS]
    piv=piv.interpolate(limit_direction='both')
    return piv.rolling(smooth,center=True,min_periods=2).mean()
def scm(piv,treated,donors,t0,pre_start=1996):
    pre=piv.loc[pre_start:t0-1]
    A=pre[donors].values; y=pre[treated].values
    # nnls with sum-to-one via augmentation
    lam=1e3
    Aa=np.vstack([A,lam*np.ones((1,len(donors)))]); ya=np.concatenate([y,[lam]])
    w,_=nnls(Aa,ya)
    fit=piv[donors].values@w
    return w,fit
def run(out,treated,t0,label):
    piv=series(out)
    donors=[u for u in UNITS if u!=treated and u not in ('ITA','ESP')]
    w,fit=scm(piv,treated,donors,t0)
    gap=piv[treated].values-fit
    yrs=piv.index.values
    pre=(yrs<t0)&(yrs>=1996); post=(yrs>=t0)&(yrs<=t0+6)
    rmspe_pre=np.sqrt(np.nanmean(gap[pre]**2)); rmspe_post=np.sqrt(np.nanmean(gap[post]**2))
    ratio=rmspe_post/rmspe_pre
    # placebo in space: each donor treated in turn
    pl=[]
    for d in donors:
        dd=[x for x in donors if x!=d]
        w2,f2=scm(piv,d,dd,t0); g2=piv[d].values-f2
        r=np.sqrt(np.nanmean(g2[post]**2))/np.sqrt(np.nanmean(g2[pre]**2)); pl.append((d,r))
    rank=1+sum(1 for _,r in pl if r>=ratio); p=rank/(len(pl)+1)
    print(f"\n{label}  outcome={out}  treated={treated}  switch={t0}")
    print("  weights: "+", ".join(f"{d}={x:.2f}" for d,x in zip(donors,w)))
    print(f"  pre-RMSPE {rmspe_pre:.4f}   post-RMSPE {rmspe_post:.4f}   ratio {ratio:.2f}")
    print("  placebo ratios: "+", ".join(f"{d}={r:.2f}" for d,r in pl))
    print(f"  rank {rank} of {len(pl)+1}  ->  p = {p:.2f}")
    print("  gaps (t-3..t+6): "+" ".join(f"{gap[list(yrs).index(y)]:+.3f}" for y in range(t0-3,t0+7) if y in yrs))
print("="*80); print("DESIGN 2 — SYNTHETIC CONTROL ON COLLECTIVE-SELLING SWITCHES"); print("="*80)
for out in ['jump','churn','top6persist']:
    run(out,'ITA',2010,'Italy (Melandri, first applied 2010/11)')
    run(out,'ESP',2016,'Spain (RDL 5/2015, first applied 2016/17)')
