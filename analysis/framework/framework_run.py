import pandas as pd, numpy as np
from scipy.optimize import linprog
rng=np.random.default_rng(7)
tab=pd.read_csv('tables.csv')

# ---------- ladder ----------
sizes=tab.groupby(['Season','tier']).size().rename('n').reset_index()
piv=sizes.pivot(index='Season',columns='tier',values='n')
def ladder(row):
    off=0
    for t in range(1,int(row.tier)):
        off+=piv.loc[row.Season,t] if t in piv.columns and not pd.isna(piv.loc[row.Season,t]) else 0
    return off+row.pos
tab['ladder']=tab.apply(ladder,axis=1)
tab['Nseason']=tab.Season.map(tab.groupby('Season').size())

# ---------- states (prize structure) ----------
def state(r):
    if r.tier==1:
        if r.pos<=4: return 0
        if r.pos<=7: return 1
        return 2
    if r.tier==2: return 3
    return 4
tab['state']=tab.apply(state,axis=1)
K=5

# ---------- transition matrix, consecutive seasons only ----------
def transitions(t0,t1,lo,hi):
    seasons=sorted(x for x in tab.Season.unique() if lo<=x<=hi)
    pairs=[(a,b) for a,b in zip(seasons,seasons[1:]) if b==a+1]
    skipped=[(a,b) for a,b in zip(seasons,seasons[1:]) if b!=a+1]
    C=np.zeros((K,K)); n=np.zeros(K)
    for a,b in pairs:
        A=tab[tab.Season==a].set_index('club').state
        B=tab[tab.Season==b].set_index('club').state
        common=A.index.intersection(B.index)
        for c in common: C[A[c],B[c]]+=1
        for c in A.index: n[A[c]]+=1
    return C,n,pairs,skipped

C,n,pairs,skipped=transitions(None,None,1992,2024)
print(f"season pairs used: {len(pairs)}   BROKEN (gap) pairs excluded: {skipped}")
P=C/C.sum(1,keepdims=True)
print("\nEngland pyramid transition matrix, K=5, 1992-2024")
print("states: 0=T1 top4  1=T1 5-7  2=T1 8-20  3=Tier2  4=Tier3/4")
print(np.round(P,3))
print("row counts:",C.sum(1).astype(int))

def mfpt(P,i,j):
    K=len(P); idxs=[x for x in range(K) if x!=j]
    A=np.eye(len(idxs))-P[np.ix_(idxs,idxs)]
    sol=np.linalg.solve(A,np.ones(len(idxs)))
    return sol[idxs.index(i)]

obs=mfpt(P,4,0)
print(f"\nOBSERVED expected seasons: bottom state (tier 3/4) -> top 4 of tier 1 = {obs:.1f}")

# ---------- permutation null ----------
def null_matrix(lo,hi,reps=300):
    seasons=sorted(x for x in tab.Season.unique() if lo<=x<=hi)
    prs=[(a,b) for a,b in zip(seasons,seasons[1:]) if b==a+1]
    vals=[]
    for _ in range(reps):
        C=np.zeros((K,K))
        for a,b in prs:
            A=tab[tab.Season==a].set_index('club').state
            B=tab[tab.Season==b].set_index('club').state
            common=list(A.index.intersection(B.index))
            perm=rng.permutation(B[common].values)   # break the link, keep marginals
            for c,newst in zip(common,perm): C[A[c],newst]+=1
        Pn=C/C.sum(1,keepdims=True)
        try: vals.append(mfpt(Pn,4,0))
        except Exception: pass
    return np.array(vals)

nullv=null_matrix(1992,2024,300)
print(f"NULL (random reassignment): mean={nullv.mean():.2f}  95% CI=[{np.percentile(nullv,2.5):.2f},{np.percentile(nullv,97.5):.2f}]")
print(f"\n*** G = observed / null = {obs/nullv.mean():.2f}x  ***")
print(f"permutation p-value (obs >= null): {(nullv>=obs).mean():.4f}")

print("\n"+"="*70)
print("VALIDATION SUITE")
print("="*70)

# --- V1: Result 1 empirical check: is occupancy stationary on REAL data? ---
occ=np.array([C.sum(1)[k] for k in range(K)],dtype=float)
pi_emp=occ/occ.sum()
w,v=np.linalg.eig(P.T); i=np.argmin(abs(w-1)); pi=np.real(v[:,i]); pi/=pi.sum()
print(f"\nV1 Result-1 check (stationary = occupancy shares?)")
print(f"   occupancy shares : {np.round(pi_emp,4)}")
print(f"   stationary of P  : {np.round(pi,4)}   maxdiff={np.abs(pi-pi_emp).max():.4f}")

# --- V2: Kac check: mean return time = 1/pi ---
print(f"\nV2 Result-4 check (return times = 1/pi, uninformative)")
print(f"   1/pi = {np.round(1/pi,2)}  vs N/n_k = {np.round(occ.sum()/occ,2)}")

# --- V3: external check vs Manasis & Ntzoufras (top-5 distinct clubs, 5-yr window) ---
print(f"\nV3 EXTERNAL CHECK — distinct clubs in tier-1 top 5 over rolling 5 seasons")
print("   (Manasis & Ntzoufras report 15 for 1991, ~6 for 2008, 8 for 2012)")
t1=tab[tab.tier==1]
for end in [1991,1995,2000,2005,2008,2012,2019,2024]:
    yrs=[y for y in range(end-4,end+1) if y in set(t1.Season)]
    if len(yrs)<5: continue
    clubs=set(t1[(t1.Season.isin(yrs))&(t1.pos<=5)].club)
    print(f"   window ending {end}: {len(clubs)} distinct clubs in top 5")

# --- V4: H2 trend — split-period comparison ---
print(f"\nV4 H2 trend test — MFPT(bottom->top4) by era")
for lo,hi in [(1958,1980),(1981,1995),(1996,2010),(2011,2024)]:
    Ce,_,prs,_=transitions(None,None,lo,hi)
    if Ce.sum()==0 or len(prs)<8: continue
    Pe=Ce/Ce.sum(1,keepdims=True)
    try: m=mfpt(Pe,4,0)
    except Exception: m=float('nan')
    print(f"   {lo}-{hi} ({len(prs)} pairs): MFPT={m:8.1f}   top4 retention={Pe[0,0]:.3f}")

# --- V5: discriminant validity — within-season concentration vs mobility ---
print(f"\nV5 Discriminant check — within-season points concentration (tier 1) by era")
for lo,hi in [(1981,1995),(1996,2010),(2011,2024)]:
    sub=t1[(t1.Season>=lo)&(t1.Season<=hi)]
    hh=sub.groupby('Season').apply(lambda g: ((g.Pts/g.Pts.sum())**2).sum()*len(g), include_groups=False)
    print(f"   {lo}-{hi}: normalised HHI mean={hh.mean():.4f}")
