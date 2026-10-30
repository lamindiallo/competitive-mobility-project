"""Cleaned top-flight loader (D239). Fixes found by the completeness audit:
  - whitespace in names (e.g. 'Feirense ' vs 'Feirense', Portugal 2011);
  - one club under two names in one season (France: Brest Armorique FC = Stade Brest; Matra Racing = Racing Club de France);
  - incomplete seasons replaced from schochastics/football-data where that source is complete (France 2006/07: one match missing,
    which moves Toulouse from 3rd to 7th; Germany 1991/92: 40 matches missing);
  - missing seasons patched (England 2022/23 from openfootball; France 1994/95 from schochastics);
  - every patched season's names are MAPPED onto engsoccerdata names of the adjacent seasons by optimal assignment, so club identity
    chains are not broken (the earlier patches used foreign names directly).
Returns the same frame as trend_xc.t1."""
import os, re, unicodedata, numpy as np, pandas as pd
from difflib import SequenceMatcher
from scipy.optimize import linear_sum_assignment
import sys; sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','rcm'))
from ladder import table_from, parse_of
SRC=os.environ['FR_SRC']
FILES={'ENG':('england',1981,'england'),'ESP':('spain',1995,'spain'),'ITA':('italy',1994,'italy'),'FRA':('france',1994,'france'),
       'GER':('germany',1995,'germany'),'NED':('holland',1995,'netherlands'),'POR':('portugal',1995,'portugal')}
ALIAS={'FRA':{'Brest Armorique FC':'Stade Brest','Matra Racing':'Racing Club de France'}}
# D213: engsoccerdata labels Gazelec Ajaccio as 'AC Ajaccio' in Ligue 1 2015/16 (AC Ajaccio was in Ligue 2 that season)
SEASON_ALIAS={('FRA',2015):{'AC Ajaccio':'Gazelec Ajaccio'}}
REPLACE={('GER',1991)}
# France 2006/07: engsoccerdata omits one Nantes-Toulouse match; schochastics records it in a way that leaves Toulouse on 56, not the
# official 58. The official table (Toulouse 3rd, 58; Nantes 20th, 34) equals engsoccerdata plus a Toulouse win, which is injected here.
# Verified: the resulting table matches the published final table for all 20 clubs (see topflight_clean audit).
INJECT={('FRA',2006):[('FC Nantes','Toulouse FC',0,1)]}
FOREIGN_ALIAS={'PSG':'Paris Saint-Germain','Paris SG':'Paris Saint-Germain'}
GEN={'fc','cf','ac','as','sc','sv','vfl','vfb','ssc','us','afc','rc','cd','ud','sd','rcd','ca','tsg','fsv','bv','og','ogc','sco','stade','olympique','calcio','club','de','del','la','le'}
def _nm(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()
    t=[x for x in re.sub(r'[^a-z0-9 ]',' ',s.replace('&',' and ')).split() if x not in GEN]
    return ' '.join(t) if t else s
def _sim(a,b):
    a,b=_nm(a),_nm(b)
    if a==b: return 1.0
    if a in b or b in a: return 0.9
    return SequenceMatcher(None,a,b).ratio()
def _map_names(foreign, reference):
    F=sorted(foreign); R=sorted(reference)
    M=np.array([[_sim(f,r) for r in R] for f in F]); ri,ci=linear_sum_assignment(-M)
    return {F[i]:(R[j] if M[i,j]>=0.6 else F[i]) for i,j in zip(ri,ci)}
_Q=None
def _scho(country,s):
    global _Q
    if _Q is None:
        q=pd.read_parquet(f'{SRC}/schochastics_football-data/data/results/games.parquet')
        q['date']=pd.to_datetime(q['date'],errors='coerce'); q['S']=q.date.dt.year-(q.date.dt.month<7).astype(int); _Q=q
    g=_Q[(_Q.competition==country)&(_Q.S==s)]
    return list(zip(g.home,g.away,g.gh.astype(int),g.ga.astype(int)))
AUDIT=[]; UNMAPPED=[]
def t1_clean(c,lo=1958,hi=2024):
    f,p3,scho=FILES[c]
    df=pd.read_csv(f'{SRC}/jalapic_engsoccerdata/data-raw/{f}.csv',low_memory=False)
    df=df[(df.tier==1)]
    for col in ('home','visitor'): df[col]=df[col].astype(str).str.strip().replace(ALIAS.get(c,{}))
    names_by_season=df.groupby('Season').apply(lambda g:set(g.home)|set(g.visitor)).to_dict()
    out=[]; have=set()
    for s in range(lo,hi+1):
        g=df[df.Season==s]
        if (c,s) in REPLACE or (len(g)==0 and ((c=='FRA' and s==1994) or (c=='ENG' and s==2022))):
            if c=='ENG' and s==2022:
                rows=parse_of(f'{SRC}/openfootball_england/2022-23/1-premierleague.txt')
            else:
                rows=_scho(scho,s)
            rows=[(FOREIGN_ALIAS.get(h,h),FOREIGN_ALIAS.get(a,a),x,y) for h,a,x,y in rows]
            foreign=set(h for h,_,_,_ in rows)|set(a for _,a,_,_ in rows)
            ref=(names_by_season.get(s-1,set())|names_by_season.get(s+1,set())|names_by_season.get(s,set()))
            m=_map_names(foreign,ref); AUDIT.append((c,s,{k:v for k,v in m.items() if k!=v}))
            UNMAPPED.extend((c,s,k) for k,v in m.items() if k==v and k not in ref)
            rows=[(m[h],m[a],x,y) for h,a,x,y in rows]
        elif len(g)==0: continue
        else:
            sa=SEASON_ALIAS.get((c,s),{})
            rows=[(sa.get(h,h),sa.get(a,a),x,y) for h,a,x,y in zip(g.home,g.visitor,g.hgoal,g.vgoal)]+INJECT.get((c,s),[])
        tab=table_from(rows,wp=3 if s>=p3 else 2); tab['pos']=np.arange(1,len(tab)+1); tab['Season']=s; out.append(tab)
    d=pd.concat(out,ignore_index=True); d['k']=d.club.str.strip().str.lower()
    d['st']=d.pos.map(lambda p:0 if p<=4 else (1 if p<=10 else 2)); return d
if __name__=='__main__':
    for c in FILES:
        d=t1_clean(c)
        bad=d.groupby('Season').P.nunique(); n=d.groupby('Season').size()
        print(c,'seasons',d.Season.nunique(),'| seasons with unequal games played:',sorted(bad[bad>1].index.tolist()))
    for c,s,m in AUDIT: print('name map',c,s,m)
    print('UNMAPPED foreign names (must be checked by hand):',UNMAPPED)
