"""Club-cluster bootstrap CIs for top-flight resource-conditional reach, and the England-France gap. Usage: xc_reach_ci.py xc_panel.csv"""
import sys, numpy as np, pandas as pd
P=pd.read_csv(sys.argv[1]); rng=np.random.default_rng(21)
P=P[P.Season>=2004]; pres=set(zip(P.country,P.ewclub,P.Season))
P['win_ok']=[((c,k,s-1) in pres) and ((c,k,s-2) in pres) for c,k,s in zip(P.country,P.ewclub,P.Season)]
P=P[P.Season>=2006].copy(); P['res']=P.groupby(['country','Season']).R3.rank(ascending=False)
recs={}
for c in ['ENG','ESP','ITA','GER','FRA']:
    D=P[P.country==c]; out=[]
    for s in sorted(D.Season.unique()):
        if s+5>D.Season.max(): continue
        hit=set(D[(D.Season>s)&(D.Season<=s+5)&(D.pos<=4)].ewclub)
        for r in D[(D.Season==s)&D.win_ok].itertuples():
            if r.pos>4: out.append((r.ewclub,r.res,r.ewclub in hit))
    recs[c]=pd.DataFrame(out,columns=['k','res','hit'])
def band(O,a,b): return O[(O.res>=a)&(O.res<b+1)]
def boot(O,B=1000):
    ks=O.k.unique(); g={k:O[O.k==k] for k in ks}
    return np.array([pd.concat([g[k] for k in rng.choice(ks,len(ks))]).hit.mean() for _ in range(B)])
print(f"{'':4s} {'ranks 5-8':>26s} {'ranks 9-20 (pooled)':>28s}")
bs={}
for c,O in recs.items():
    row=[]
    for (a,b) in [(5,8),(9,20)]:
        sub=band(O,a,b); x=boot(sub); bs[(c,a)]=x
        row.append(f"{sub.hit.mean():.2f} [{np.percentile(x,2.5):.2f},{np.percentile(x,97.5):.2f}] n={len(sub):3d}")
    print(f"{c:4s} "+"   ".join(row))
for a in (5,9):
    d=bs[('FRA',a)]-bs[('ENG',a)]
    print(f"FRA minus ENG, band starting {a}: {d.mean():+.2f}  95% CI [{np.percentile(d,2.5):+.2f},{np.percentile(d,97.5):+.2f}]  P(diff<=0)={np.mean(d<=0):.3f}")
