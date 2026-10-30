"""Outsider-specific mobility (D231). An 'outsider' at season s = no top-four finish in seasons s-10..s-1.
Chain estimated on outsider club-seasons only; MFPT bottom-half-of-top-flight -> top four; compared with the all-club chain,
with the permutation null (all clubs), and with observed ten-season reach for outsiders. England four tiers.
Usage: FR_SRC=<src> python -I trend_outsider.py"""
import os, sys, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(HERE,'..','rcm'))
from trend_eng import state, mfpt
from ladder import eng_ladder
from clubkey import ck
rng=np.random.default_rng(10)
lad=eng_ladder(4,1948,2024)        # pre-1958 seasons only to define outsider status for 1958+
lad=lad[lad.tier<=4]; lad['k']=lad.club.map(ck)
lad=lad[(lad.Season>=1948)]
lad['st']=lad.apply(state,axis=1)
top=set(zip(lad[lad.st==0].k,lad[lad.st==0].Season))
lad['outsider']=[not any((k,s-j) in top for j in range(1,11)) for k,s in zip(lad.k,lad.Season)]
L=lad[lad.Season>=1958]
def trans(L,yrs,only_out):
    C=np.zeros((6,6)); allpairs=[]
    for a in yrs:
        A=L[L.Season==a].drop_duplicates('k').set_index('k'); B=L[L.Season==a+1].drop_duplicates('k').set_index('k')
        ix=A.index.intersection(B.index)
        if len(ix)==0: continue
        sa=A.loc[ix,'st'].values.astype(int); sb=B.loc[ix,'st'].values.astype(int); ou=A.loc[ix,'outsider'].values
        allpairs.append((sa,sb))
        m=ou if only_out else np.ones(len(ix),bool)
        np.add.at(C,(sa[m],sb[m]),1)
    return C,allpairs
def null_mfpt(allpairs,reps=150):
    v=[]
    for _ in range(reps):
        Cn=np.zeros((6,6))
        for a,b in allpairs: np.add.at(Cn,(a,rng.permutation(b)),1)
        if (Cn.sum(1)==0).any(): continue
        x=mfpt(Cn/Cn.sum(1,keepdims=True),2,0)
        if x==x: v.append(x)
    return np.mean(v)
ERAS=[(1958,1969),(1970,1980),(1981,1991),(1992,2002),(2003,2013),(2014,2023)]
print(f"{'era':10s} {'G all':>6s} {'G outsiders':>12s} {'ratio':>6s} | {'outsider 10y reach: model':>26s} {'observed':>9s} {'n':>5s}")
for a,b in ERAS:
    yrs=[y for y in range(a,b+1) if y+1<=2024]
    Ca,ap=trans(L,yrs,False); Co,_=trans(L,yrs,True); n=null_mfpt(ap)
    Pa=Ca/Ca.sum(1,keepdims=True)
    Po=Co.copy(); 
    for i in range(6):
        if Po[i].sum()==0: Po[i]=Ca[i]          # top-four row for outsiders is empty by definition; irrelevant once absorbed
    Po=Po/Po.sum(1,keepdims=True)
    ga=mfpt(Pa,2,0)/n; go=mfpt(Po,2,0)/n
    Q=Po.copy(); Q[0]=0; Q[0,0]=1; model=np.linalg.matrix_power(Q,10)[2,0]
    st=L[(L.Season>=a)&(L.Season<=min(b,2014))&(L.st==2)&(L.outsider)]
    hit=[any((k,s+j) in top for j in range(1,11)) for k,s in zip(st.k,st.Season)]
    obs=np.mean(hit) if hit else np.nan
    print(f"{a}-{b+1:<5d} {ga:6.2f} {go:12.2f} {go/ga:6.2f} | {model:26.3f} {obs:9.3f} {len(hit):5d}")

# Block bootstrap over season pairs for outsider G (null held at its point estimate for speed)
print("\nOutsider G with 95% block-bootstrap interval (null fixed at point estimate):")
for a,b in ERAS:
    yrs=[y for y in range(a,b+1) if y+1<=2024]
    Ca,ap=trans(L,yrs,False); n=null_mfpt(ap,reps=100)
    per={y:trans(L,[y],True)[0] for y in yrs}; pa={y:trans(L,[y],False)[0] for y in yrs}
    def g_of(sample):
        Co=sum(per[y] for y in sample); Cb=sum(pa[y] for y in sample)
        if (Cb.sum(1)==0).any(): return np.nan
        Po=Co.copy()
        for i in range(6):
            if Po[i].sum()==0: Po[i]=Cb[i]
        return mfpt(Po/Po.sum(1,keepdims=True),2,0)/n
    pt=g_of(yrs); bs=[g_of(list(rng.choice(yrs,len(yrs)))) for _ in range(300)]; bs=[x for x in bs if x==x and x>0]
    print(f"{a}-{b+1:<5d} {pt:6.2f}  [{np.percentile(bs,2.5):.2f}, {np.percentile(bs,97.5):.2f}]")
