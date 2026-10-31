import numpy as np, pandas as pd, itertools
P=pd.read_csv('/tmp/fr/03/eng_tier_mobility_panel.csv')
piv=P.pivot(index='Season',columns='tier',values='raw')
def did(treat,ctrl,cut,lo=1992,hi=2023,piv=piv):
    a=piv.loc[lo:cut-1]; b=piv.loc[cut:hi]
    return (b[treat].mean()-a[treat].mean())-(b[ctrl].mean()-a[ctrl].mean())
print("="*74)
print("DESIGN 1 — League One SCMP adoption 2011/12, outcome: mean |Δladder rank|")
print("="*74)
for c,name in [(4,'League Two (already treated 2003/04)'),(2,'Championship (not-yet-treated)'),(1,'Premier League (never SCMP)')]:
    d=did(3,c,2011)
    print(f"  tier 3 vs tier {c}  DiD = {d:+.3f}   {name}")
print("\n  Pre/post means:")
for t in [1,2,3,4]:
    print(f"   tier {t}: pre {piv.loc[1992:2010,t].mean():.2f}  post {piv.loc[2011:2023,t].mean():.2f}  diff {piv.loc[2011:2023,t].mean()-piv.loc[1992:2010,t].mean():+.2f}")

print("\n"+"="*74)
print("RANDOMISATION INFERENCE — placebo adoption years, tier 3 vs tier 4")
print("="*74)
real=did(3,4,2011)
pl=[did(3,4,y) for y in range(1998,2019)]
p=np.mean([abs(x)>=abs(real) for x in pl])
print(f"  observed DiD (2011) = {real:+.3f}")
print(f"  placebo years 1998-2018: mean {np.mean(pl):+.3f}, sd {np.std(pl):.3f}, range {min(pl):+.3f} to {max(pl):+.3f}")
print(f"  share of placebo years with |DiD| >= observed: {p:.2f}")

print("\n  PLACEBO UNITS at 2011 (each tier against each other tier):")
for a,b in itertools.permutations([1,2,3,4],2):
    print(f"    tier {a} vs {b}: {did(a,b,2011):+.3f}")

print("\n"+"="*74)
print("EVENT STUDY — tier 3 minus tier 4, relative to 2011")
print("="*74)
d=piv[3]-piv[4]
base=d.loc[2006:2010].mean()
for y in range(2006,2019):
    if y in d.index:
        print(f"   {y-2011:+3d}  {d[y]-base:+6.2f}")
