"""Top-flight (truncated) rolling G for several countries, 1958-2024, K=3 (top 4 / 5-10 / 11-last).
Step 1 validates the truncated series as a TREND proxy by correlating England's truncated and pyramid-wide rolling series.
Usage: FR_SRC=<src> python -I trend_xc.py <eng_rolling_G.csv> <outdir>"""
import os, sys, numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(HERE,'..','rcm'))
from trend_eng import G
from ladder import table_from, norm, parse_of
SRC=os.environ['FR_SRC']; rng=np.random.default_rng(7)
FILES={'ENG':('england',1981),'ESP':('spain',1995),'ITA':('italy',1994),'FRA':('france',1994),'GER':('germany',1995),'NED':('holland',1995),'POR':('portugal',1995)}
def t1(c,lo=1958,hi=2024):
    """Superseded raw loader replaced by the cleaned loader (D239); see topflight_clean.py."""
    from topflight_clean import t1_clean
    return t1_clean(c,lo,hi)
def pairs(d):
    out={}; ss=sorted(d.Season.unique())
    for a,b in zip(ss,ss[1:]):
        if b!=a+1: continue
        A=d[d.Season==a].drop_duplicates('k').set_index('k').st; B=d[d.Season==b].drop_duplicates('k').set_index('k').st
        ix=A.index.intersection(B.index); out[a]=(np.array(A[ix].values,dtype=int),np.array(B[ix].values,dtype=int))
    return out
W=12
if __name__=='__main__':
    eng_pyr=pd.read_csv(sys.argv[1]); out=sys.argv[2]; rows=[]
    for c in FILES:
        PR=pairs(t1(c))
        for s in sorted(PR):
            if all((s+j) in PR for j in range(W)):
                o,n,g=G([PR[s+j] for j in range(W)],K=3,reps=120)
                rows.append(dict(country=c,start=s,mid=s+W/2,G=g))
    R=pd.DataFrame(rows); R.to_csv(f'{out}/rolling_G_topflight.csv',index=False)
    e=R[R.country=='ENG'].merge(eng_pyr[['start','G']].rename(columns={'G':'G_pyr'}),on='start')
    print(f"VALIDATION: England truncated vs pyramid rolling G, n={len(e)} windows: Pearson r = {np.corrcoef(e.G,e.G_pyr)[0,1]:.3f}")
    piv=R.pivot(index='start',columns='country',values='G')
    sel=[1958,1970,1981,1988,1994,2000,2006,2012]
    print(piv.loc[[s for s in sel if s in piv.index]].round(2).to_string())
