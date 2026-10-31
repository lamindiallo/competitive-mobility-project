import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from scipy.optimize import nnls
FILES={'ENG':'england','ESP':'spain','ITA':'italy','GER':'germany','FRA':'france','SCO':'scotland',
       'NED':'holland','POR':'portugal','BEL':'belgium','GRE':'greece','TUR':'turkey'}
import os,shutil
for c,f in FILES.items():
    if not os.path.exists(f'/tmp/fr/{f}.csv'):
        shutil.copy(f'/tmp/esd/data-raw/{f}.csv',f'/tmp/fr/{f}.csv')
rows=[]
for c,f in FILES.items():
    df=pd.read_csv(f'/tmp/fr/{f}.csv',low_memory=False); df=df[df.tier==1]
    tabs={}
    for s,g in df.groupby('Season'):
        if s<1994 or s>2024: continue
        r={}
        for _,x in g.iterrows():
            for tm,gf,ga in ((x.home,x.hgoal,x.vgoal),(x.visitor,x.vgoal,x.hgoal)):
                d=r.setdefault(tm,[0,0,0]); d[0]+=(3 if gf>ga else (1 if gf==ga else 0)); d[1]+=gf-ga; d[2]+=gf
        t=pd.DataFrame([(k,*v) for k,v in r.items()],columns=['club','P','GD','GF']).sort_values(['P','GD','GF'],ascending=False).reset_index(drop=True)
        t['pos']=np.arange(1,len(t)+1); tabs[s]=t.set_index('club')
    ss=sorted(tabs)
    for a,b in zip(ss,ss[1:]):
        if b!=a+1: continue
        A,B=tabs[a],tabs[b]; ix=A.index.intersection(B.index)
        if len(ix)<10: continue
        rho=spearmanr(A.loc[ix,'pos'],B.loc[ix,'pos']).statistic
        top6=[k for k in A.index if A.loc[k,'pos']<=6]
        p6=np.mean([1.0 if (k in B.index and B.loc[k,'pos']<=6) else 0.0 for k in top6])
        rows.append(dict(country=c,Season=a,churn=1-rho,top6persist=p6,jump=(B.loc[ix,'pos']-A.loc[ix,'pos']).abs().mean()/len(A)))
D=pd.DataFrame(rows); D.to_csv('/tmp/fr/03/country_mobility_t1_panel.csv',index=False)
UNITS=list(FILES)
def scm(piv,tr,don,t0,ps=1996):
    pre=piv.loc[ps:t0-1]; A=pre[don].values; y=pre[tr].values; lam=1e3
    w,_=nnls(np.vstack([A,lam*np.ones((1,len(don)))]),np.concatenate([y,[lam]]))
    return w, piv[don].values@w
def run(out,tr,t0):
    piv=D.pivot(index='Season',columns='country',values=out)[UNITS].interpolate(limit_direction='both').rolling(3,center=True,min_periods=2).mean()
    don=[u for u in UNITS if u not in ('ITA','ESP')]
    w,fit=scm(piv,tr,don,t0); gap=piv[tr].values-fit; yrs=piv.index.values
    pre=(yrs<t0)&(yrs>=1996); post=(yrs>=t0)&(yrs<=t0+6)
    ratio=np.sqrt(np.nanmean(gap[post]**2))/np.sqrt(np.nanmean(gap[pre]**2))
    pl=[]
    for d in don:
        dd=[x for x in don if x!=d]; w2,f2=scm(piv,d,dd,t0); g2=piv[d].values-f2
        pl.append((d,np.sqrt(np.nanmean(g2[post]**2))/np.sqrt(np.nanmean(g2[pre]**2))))
    rank=1+sum(1 for _,r in pl if r>=ratio); p=rank/(len(pl)+1)
    print(f"\n {out:12s} {tr} @{t0}   RMSPE ratio {ratio:.2f}   rank {rank}/{len(pl)+1}   p={p:.3f}   (floor {1/(len(pl)+1):.2f})")
    print(f"   weights: "+", ".join(f"{d}={x:.2f}" for d,x in zip(don,w) if x>0.02))
    print(f"   gaps t..t+6: "+" ".join(f"{gap[list(yrs).index(y)]:+.3f}" for y in range(t0,t0+7) if y in yrs))
print("="*84); print("DESIGN 2b — EXPANDED DONOR POOL (tier-1 outcomes, 9 candidate never-switchers)"); print("="*84)
for out in ['jump','churn','top6persist']:
    run(out,'ITA',2010); run(out,'ESP',2016)
