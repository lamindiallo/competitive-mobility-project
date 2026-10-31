import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from names import norm
from run5 import mfpt
from depth import trans, fp
rng=np.random.default_rng(31)
def lad_from(fn,maxtier,lo,hi,wpyear):
    df=pd.read_csv(fn,low_memory=False); df=df[df.tier<=maxtier]
    out=[]
    for (s,t),g in df.groupby(['Season','tier']):
        if s<lo or s>hi: continue
        wp=3 if s>=wpyear else 2; r={}
        for _,x in g.iterrows():
            for tm,gf,ga in ((x.home,x.hgoal,x.vgoal),(x.visitor,x.vgoal,x.hgoal)):
                d=r.setdefault(tm,[0,0,0]); d[0]+=(wp if gf>ga else (1 if gf==ga else 0)); d[1]+=gf-ga; d[2]+=gf
        tt=pd.DataFrame([(k,*v) for k,v in r.items()],columns=['club','Pts','GD','GF'])
        tt=tt.sort_values(['Pts','GD','GF'],ascending=False).reset_index(drop=True)
        tt['pos']=np.arange(1,len(tt)+1); tt['Season']=s; tt['tier']=t
        out.append(tt[['club','Season','tier','pos']])
    d=pd.concat(out,ignore_index=True); d['k']=[norm(x) for x in d.club]; return d

sco=lad_from('/tmp/fr/scotland.csv',4,1994,2024,1994) if __import__('os').path.exists('/tmp/fr/scotland.csv') else None
if sco is None:
    import shutil; shutil.copy('/tmp/esd/data-raw/scotland.csv','/tmp/fr/scotland.csv')
    sco=lad_from('/tmp/fr/scotland.csv',4,1994,2024,1994)
n1=sco[sco.tier==1].groupby('Season').size()
print('Scotland: seasons',len(set(sco.Season)),'tier1 size',sorted(set(n1)),'tiers',sorted(set(sco.tier)))
def sf1(r): return 0 if r.pos<=2 else (1 if r.pos<=6 else 2)
def sfp(r): return (0 if r.pos<=2 else (1 if r.pos<=6 else 2)) if r.tier==1 else 2+r.tier-1
def Gof(sub,sf,K,s=2,t=0,reps=200):
    C=trans(sub,sf,K,1994,2024); o=fp(C,s,t)
    tb=sub.copy(); tb['state']=tb.apply(sf,axis=1); ss=sorted(tb.Season.unique()); prs=[]
    for a,b in zip(ss,ss[1:]):
        if b!=a+1: continue
        A=tb[tb.Season==a].drop_duplicates('k').set_index('k').state; B=tb[tb.Season==b].drop_duplicates('k').set_index('k').state
        ix=list(A.index.intersection(B.index)); prs.append((A[ix].values,B[ix].values))
    nv=[]
    for _ in range(reps):
        Cn=np.zeros((K,K))
        for a,b in prs:
            pm=rng.permutation(b)
            for x,y in zip(a,pm): Cn[x,y]+=1
        v=fp(Cn,s,t)
        if v==v: nv.append(v)
    return o,float(np.mean(nv))
print("\nSCOTLAND — depth ladder (top 2 / 3-6 / 7-12 in tier 1)")
print(f"{'depth':>6s} {'K':>3s} {'MFPT':>8s} {'ratio':>7s} {'null':>7s} {'G':>6s}")
base=None
for depth in [1,2,3,4]:
    sub=sco[sco.tier<=depth]; K=3 if depth==1 else 2+depth
    sf=sf1 if depth==1 else sfp
    o,n=Gof(sub,sf,K)
    if base is None: base=o
    print(f"{depth:6d} {K:3d} {o:8.2f} {o/base:7.2f} {n:7.2f} {o/n:6.2f}")

def sf1b(r): return 0 if r.pos<=4 else (1 if r.pos<=8 else 2)
def sfpb(r): return (0 if r.pos<=4 else (1 if r.pos<=8 else 2)) if r.tier==1 else 2+r.tier-1
print("\nSCOTLAND — alternative boundaries (top 4 / 5-8 / 9-12)")
print(f"{'depth':>6s} {'K':>3s} {'MFPT':>8s} {'ratio':>7s} {'null':>7s} {'G':>6s}")
base=None
for depth in [1,2,3,4]:
    sub=sco[sco.tier<=depth]; K=3 if depth==1 else 2+depth
    sf=sf1b if depth==1 else sfpb
    o,n=Gof(sub,sf,K)
    if base is None: base=o
    print(f"{depth:6d} {K:3d} {o:8.2f} {o/base:7.2f} {n:7.2f} {o/n:6.2f}")
