"""Outsider G across seven leagues, top flight only (trend comparison; levels truncation-biased, D223).
Outsider = no top-four finish in the previous ten seasons; requires ten prior seasons of data, so each league's first era starts ten
seasons after its data begins. Usage: FR_SRC=<src> python -I trend_outsider_xc.py"""
import os, sys, numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from trend_xc import t1, FILES
from trend_eng import mfpt
rng=np.random.default_rng(12)
ERAS=[(1958,1969),(1970,1980),(1981,1991),(1992,2002),(2003,2013),(2014,2023)]
def run(c):
    d=t1(c,lo=1930,hi=2024); first=d.Season.min()
    top=set(zip(d[d.st==0].k,d[d.st==0].Season))
    d['out']=[not any((k,s-j) in top for j in range(1,11)) for k,s in zip(d.k,d.Season)]
    res={}
    for a,b in ERAS:
        if a<first+10: continue
        Ca=np.zeros((3,3)); Co=np.zeros((3,3)); ap=[]
        for y in range(a,b+1):
            A=d[d.Season==y].drop_duplicates('k').set_index('k'); B=d[d.Season==y+1].drop_duplicates('k').set_index('k')
            ix=A.index.intersection(B.index)
            if len(ix)==0: continue
            sa=A.loc[ix,'st'].values.astype(int); sb=B.loc[ix,'st'].values.astype(int); ou=A.loc[ix,'out'].values
            np.add.at(Ca,(sa,sb),1); np.add.at(Co,(sa[ou],sb[ou]),1); ap.append((sa,sb))
        if len(ap)<8: continue
        nv=[]
        for _ in range(150):
            Cn=np.zeros((3,3))
            for x,y in ap: np.add.at(Cn,(x,rng.permutation(y)),1)
            v=mfpt(Cn/Cn.sum(1,keepdims=True),2,0)
            if v==v: nv.append(v)
        n=np.mean(nv)
        Po=Co.copy()
        for i in range(3):
            if Po[i].sum()==0: Po[i]=Ca[i]
        go=mfpt(Po/Po.sum(1,keepdims=True),2,0)/n; ga=mfpt(Ca/Ca.sum(1,keepdims=True),2,0)/n
        res[f"{a}-{b+1}"]=(ga,go)
    return res
rows=[]
for c in FILES:
    for era,(ga,go) in run(c).items(): rows.append(dict(country=c,era=era,G_all=ga,G_out=go))
R=pd.DataFrame(rows); R.to_csv(sys.argv[1] if len(sys.argv)>1 else 'outsider_xc.csv',index=False)
R['cell']=R.apply(lambda r:f"{r.G_out:5.1f} ({r.G_all:.1f})",axis=1)
pd.set_option('display.width',220); print("Outsider G (all-club G in brackets), top flight:"); print(R.pivot(index='country',columns='era',values='cell').to_string())
