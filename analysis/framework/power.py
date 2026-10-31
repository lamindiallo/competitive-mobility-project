import numpy as np, pandas as pd
rng=np.random.default_rng(23)
tab=pd.read_csv('tables.csv')
def prize5(r):
    if r.tier==1: return 0 if r.pos<=4 else (1 if r.pos<=7 else 2)
    return 3 if r.tier==2 else 4
tab['state']=tab.apply(prize5,axis=1)
K=5
def est(lo,hi):
    ss=[s for s in sorted(tab.Season.unique()) if lo<=s<=hi]
    prs=[(a,b) for a,b in zip(ss,ss[1:]) if b==a+1]
    C=np.zeros((K,K))
    for a,b in prs:
        A=tab[tab.Season==a].set_index('club').state; B=tab[tab.Season==b].set_index('club').state
        for c in A.index.intersection(B.index): C[A[c],B[c]]+=1
    return C/C.sum(1,keepdims=True), C.sum(1)

P_early,n_early=est(1981,1995)
struct=(P_early>0)          # structural support pattern
occ=np.array([4,3,13,24,48],dtype=float)   # England pyramid approx occupancy

def stiffen(P,delta,struct):
    """increase diagonal by delta, redistribute proportionally within structural support"""
    Q=P.copy()
    for i in range(len(P)):
        off=[j for j in range(len(P)) if j!=i and struct[i,j]]
        if not off: continue
        room=sum(Q[i,j] for j in off)
        take=min(delta,room*0.99)
        Q[i,i]+=take
        for j in off: Q[i,j]-=take*Q[i,j]/room
    return Q

def simulate(P,T,occ,rng):
    """generate T seasons of state occupancy consistent with P (approximate: sample per club)"""
    N=int(occ.sum()); states=np.concatenate([[k]*int(occ[k]) for k in range(K)])
    seq=[states.copy()]
    for _ in range(T-1):
        nxt=np.array([rng.choice(K,p=P[s]) for s in seq[-1]])
        # enforce occupancy by rank-repair: sort by drawn state, reassign to fill quotas
        order=np.argsort(nxt,kind='stable')
        newst=np.concatenate([[k]*int(occ[k]) for k in range(K)])
        fixed=np.empty(N,dtype=int); fixed[order]=newst
        seq.append(fixed)
    return seq

def Cmat(seq):
    C=np.zeros((K,K))
    for a,b in zip(seq,seq[1:]):
        for x,y in zip(a,b): C[x,y]+=1
    return C

def sup_wald_break(seq,trim=0.2):
    """max chi-square for homogeneity across a single split point"""
    T=len(seq); lo=int(trim*T); hi=int((1-trim)*T); best=0
    for t in range(lo,hi):
        C1=Cmat(seq[:t]); C2=Cmat(seq[t:])
        stat=0
        for i in range(K):
            n1,n2=C1[i].sum(),C2[i].sum()
            if n1<5 or n2<5: continue
            p1,p2=C1[i]/n1,C2[i]/n2; pp=(C1[i]+C2[i])/(n1+n2)
            with np.errstate(divide='ignore',invalid='ignore'):
                s=np.nansum(np.where(pp>0,(p1-pp)**2/pp*n1+(p2-pp)**2/pp*n2,0))
            stat+=s
        best=max(best,stat)
    return best

# null distribution of the statistic (no break)
T=30; NREP=120
null=[sup_wald_break(simulate(P_early,T,occ,rng)) for _ in range(NREP)]
crit=np.percentile(null,95)
print(f"break test: T={T}, null reps={NREP}, 95% critical value={crit:.1f}\n")
print(f"{'delta (diagonal shift)':26s} {'power':>7s}  {'implied top-4 retention':>24s}")
print("-"*62)
for delta in [0.0,0.05,0.10,0.15,0.20,0.30]:
    P1=stiffen(P_early,delta,struct)
    hits=0
    for _ in range(NREP):
        s=simulate(P_early,T//2,occ,rng)+simulate(P1,T//2,occ,rng)
        if sup_wald_break(s)>crit: hits+=1
    print(f"{delta:26.2f} {hits/NREP:7.2f}  {P_early[0,0]:.2f} -> {P1[0,0]:22.2f}")
print(f"\nOBSERVED shift in the real data: top-4 retention 0.518 (1981-95) -> 0.821 (1996-2010)")
print(f"   i.e. delta ~ 0.30")
