import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from names import *
from alias import ALIAS
def key(c,name):
    n=norm(name); return ALIAS[c].get(n,n)
def build(c,f,lo=1992,hi=2024):
    t1=t1_tables(c,f'/tmp/fr/{f}.csv',lo,hi); t2=t2_tables(c)
    t2=t2[(t2.Season>=lo)&(t2.Season<=hi)]
    for d in (t1,t2): d['k']=[key(c,x) for x in d.club]
    return pd.concat([t1,t2],ignore_index=True)
if __name__=='__main__':
    for c,f in [('fr','france'),('es','spain'),('it','italy')]:
        lad=build(c,f)
        print('='*14,c)
        yrs=sorted(set(lad[lad.tier==1].Season)&set(lad[lad.tier==2].Season))
        tot=miss=0
        for y in yrs:
            if y+1 not in yrs: continue
            a1=set(lad[(lad.Season==y)&(lad.tier==1)].k); b1=set(lad[(lad.Season==y+1)&(lad.tier==1)].k)
            b2=set(lad[(lad.Season==y+1)&(lad.tier==2)].k)
            rel=a1-b1; tot+=len(rel)
            lost=rel-b2
            if lost:
                miss+=len(lost); print(f'  {y}->{y+1} relegated not found in tier2: {sorted(lost)}')
        print(f'  seasons {yrs[0]}-{yrs[-1]}  relegations {tot}  unmatched {miss} ({100*miss/max(tot,1):.1f}%)')
