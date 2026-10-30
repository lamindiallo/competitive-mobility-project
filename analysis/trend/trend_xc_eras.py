"""Era estimates of top-flight (truncated) G with block-bootstrap CIs, seven leagues. Trend comparisons only (levels are truncation-biased, D165).
Usage: FR_SRC=<src> python -I trend_xc_eras.py"""
import os, sys, numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from trend_xc import t1, pairs, FILES
from trend_eng import G
rng=np.random.default_rng(92)
ERAS=[(1958,1969),(1970,1980),(1981,1991),(1992,2002),(2003,2013),(2014,2023)]
rows=[]
for c in FILES:
    PR=pairs(t1(c))
    for a,b in ERAS:
        prs=[PR[s] for s in range(a,b+1) if s in PR]
        if len(prs)<8: continue
        g=G(prs,K=3,reps=200)[2]; bs=[]
        for _ in range(150):
            r=G([prs[i] for i in rng.integers(0,len(prs),len(prs))],K=3,reps=40)[2]
            if r==r: bs.append(r)
        rows.append(dict(country=c,era=f"{a}-{b+1}",G=g,lo=np.percentile(bs,2.5),hi=np.percentile(bs,97.5),pairs=len(prs)))
R=pd.DataFrame(rows); R.to_csv(sys.argv[1] if len(sys.argv)>1 else 'xc_eras.csv',index=False)
R['cell']=R.apply(lambda r:f"{r.G:.2f} [{r.lo:.2f},{r.hi:.2f}]",axis=1)
pd.set_option('display.width',250); print(R.pivot(index='country',columns='era',values='cell').to_string())
