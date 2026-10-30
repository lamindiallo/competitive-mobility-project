"""Bootstrap intervals for top-flight outsider G, 2003-14 and 2014-24, six leagues (Portugal excluded: near-absorbing, D226).
Null held at its point estimate. Usage: FR_SRC=<src> python -I trend_outsider_xc_ci.py"""
import os, sys, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from trend_xc import t1
from trend_eng import mfpt
rng=np.random.default_rng(13)
for c in ['ENG','ESP','ITA','GER','FRA','NED']:
    d=t1(c,lo=1930,hi=2024); top=set(zip(d[d.st==0].k,d[d.st==0].Season))
    d['out']=[not any((k,s-j) in top for j in range(1,11)) for k,s in zip(d.k,d.Season)]
    line=[]
    for a,b in [(2003,2013),(2014,2023)]:
        per={}
        for y in range(a,b+1):
            A=d[d.Season==y].drop_duplicates('k').set_index('k'); B=d[d.Season==y+1].drop_duplicates('k').set_index('k'); ix=A.index.intersection(B.index)
            sa=A.loc[ix,'st'].values.astype(int); sb=B.loc[ix,'st'].values.astype(int); ou=A.loc[ix,'out'].values
            Ca=np.zeros((3,3)); Co=np.zeros((3,3)); np.add.at(Ca,(sa,sb),1); np.add.at(Co,(sa[ou],sb[ou]),1); per[y]=(Ca,Co,sa,sb)
        yrs=list(per); nv=[]
        for _ in range(150):
            Cn=np.zeros((3,3))
            for y in yrs: np.add.at(Cn,(per[y][2],rng.permutation(per[y][3])),1)
            v=mfpt(Cn/Cn.sum(1,keepdims=True),2,0)
            if v==v: nv.append(v)
        n=np.mean(nv)
        def g(sample):
            Ca=sum(per[y][0] for y in sample); Co=sum(per[y][1] for y in sample)
            if (Ca.sum(1)==0).any(): return np.nan
            Po=Co.copy()
            for i in range(3):
                if Po[i].sum()==0: Po[i]=Ca[i]
            return mfpt(Po/Po.sum(1,keepdims=True),2,0)/n
        pt=g(yrs); bs=[g(list(rng.choice(yrs,len(yrs)))) for _ in range(300)]
        fin=[x for x in bs if x==x and 0<x<1e6]; unreach=1-len(fin)/len(bs)
        lo,hi=(np.percentile(fin,2.5),np.percentile(fin,97.5)) if fin else (np.nan,np.nan)
        line.append(f"{a}-{b+1}: {pt:6.1f} [{lo:5.1f},{hi:6.1f}] unreachable in {unreach:.0%} of resamples")
    print(f"{c}  "+"   |   ".join(line))
