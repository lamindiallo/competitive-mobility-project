import pandas as pd, numpy as np
rng=np.random.default_rng(11)
tab=pd.read_csv('tables.csv')
piv=tab.groupby(['Season','tier']).size().unstack()

def mfpt(P,i,j):
    K=len(P); idxs=[x for x in range(K) if x!=j]
    A=np.eye(len(idxs))-P[np.ix_(idxs,idxs)]
    return np.linalg.solve(A,np.ones(len(idxs)))[idxs.index(i)]

def build(states_fn,K,lo,hi,tiers,shrink=0.0):
    sub=tab[tab.tier.isin(tiers)].copy()
    sub['state']=sub.apply(states_fn,axis=1)
    seasons=sorted(sub.Season.unique()); seasons=[s for s in seasons if lo<=s<=hi]
    prs=[(a,b) for a,b in zip(seasons,seasons[1:]) if b==a+1]
    C=np.zeros((K,K))
    for a,b in prs:
        A=sub[sub.Season==a].set_index('club').state; B=sub[sub.Season==b].set_index('club').state
        for c in A.index.intersection(B.index): C[A[c],B[c]]+=1
    marg=C.sum(0)/C.sum()
    P=(C+shrink*C.sum(1,keepdims=True)*marg)/ (C.sum(1,keepdims=True)*(1+shrink))
    return P,C,prs,sub

def nullval(sub,K,lo,hi,reps=200):
    seasons=sorted(x for x in sub.Season.unique() if lo<=x<=hi)
    prs=[(a,b) for a,b in zip(seasons,seasons[1:]) if b==a+1]
    v=[]
    for _ in range(reps):
        C=np.zeros((K,K))
        for a,b in prs:
            A=sub[sub.Season==a].set_index('club').state; B=sub[sub.Season==b].set_index('club').state
            cm=list(A.index.intersection(B.index)); perm=rng.permutation(B[cm].values)
            for c,s in zip(cm,perm): C[A[c],s]+=1
        P=C/C.sum(1,keepdims=True)
        try: v.append(mfpt(P,K-1,0))
        except Exception: pass
    return np.array(v)

# ---- state definitions ----
def prize5(r):
    if r.tier==1: return 0 if r.pos<=4 else (1 if r.pos<=7 else 2)
    return 3 if r.tier==2 else 4
def prize4(r):
    if r.tier==1: return 0 if r.pos<=4 else 1
    return 2 if r.tier==2 else 3
def prize6(r):
    if r.tier==1: return 0 if r.pos<=4 else (1 if r.pos<=7 else 2)
    if r.tier==2: return 3
    return 4 if r.tier==3 else 5
def quant(K):
    def f(r):
        lad=r._ladder; N=r._N
        return min(int(lad/N*K),K-1)
    return f
def prize3_t12(r):     # tiers 1-2 only
    if r.tier==1: return 0 if r.pos<=4 else 1
    return 2

print(f"{'specification':42s} {'K':>2s} {'obs':>8s} {'null':>7s} {'G':>6s}")
print("-"*72)
rows=[]
for lab,fn,K,tiers in [
    ("prize, tiers1-4 (headline)",prize5,5,[1,2,3,4]),
    ("prize, tiers1-4, K=4",prize4,4,[1,2,3,4]),
    ("prize, tiers1-4, K=6",prize6,6,[1,2,3,4]),
    ("prize, tiers1-2 only",prize3_t12,3,[1,2]),
]:
    P,C,prs,sub=build(fn,K,1992,2024,tiers)
    o=mfpt(P,K-1,0); nv=nullval(sub,K,1992,2024)
    print(f"{lab:42s} {K:2d} {o:8.1f} {nv.mean():7.1f} {o/nv.mean():6.2f}")
    rows.append((lab,o,nv.mean(),o/nv.mean()))

# equal-quantile boundaries
tab['_N']=tab.Season.map(tab.groupby('Season').size())
off={}
for s in tab.Season.unique():
    c=0
    for t in [1,2,3,4]:
        off[(s,t)]=c
        c+= piv.loc[s,t] if t in piv.columns and not pd.isna(piv.loc[s,t]) else 0
tab['_ladder']=[off[(r.Season,r.tier)]+r.pos for r in tab.itertuples()]
for K in [4,5,6]:
    P,C,prs,sub=build(quant(K),K,1992,2024,[1,2,3,4])
    o=mfpt(P,K-1,0); nv=nullval(sub,K,1992,2024)
    print(f"{'equal quantiles':42s} {K:2d} {o:8.1f} {nv.mean():7.1f} {o/nv.mean():6.2f}")
    rows.append((f"equal quantiles K={K}",o,nv.mean(),o/nv.mean()))

# shrinkage
for sh in [0.0,0.05,0.2]:
    P,C,prs,sub=build(prize5,5,1992,2024,[1,2,3,4],shrink=sh)
    o=mfpt(P,4,0)
    print(f"{'prize K=5, shrinkage='+str(sh):42s} {5:2d} {o:8.1f} {'-':>7s} {'-':>6s}")

print("\nG values across all specifications:", [f"{r[3]:.2f}" for r in rows])
print(f"min G={min(r[3] for r in rows):.2f}   max G={max(r[3] for r in rows):.2f}")
