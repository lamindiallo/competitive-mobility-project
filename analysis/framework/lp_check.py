import itertools, numpy as np
from scipy.optimize import linprog

def state_of(pos,bounds):
    for k,b in enumerate(bounds):
        if pos<=b: return k
    return len(bounds)-1
def occ(bounds,N):
    n=np.zeros(len(bounds))
    for p in range(1,N+1): n[state_of(p,bounds)]+=1
    return n

def max_jump_LP(n):
    """max mean |j-k| flow subject to row sums n_j and col sums n_k (transportation LP)"""
    K=len(n); N=n.sum()
    c=-np.array([abs(j-k) for j in range(K) for k in range(K)],dtype=float)  # maximise
    A=[];b=[]
    for j in range(K):
        r=np.zeros(K*K); r[j*K:(j+1)*K]=1; A.append(r); b.append(n[j])
    for k in range(K):
        r=np.zeros(K*K); r[k::K]=1; A.append(r); b.append(n[k])
    res=linprog(c,A_eq=np.array(A),b_eq=np.array(b),bounds=(0,None),method="highs")
    return -res.fun/N

def max_jump_exhaustive(bounds,N):
    best=0
    for s in itertools.permutations(range(1,N+1)):
        v=sum(abs(state_of(i,bounds)-state_of(s[i-1],bounds)) for i in range(1,N+1))/N
        best=max(best,v)
    return best

print("=== LP vs exhaustive enumeration ===")
for bb,NN in [([2,5,8],8),([3,6,9],9),([2,4,6,8],8),([1,3,5,7,9],9),([2,3,6,8],8)]:
    n=occ(bb,NN); e=max_jump_exhaustive(bb,NN); l=max_jump_LP(n)
    print(f"occ={n.astype(int)}  exhaustive={e:.6f}  LP={l:.6f}  match={np.isclose(e,l)}")

print("\n=== realistic Premier League cases (K=5, prize-structure boundaries) ===")
# 20 clubs: champion+CL (1-4), Europa (5-7), mid (8-17), releg (18-20) -> K=4
for label,n in [("EPL K=4 [4,3,10,3]",np.array([4,3,10,3.])),
                ("EPL K=5 [1,3,3,10,3]",np.array([1,3,3,10,3.])),
                ("equal K=5 (N=20)",np.array([4,4,4,4,4.])),
                ("pyramid K=5 (N=44, E+Champ)",np.array([4,3,13,13,11.]))]:
    K=len(n)
    print(f"{label:32s} maxjump={max_jump_LP(n):.4f}   (K-1)={K-1}  K/2={K/2}")
