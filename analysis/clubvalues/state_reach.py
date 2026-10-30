"""State-level (not club-level) reach probabilities for the website: P(reach top four within h seasons | current state), England four tiers,
from the transition matrix of a chosen era. Compared with the mean first-passage time, which is dominated by long tails.
Usage: FR_SRC=<src> python -I state_reach.py <lo> <hi>"""
import os, sys, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(HERE,'..','rcm')); sys.path.insert(0,os.path.join(HERE,'..','trend'))
from ladder import eng_ladder
from clubkey import ck
from trend_eng import state, mfpt
lo,hi=int(sys.argv[1]),int(sys.argv[2])
lad=eng_ladder(4,lo,hi); lad['k']=lad.club.map(ck); lad['st']=lad.apply(state,axis=1)
ss=sorted(lad.Season.unique()); C=np.zeros((6,6))
for a,b in zip(ss,ss[1:]):
    if b!=a+1: continue
    A=lad[lad.Season==a].drop_duplicates('k').set_index('k').st; B=lad[lad.Season==b].drop_duplicates('k').set_index('k').st
    ix=A.index.intersection(B.index); np.add.at(C,(A[ix].values.astype(int),B[ix].values.astype(int)),1)
P=C/C.sum(1,keepdims=True)
Q=P.copy(); Q[0]=0; Q[0,0]=1          # make top four absorbing
names=['Top-flight top 4','Top flight 5th-10th','Top flight 11th-last','Tier 2','Tier 3','Tier 4']
print(f"England, transition matrix {lo}-{hi}")
print(f"{'current state':22s} {'P(top4 <=5 seasons)':>20s} {'<=10':>7s} {'<=20':>7s} {'mean wait':>10s}")
for i in range(1,6):
    p=[np.linalg.matrix_power(Q,h)[i,0] for h in (5,10,20)]
    print(f"{names[i]:22s} {p[0]:20.3f} {p[1]:7.3f} {p[2]:7.3f} {mfpt(P,i,0):10.1f}")

# Observed (model-free) frequency: share of club-seasons in each state whose club reached the top four within h seasons,
# for start seasons whose h-season horizon lies inside the data (1958-2024).
h=10; full=eng_ladder(4,1958,2024); full['k']=full.club.map(ck); full['st']=full.apply(state,axis=1)
top=set(zip(full[full.st==0].k,full[full.st==0].Season))
starts=full[(full.Season>=lo)&(full.Season<=min(hi,2024-h))]
print(f"\nObserved share reaching top four within {h} seasons (start seasons {lo}-{min(hi,2024-h)}):")
for i in range(1,6):
    g=starts[starts.st==i]; hit=[any((k,s+j) in top for j in range(1,h+1)) for k,s in zip(g.k,g.Season)]
    print(f"{names[i]:22s} {np.mean(hit):6.3f}   (n={len(g)})")
