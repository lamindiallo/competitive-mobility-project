import pandas as pd, numpy as np
rng=np.random.default_rng(31)

def tables(fn,lo=1958,hi=2024):
    df=pd.read_csv(fn,low_memory=False)
    df=df[df.tier.isin([1,2])]
    out=[]
    for (s,t),g in df.groupby(['Season','tier']):
        if s<lo or s>hi: continue
        wp=3 if s>=1995 else 2      # 3pts: ENG 1981, most of Europe by 1995
        r={}
        for _,x in g.iterrows():
            for tm,gf,ga in ((x.home,x.hgoal,x.vgoal),(x.visitor,x.vgoal,x.hgoal)):
                d=r.setdefault(tm,[0,0,0]); d[0]+= (wp if gf>ga else (1 if gf==ga else 0)); d[1]+=gf-ga; d[2]+=gf
        tt=pd.DataFrame([(k,v[0],v[1],v[2]) for k,v in r.items()],columns=['club','Pts','GD','GF'])
        tt=tt.sort_values(['Pts','GD','GF'],ascending=False).reset_index(drop=True)
        tt['pos']=np.arange(1,len(tt)+1); tt['Season']=s; tt['tier']=t
        out.append(tt)
    return pd.concat(out,ignore_index=True)

def mfpt(P,i,j):
    K=len(P); idx=[x for x in range(K) if x!=j]
    A=np.eye(len(idx))-P[np.ix_(idx,idx)]
    return np.linalg.solve(A,np.ones(len(idx)))[idx.index(i)]

def run(tab,states_fn,K,lo,hi,reps=200):
    tb=tab.copy(); tb['state']=tb.apply(states_fn,axis=1)
    ss=sorted(x for x in tb.Season.unique() if lo<=x<=hi)
    prs=[(a,b) for a,b in zip(ss,ss[1:]) if b==a+1]
    if len(prs)<8: return None
    C=np.zeros((K,K))
    for a,b in prs:
        A=tb[tb.Season==a].set_index('club').state; B=tb[tb.Season==b].set_index('club').state
        for c in A.index.intersection(B.index): C[A[c],B[c]]+=1
    if (C.sum(1)==0).any(): return None
    P=C/C.sum(1,keepdims=True)
    try: o=mfpt(P,K-1,0)
    except Exception: return None
    nv=[]
    for _ in range(reps):
        Cn=np.zeros((K,K))
        for a,b in prs:
            A=tb[tb.Season==a].set_index('club').state; B=tb[tb.Season==b].set_index('club').state
            cm=list(A.index.intersection(B.index)); pm=rng.permutation(B[cm].values)
            for c,s2 in zip(cm,pm): Cn[A[c],s2]+=1
        Pn=Cn/Cn.sum(1,keepdims=True)
        try: nv.append(mfpt(Pn,K-1,0))
        except Exception: pass
    return o,np.mean(nv),o/np.mean(nv),len(prs),P

# state functions
def t1only(r):   # 3 states, TIER 1 ONLY -> relegated clubs vanish (the standard flawed approach)
    return 0 if r.pos<=4 else (1 if r.pos<=10 else 2)
def pyramid(r):  # 4 states spanning both tiers
    if r.tier==1: return 0 if r.pos<=4 else (1 if r.pos<=10 else 2)
    return 3

files={'ENG':'england.csv','FRA':'france.csv','ESP':'spain.csv','ITA':'italy.csv','GER':'germany.csv'}
print("="*78)
print("A. TIER-1-ONLY  (relegated clubs leave the panel — the standard approach)")
print("="*78)
print(f"{'country':8s} {'pairs':>6s} {'obs':>8s} {'null':>7s} {'G':>7s}")
store={}
for c,f in files.items():
    tab=tables(f); store[c]=tab
    t1=tab[tab.tier==1]
    r=run(t1,t1only,3,1992,2024)
    if r: print(f"{c:8s} {r[3]:6d} {r[0]:8.1f} {r[1]:7.1f} {r[2]:7.2f}")
    else: print(f"{c:8s}  -- insufficient")

print("\n"+"="*78)
print("B. PYRAMID-WIDE (tiers 1-2; relegation is a transition) — only ENG and GER possible")
print("="*78)
print(f"{'country':8s} {'pairs':>6s} {'obs':>8s} {'null':>7s} {'G':>7s}")
for c in ['ENG','GER']:
    tab=store[c][store[c].tier.isin([1,2])]
    r=run(tab,pyramid,4,1992,2024)
    if r: print(f"{c:8s} {r[3]:6d} {r[0]:8.1f} {r[1]:7.1f} {r[2]:7.2f}")

print("\n"+"="*78)
print("C. LIKE-FOR-LIKE: MFPT from SAME source state (tier1 pos 11-20) to top 4")
print("   truncated (tier-1 only) vs pyramid-wide (tiers 1-2)")
print("="*78)
def pyr4(r):
    if r.tier==1: return 0 if r.pos<=4 else (1 if r.pos<=10 else 2)
    return 3
print(f"{'country':8s} {'truncated':>11s} {'pyramid':>9s} {'ratio':>7s}   interpretation")
for c in ['ENG','GER']:
    tab=store[c]
    # truncated: tier1 only, K=3, source=state2 (pos 11-20)
    t1=tab[tab.tier==1].copy(); t1['state']=t1.apply(t1only,axis=1)
    ss=[x for x in sorted(t1.Season.unique()) if 1992<=x<=2024]
    prs=[(a,b) for a,b in zip(ss,ss[1:]) if b==a+1]
    C=np.zeros((3,3))
    for a,b in prs:
        A=t1[t1.Season==a].set_index('club').state; B=t1[t1.Season==b].set_index('club').state
        for x in A.index.intersection(B.index): C[A[x],B[x]]+=1
    Pt=C/C.sum(1,keepdims=True); trunc=mfpt(Pt,2,0)
    # pyramid: K=4, source=state2 (tier1 pos 11-20) -> top4
    tb=tab[tab.tier.isin([1,2])].copy(); tb['state']=tb.apply(pyr4,axis=1)
    C2=np.zeros((4,4))
    for a,b in prs:
        A=tb[tb.Season==a].set_index('club').state; B=tb[tb.Season==b].set_index('club').state
        for x in A.index.intersection(B.index): C2[A[x],B[x]]+=1
    Pp=C2/C2.sum(1,keepdims=True); pyr=mfpt(Pp,2,0)
    tag = "truncation UNDERstates immobility" if trunc<pyr else "truncation OVERstates immobility"
    print(f"{c:8s} {trunc:11.2f} {pyr:9.2f} {pyr/trunc:7.2f}   {tag}")
