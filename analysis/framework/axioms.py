import itertools, numpy as np
from math import comb

def state_of(pos, bounds):
    """bounds: cumulative upper positions of each state, e.g. [4,7,17,20]"""
    for k,b in enumerate(bounds):
        if pos <= b: return k
    return len(bounds)-1

def occupancy(bounds, N):
    n = np.zeros(len(bounds))
    for p in range(1, N+1): n[state_of(p,bounds)] += 1
    return n

def P_from_perm(sigma, bounds, N):
    """sigma[i] = new position of club currently at position i+1"""
    K = len(bounds); n = occupancy(bounds,N)
    C = np.zeros((K,K))
    for i in range(1, N+1):
        C[state_of(i,bounds), state_of(sigma[i-1],bounds)] += 1
    return C / n[:,None], n

# ---------- RESULT 1: is occupancy always a left eigenvector? ----------
print("=== RESULT 1: occupancy vector is always stationary ===")
N=8; bounds=[2,5,8]
viol=0; tested=0
for sigma in itertools.islice(itertools.permutations(range(1,N+1)), 4000):
    P,n = P_from_perm(list(sigma), bounds, N)
    tested+=1
    if not np.allclose(n @ P, n, atol=1e-9): viol+=1
print(f"N={N}, states occupancy={occupancy(bounds,N)}, permutations tested={tested}, violations={viol}")

# pooled average of many permutations
rng=np.random.default_rng(0)
acc=np.zeros((3,3))
for _ in range(2000):
    s=list(rng.permutation(np.arange(1,N+1)))
    P,n=P_from_perm(s,bounds,N); acc+=P
Pbar=acc/2000
print("pooled P-bar row sums:", Pbar.sum(1))
print("n @ Pbar  =", np.round(n@Pbar,6), " vs n =", n)
print("=> stationary distribution is FIXED BY CONSTRUCTION\n")

# ---------- RESULT 2: are both extremes feasible? does impossibility bite? ----------
print("=== RESULT 2: feasibility of the extremes ===")
K=3; n=occupancy(bounds,N)
I3=np.eye(K)
PM=np.tile(n/N,(K,1))                      # perfect mobility: rows = occupancy shares
print("Identity  I: n@I == n ?", np.allclose(n@I3,n))
print("PerfMob ixp: n@P == n ?", np.allclose(n@PM,n), " rows:", np.round(PM[0],4))

# the full reversal permutation
rev=[N+1-i for i in range(1,N+1)]
Prev,_=P_from_perm(rev,bounds,N)
print("\nreversal permutation P:\n", np.round(Prev,3))
print("n@Prev == n ?", np.allclose(n@Prev,n))

# Is reversal strictly MORE mobile than PM in the monotone (off-diagonal mass) sense?
def offdiag_mass(P,n): return float(((1-np.eye(len(n)))*P*n[:,None]).sum()/n.sum())
print(f"\noff-diagonal mass  identity={offdiag_mass(I3,n):.4f}"
      f"  perfect-mobility={offdiag_mass(PM,n):.4f}  reversal={offdiag_mass(Prev,n):.4f}")

# Shorrocks trace index on each
def M1(P): K=len(P); return (K-np.trace(P))/(K-1)
print(f"M1(identity)={M1(I3):.4f}  M1(PM)={M1(PM):.4f}  M1(reversal)={M1(Prev):.4f}")
print("\n=> If (PM) sets M=1 at perfect mobility and (M) is monotone,")
print("   the REVERSAL is strictly more mobile and forces M>1, breaking (N).")
print("   THE IMPOSSIBILITY BITES.\n")

# ---------- RESULT 3: maximum mean absolute STATE jump ----------
print("=== RESULT 3: max mean absolute state jump over permutations ===")
def max_state_jump(bounds,N,exhaustive_limit=9):
    K=len(bounds); n=occupancy(bounds,N)
    best=0
    if N<=exhaustive_limit:
        for sigma in itertools.permutations(range(1,N+1)):
            v=sum(abs(state_of(i,bounds)-state_of(sigma[i-1],bounds)) for i in range(1,N+1))/N
            best=max(best,v)
    return best,n

for bb,NN in [([2,5,8],8),([3,6,9],9),([2,4,6,8],8),([1,3,5,7,9],9)]:
    b,n=max_state_jump(bb,NN)
    K=len(bb)
    # candidate closed forms
    print(f"bounds={bb} N={NN} K={K} occ={n.astype(int)}  MAXmeanjump={b:.4f}"
          f"   [(K-1)={K-1}]  [K/2={K/2}]")
