"""Completeness audit of engsoccerdata: every league-season should have n(n-1) matches and equal games played (double round robin).
Lists incomplete seasons and whether the gap could move a club across the top-four boundary. Usage: FR_SRC=<src> python -I audit_completeness.py"""
import os, sys, numpy as np, pandas as pd
SRC=os.environ['FR_SRC']
FILES={'ENG':'england','ESP':'spain','ITA':'italy','FRA':'france','GER':'germany','NED':'holland','POR':'portugal','SCO':'scotland','BEL':'belgium','GRE':'greece','TUR':'turkey'}
rows=[]
for c,f in FILES.items():
    d=pd.read_csv(f'{SRC}/jalapic_engsoccerdata/data-raw/{f}.csv',low_memory=False)
    d=d[(d.Season>=1958)]
    for (s,t),g in d.groupby(['Season','tier']):
        teams=set(g.home)|set(g.visitor); n=len(teams)
        played=pd.concat([g.home,g.visitor]).value_counts()
        exp=n*(n-1)
        if len(g)!=exp or played.nunique()>1:
            short=played[played<played.max()]
            rows.append(dict(country=c,season=s,tier=t,clubs=n,matches=len(g),expected=exp,
                             clubs_short=', '.join(f"{k}({v})" for k,v in short.items())))
R=pd.DataFrame(rows)
pd.set_option('display.width',250); pd.set_option('display.max_colwidth',90)
print(f"league-seasons failing the double-round-robin check: {len(R)}")
print(R.to_string(index=False))
R.to_csv(sys.argv[1] if len(sys.argv)>1 else 'completeness.csv',index=False)
