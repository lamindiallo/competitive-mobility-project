import numpy as np, itertools
np.set_printoptions(suppress=True)

def state_of(p,b):
    for k,x in enumerate(b):
        if p<=x: return k
    return len(b)-1
def occ(b,N):
    n=np.zeros(len(b))
    for p in range(1,N+1): n[state_of(p,b)]+=1
    return n
def P_from_perm(s,b,N):
    K=len(b); n=occ(b,N); C=np.zeros((K,K))
    for i in range(1,N+1): C[state_of(i,b),state_of(s[i-1],b)]+=1
    return C/n[:,None]

def mfpt(P):
    """mean first passage times m[i][j], i!=j, for irreducible P"""
    K=len(P)
    w,v=np.linalg.eig(P.T); idx=np.argmin(abs(w-1)); pi=np.real(v[:,idx]); pi=pi/pi.sum()
    M=np.zeros((K,K))
    for j in range(K):
        idxs=[i for i in range(K) if i!=j]
        A=np.eye(len(idxs))-P[np.ix_(idxs,idxs)]
        sol=np.linalg.solve(A,np.ones(len(idxs)))
        for a,i in enumerate(idxs): M[i,j]=sol[a]
    return M, pi

# ---- Corollary of Result 1: mean RETURN time is fixed by construction (Kac) ----
print("=== Kac corollary: mean return time = N/n_k, fixed by construction ===")
N=20; bounds=[4,7,17,20]; n=occ(bounds,N); K=len(bounds)
print(f"occupancy={n.astype(int)}  N={N}   predicted return times N/n_k = {np.round(N/n,3)}")
rng=np.random.default_rng(1)
for label,gen in [("near-immobile",0.05),("moderate",0.5),("fully random",1.0)]:
    acc=np.zeros((K,K))
    for _ in range(6000):
        base=np.arange(1,N+1)
        if gen<1.0:
            s=base.copy()
            for _ in range(int(gen*N)):
                a,b_=rng.integers(0,N,2); s[a],s[b_]=s[b_],s[a]
        else: s=rng.permutation(base)
        acc+=P_from_perm(list(s),bounds,N)
    P=acc/6000
    M,pi=mfpt(P)
    ret=1/pi
    print(f"  {label:14s} pi={np.round(pi,4)}  return times={np.round(ret,3)}"
          f"   MFPT(bottom->top)={M[K-1,0]:.3f}")
print("\n=> return times IDENTICAL across regimes; MFPT bottom->top VARIES. \n")

# ---- Range of lambda2 under the occupancy constraint ----
print("=== what range can the mixing rate take? ===")
I=np.eye(K); PM=np.tile(n/N,(K,1))
rev=[N+1-i for i in range(1,N+1)]; Prev=P_from_perm(rev,bounds,N)
for lab,P in [("identity",I),("perfect mobility",PM),("full reversal",Prev)]:
    w=np.sort(abs(np.linalg.eigvals(P)))[::-1]
    print(f"  {lab:18s} |lambda2|={w[1]:.4f}")
print("=> lambda2 spans 0..1 => mixing rate IS informative (unlike pi).\n")

# ---- Absorbing state: two distinct quantities ----
print("=== absorbing 'below ladder' state: survival vs conditional mixing ===")
Ka=K+1
Pa=np.zeros((Ka,Ka))
Pa[:K,:K]=0.97*Prev; Pa[:K,K]=0.03; Pa[K,K]=1.0
Pa=Pa/Pa.sum(1,keepdims=True)
w=np.sort(abs(np.linalg.eigvals(Pa)))[::-1]
Q=Pa[:K,:K]
wq=np.sort(abs(np.linalg.eigvals(Q)))[::-1]
print(f"  full matrix eigenvalues (top3): {np.round(w[:3],4)}   <- lambda1=lambda2=1, reducible")
print(f"  transient sub-chain Q: rho(Q)={wq[0]:.4f} (absorption rate), "
      f"|lambda2(Q)|/rho={wq[1]/wq[0]:.4f} (conditional mixing)")
print("=> TWO distinct quantities. rho(Q)=survival; ratio=quasi-stationary convergence.")
