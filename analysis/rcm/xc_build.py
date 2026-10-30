"""Cross-country top-flight resource panel (transfer-spend proxy), 2004-2022. Matches ewenme clubs to engsoccerdata tables per season by optimal assignment on name similarity."""
import os, re, sys, unicodedata, numpy as np, pandas as pd
from difflib import SequenceMatcher
from scipy.optimize import linear_sum_assignment
SRC=os.environ['FR_SRC']
CFG={'ENG':('england','premier-league',1981),'FRA':('france','ligue-1',1994),'GER':('germany','1-bundesliga',1995),
     'ITA':('italy','serie-a',1994),'ESP':('spain','primera-division',1995)}
GEN={'fc','cf','ac','as','sc','sv','vfl','vfb','ssc','us','afc','rc','cd','ud','sd','rcd','ca','tsg','fsv','bv','og','ogc','sco','stade','olympique','calcio','club','de','del','la','le','1','04','05','09','1846','1848','1899','1900','1907','1909','1913','1896','1910'}
def nm(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()
    s=re.sub(r'[^a-z0-9 ]',' ',s.replace('&',' and '))
    t=[x for x in s.split() if x not in GEN]
    return ' '.join(t) if t else s
SPECIAL={('GER','bayern munich'):'bayern munchen',('GER','fc koln'):'koln',('GER','1 fc koln'):'koln',('ITA','inter'):'internazionale',('ITA','milan'):'milan'}
def sim(a,b):
    if a==b: return 1.0
    if a in b or b in a: return 0.9
    return SequenceMatcher(None,a,b).ratio()
def tables(c,lo,hi):
    """Cleaned tables (D239): uses trend/topflight_clean.t1_clean, which fixes missing matches, split names and patches
    England 2022/23 and France 1994/95 with names mapped onto engsoccerdata's."""
    sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','trend'))
    from topflight_clean import t1_clean
    d=t1_clean(c,lo,hi); out={}
    for s,t in d.groupby('Season'):
        out[s]=t.sort_values('pos').reset_index(drop=True)[['club','Pts','GD','GF','pos']].rename(columns={'Pts':'P'})
    return out
def build(lo=2004,hi=2022):
    rows=[]; audit=[]
    for c,(f,ew,_) in CFG.items():
        tabs=tables(c,lo,hi)
        tr=pd.read_csv(f'{SRC}/ewenme_transfers/data/{ew}.csv'); tr['S']=tr.season.str[:4].astype(int)
        tr['fee']=pd.to_numeric(tr.fee_cleaned,errors='coerce').fillna(0.0)
        tin=tr[tr.transfer_movement=='in']
        gin=tin.groupby(['club_name','S']).fee.sum(); gs=tin[tin.transfer_period.str.lower()=='summer'].groupby(['club_name','S']).fee.sum()
        for s,t in tabs.items():
            ew_clubs=sorted(tr[tr.S==s].club_name.unique())
            if not ew_clubs: continue
            A=[SPECIAL.get((c,nm(x)),nm(x)) for x in t.club]; B=[SPECIAL.get((c,nm(x)),nm(x)) for x in ew_clubs]
            M=np.array([[sim(a,b) for b in B] for a in A]); ri,ci=linear_sum_assignment(-M)
            for i,j in zip(ri,ci):
                audit.append((c,s,t.club[i],ew_clubs[j],M[i,j]))
                k=ew_clubs[j]
                R3=float(gs.get((k,s),0))+float(gin.get((k,s-1),0))+float(gin.get((k,s-2),0))
                rows.append(dict(country=c,Season=s,club=t.club[i],ewclub=k,pos=int(t.pos[i]),n=len(t),R3=R3,gin=float(gin.get((k,s),0)),score=M[i,j]))
    P=pd.DataFrame(rows); A=pd.DataFrame(audit,columns=['country','Season','esd','ewenme','score'])
    return P,A
if __name__=='__main__':
    P,A=build(); P.to_csv(sys.argv[1],index=False); A.to_csv(sys.argv[2],index=False)
    print(P.groupby('country').size().to_dict())
    low=A[A.score<0.75].drop_duplicates(['country','esd','ewenme'])
    print('low-similarity pairs to audit:',len(low)); print(low.to_string(index=False))
