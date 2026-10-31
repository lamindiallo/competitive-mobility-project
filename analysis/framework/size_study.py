import numpy as np, pandas as pd
rng=np.random.default_rng(101)
tab=pd.read_csv('tables.csv')
def prize5(r):
    if r.tier==1: return 0 if r.pos<=4 else (1 if r.pos<=7 else 2)
    return 3 if r.tier==2 else 4
tab['state']=tab.apply(prize5,axis=1); K=5
def est(lo,hi):
    ss=[s for s in sorted(tab.Season.unique()) if lo<=s<=hi]
    prs=[(a,b) for a,b in zip(ss,ss[1:]) if b==a+1]
    C=np.zeros((K,K))
    for a,b in prs:
        A=tab[tab.Season==a].set_index('club').state; B=tab[tab.Season==b].set_index('club').state
        for c in A.index.intersection(B.index): C[A[c],B[c]]+=1
    return C/C.sum(1,keepdims=True)
P0=est(1981,1995)
occ=np.array([4,3,13,24,48]); N=int(occ.sum())
base=np.concatenate([[k]*occ[k] for k in range(K)])

def simulate(P,T):
    seq=[base.copy()]
    for _ in range(T-1):
        nxt=np.array([rng.choice(K,p=P[s]) for s in seq[-1]])
        order=np.argsort(nxt,kind='stable')
        fixed=np.empty(N,dtype=int); fixed[order]=base
        seq.append(fixed)
    return seq
def Cmat(seq):
    C=np.zeros((K,K))
    for a,b in zip(seq,seq[1:]):
        np.add.at(C,(a,b),1)
    return C
def stat(seq,trim=0.2):
    T=len(seq); best=0
    for t in range(int(trim*T),int((1-trim)*T)):
        C1,C2=Cmat(seq[:t]),Cmat(seq[t:]); s=0
        for i in range(K):
            n1,n2=C1[i].sum(),C2[i].sum()
            if n1<5 or n2<5: continue
            p1,p2,pp=C1[i]/n1,C2[i]/n2,(C1[i]+C2[i])/(n1+n2)
            m=pp>0
            s+=(((p1[m]-pp[m])**2/pp[m])*n1).sum()+(((p2[m]-pp[m])**2/pp[m])*n2).sum()
        best=max(best,s)
    return best

print("Resolving D135: is empirical size 0.12 Monte Carlo error or real distortion?\n")
print(f"{'null reps':>10s} {'crit(95%)':>10s} {'size @ independent draws':>26s}")
print("-"*50)
for R in [120, 400, 1200]:
    null=np.array([stat(simulate(P0,30)) for _ in range(R)])
    crit=np.percentile(null,95)
    # independent test draws
    test=np.array([stat(simulate(P0,30)) for _ in range(600)])
    print(f"{R:10d} {crit:10.1f} {(test>crit).mean():26.3f}")
