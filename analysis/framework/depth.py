import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from names import norm, PTS3
from patch import parse_of, table_from
from run5 import mfpt

def eng_ladder(maxtier=4,lo=1992,hi=2024):
    df=pd.read_csv('/tmp/fr/england.csv',low_memory=False)
    df=df[df.tier<=maxtier]
    out=[]
    for (s,t),g in df.groupby(['Season','tier']):
        if s<lo or s>hi: continue
        wp=3 if s>=1981 else 2
        r={}
        for _,x in g.iterrows():
            for tm,gf,ga in ((x.home,x.hgoal,x.vgoal),(x.visitor,x.vgoal,x.hgoal)):
                d=r.setdefault(tm,[0,0,0]); d[0]+=(wp if gf>ga else (1 if gf==ga else 0)); d[1]+=gf-ga; d[2]+=gf
        tt=pd.DataFrame([(k,*v) for k,v in r.items()],columns=['club','Pts','GD','GF'])
        tt=tt.sort_values(['Pts','GD','GF'],ascending=False).reset_index(drop=True)
        tt['pos']=np.arange(1,len(tt)+1); tt['Season']=s; tt['tier']=t
        out.append(tt[['club','Season','tier','pos']])
    # patch 2022
    names={1:'1-premierleague',2:'2-championship',3:'3-league1',4:'4-league2'}
    for t in range(1,maxtier+1):
        tab=table_from(parse_of(f'/tmp/of_eng/2022-23/{names[t]}.txt'))
        tab['pos']=np.arange(1,len(tab)+1); tab['Season']=2022; tab['tier']=t
        out.append(tab[['club','Season','tier','pos']])
    d=pd.concat(out,ignore_index=True); d['k']=[norm(x) for x in d.club]; return d

def trans(lad,statef,K,lo=1992,hi=2024):
    tb=lad.copy(); tb['state']=tb.apply(statef,axis=1)
    ss=sorted(x for x in tb.Season.unique() if lo<=x<=hi)
    C=np.zeros((K,K))
    for a,b in zip(ss,ss[1:]):
        if b!=a+1: continue
        A=tb[tb.Season==a].drop_duplicates('k').set_index('k').state
        B=tb[tb.Season==b].drop_duplicates('k').set_index('k').state
        for c in A.index.intersection(B.index): C[A[c],B[c]]+=1
    return C

def fp(C,src,tgt):
    if (C.sum(1)==0).any(): return None
    return mfpt(C/C.sum(1,keepdims=True),src,tgt)

lad=eng_ladder(4)
print('England ladder: seasons',len(set(lad.Season)),'rows',len(lad),'tiers',sorted(set(lad.tier)))

print("\n"+"="*78)
print("E. DOES THE TRUNCATION FACTOR GROW WITH LADDER DEPTH?  (England, 1992-2024)")
print("   same source state (tier 1, pos 11-20), same target (tier 1, top 4)")
print("="*78)
def mk(depth):
    def f(r):
        if r.tier==1: return 0 if r.pos<=4 else (1 if r.pos<=10 else 2)
        return 2+min(r.tier,depth)-1+1-1+r.tier-1 if False else 2+r.tier-1
    return f
base=fp(trans(lad[lad.tier==1],lambda r:0 if r.pos<=4 else (1 if r.pos<=10 else 2),3),2,0)
print(f"{'depth':>6s} {'K':>3s} {'MFPT':>8s} {'ratio vs truncated':>20s}")
print(f"{'1 (trunc)':>9s} {3:3d} {base:8.2f} {1.0:20.2f}")
for depth in [2,3,4]:
    sub=lad[lad.tier<=depth]
    K=2+depth
    v=fp(trans(sub,mk(depth),K),2,0)
    print(f"{depth:>9d} {K:3d} {v:8.2f} {v/base:20.2f}")
