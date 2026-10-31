import numpy as np, pandas as pd, itertools
P=pd.read_csv('/tmp/fr/03/eng_tier_mobility_panel.csv')
def did(piv,tr,ct,cut,lo=1992,hi=2023):
    a=piv.loc[lo:cut-1]; b=piv.loc[cut:hi]
    return (b[tr].mean()-a[tr].mean())-(b[ct].mean()-a[ct].mean())
print("="*80)
print("RANDOMISATION INFERENCE — full placebo distribution over (unit, year)")
print("   real cell = tier 3 treated at 2011; every other (tier, year) is a placebo")
print("="*80)
for out in ['jump','churn','top6persist','exitrate']:
    piv=P.pivot(index='Season',columns='tier',values=out).dropna()
    real=np.mean([did(piv,3,c,2011) for c in [1,2,4]])
    dist=[]
    for tr in [1,2,3,4]:
        for y in range(1998,2019):
            if tr==3 and y==2011: continue
            ctrls=[c for c in [1,2,4] if c!=tr] if tr!=3 else [1,2,4]
            ctrls=[c for c in [1,2,3,4] if c!=tr]
            dist.append(np.mean([did(piv,tr,c,y) for c in ctrls]))
    dist=np.array(dist); p=np.mean(np.abs(dist)>=abs(real))
    mde=1.96*dist.std()
    print(f"\n {out:12s} observed (mean vs 3 controls) {real:+.4f}")
    print(f" {'':12s} placebo dist n={len(dist)}  sd {dist.std():.4f}  p = {p:.3f}")
    print(f" {'':12s} minimum detectable effect at 5% ≈ {mde:.4f}  ({abs(real)/mde:.2f}x of MDE observed)")
