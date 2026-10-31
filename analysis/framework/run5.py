import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from names import *
from alias import ALIAS
from flow import build
import numpy as np, pandas as pd
rng=np.random.default_rng(31)

def mfpt(P,i,j):
    K=len(P); idx=[x for x in range(K) if x!=j]
    A=np.eye(len(idx))-P[np.ix_(idx,idx)]
    return np.linalg.solve(A,np.ones(len(idx)))[idx.index(i)]

def esd_ladder(country,fn,lo=1992,hi=2024):
    df=pd.read_csv(fn,low_memory=False); df=df[df.tier.isin([1,2])]
    out=[]
    for (s,t),g in df.groupby(['Season','tier']):
        if s<lo or s>hi: continue
        wp=3 if s>=PTS3[country] else 2
        r={}
        for _,x in g.iterrows():
            for tm,gf,ga in ((x.home,x.hgoal,x.vgoal),(x.visitor,x.vgoal,x.hgoal)):
                d=r.setdefault(tm,[0,0,0]); d[0]+=(wp if gf>ga else (1 if gf==ga else 0)); d[1]+=gf-ga; d[2]+=gf
        tt=pd.DataFrame([(k,v[0],v[1],v[2]) for k,v in r.items()],columns=['club','Pts','GD','GF'])
        tt=tt.sort_values(['Pts','GD','GF'],ascending=False).reset_index(drop=True)
        tt['pos']=np.arange(1,len(tt)+1); tt['Season']=s; tt['tier']=t
        out.append(tt[['club','Season','tier','pos']])
    d=pd.concat(out,ignore_index=True); d['k']=[norm(x) for x in d.club]; return d

def counts(lad,statef,K,lo,hi):
    tb=lad.copy(); tb['state']=tb.apply(statef,axis=1)
    ss=sorted(x for x in tb.Season.unique() if lo<=x<=hi)
    prs=[(a,b) for a,b in zip(ss,ss[1:]) if b==a+1]
    C=np.zeros((K,K)); pairs=[]
    for a,b in prs:
        A=tb[tb.Season==a].drop_duplicates('k').set_index('k').state
        B=tb[tb.Season==b].drop_duplicates('k').set_index('k').state
        ix=A.index.intersection(B.index)
        for c in ix: C[A[c],B[c]]+=1
        pairs.append((A,B,list(ix)))
    return C,pairs,len(prs)

def G(lad,statef,K,src,tgt,lo=1992,hi=2024,reps=300):
    C,pairs,np_=counts(lad,statef,K,lo,hi)
    if (C.sum(1)==0).any(): return None
    P=C/C.sum(1,keepdims=True); o=mfpt(P,src,tgt)
    nv=[]
    for _ in range(reps):
        Cn=np.zeros((K,K))
        for A,B,ix in pairs:
            pm=rng.permutation(B[ix].values)
            for c,s2 in zip(ix,pm): Cn[A[c],s2]+=1
        if (Cn.sum(1)==0).any(): continue
        try: nv.append(mfpt(Cn/Cn.sum(1,keepdims=True),src,tgt))
        except Exception: pass
    return o,float(np.mean(nv)),o/float(np.mean(nv)),np_

def t1only(r): return 0 if r.pos<=4 else (1 if r.pos<=10 else 2)
def pyr(r):    return (0 if r.pos<=4 else (1 if r.pos<=10 else 2)) if r.tier==1 else 3

if __name__=="__main__":
    lads={}
    for c,f in [('fr','france'),('es','spain'),('it','italy')]:
        lads[{'fr':'FRA','es':'ESP','it':'ITA'}[c]]=build(c,f)
    for c,f in [('eng','england'),('de','germany')]:
        lads[{'eng':'ENG','de':'GER'}[c]]=esd_ladder(c,f'/tmp/fr/{f}.csv')
    
    print("="*84)
    print("A. TIER-1-ONLY (truncated at the divisional boundary — the standard approach)")
    print("="*84)
    print(f"{'country':8s} {'pairs':>6s} {'obs MFPT':>9s} {'null':>7s} {'G':>7s}")
    res={}
    for c in ['ENG','ESP','ITA','GER','FRA']:
        lad=lads[c]; r=G(lad[lad.tier==1],t1only,3,2,0)
        res[c]={'trunc':r}
        print(f"{c:8s} {r[3]:6d} {r[0]:9.2f} {r[1]:7.2f} {r[2]:7.2f}")
    
    print("\n"+"="*84)
    print("B. PYRAMID-WIDE (tiers 1-2, relegation is a transition) — ALL FIVE COUNTRIES")
    print("="*84)
    print(f"{'country':8s} {'pairs':>6s} {'obs MFPT':>9s} {'null':>7s} {'G':>7s}")
    for c in ['ENG','ESP','ITA','GER','FRA']:
        r=G(lads[c],pyr,4,2,0); res[c]['pyr']=r
        print(f"{c:8s} {r[3]:6d} {r[0]:9.2f} {r[1]:7.2f} {r[2]:7.2f}")
    
    print("\n"+"="*84)
    print("C. TRUNCATION BIAS, LIKE-FOR-LIKE (same source state, same target state)")
    print("="*84)
    print(f"{'country':8s} {'truncated':>10s} {'pyramid':>9s} {'ratio':>7s}")
    rs=[]
    for c in ['ENG','ESP','ITA','GER','FRA']:
        a=res[c]['trunc'][0]; b=res[c]['pyr'][0]; rs.append(b/a)
        print(f"{c:8s} {a:10.2f} {b:9.2f} {b/a:7.2f}")
    print(f"{'MEAN':8s} {'':10s} {'':9s} {np.mean(rs):7.2f}   sd={np.std(rs,ddof=1):.2f}")
    