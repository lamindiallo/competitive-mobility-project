"""Adds 2025/26 (Season=2025) to the site ladders from the official final tables, and repairs seven club-key splits (D295)."""
import sys, unicodedata, re, difflib, pandas as pd
SP=sys.argv[1]; IN=f'{SP}/site_src/data_in'
sys.path.insert(0, f'{SP}/deliver/02 Framework/code/rcm'); from clubkey import ck
KEYFIX={'FRA':{'auxerre':'aj auxerre','lille':'lille osc','montpellier':'montpellier hsc','psg':'paris saint germain'},
        'GER':{'tsv 1860 munchen':'1860 munchen','tsg hoffenheim':'hoffenheim'},'ESP':{'b':'athletic club b'}}
FILE={'ENG':['ladder_ENG4.csv','ladder_ENG4_results.csv'],'ESP':['ladder_ESP.csv','ladder_ESP_results.csv'],'ITA':['ladder_ITA.csv','ladder_ITA_results.csv'],'GER':['ladder_GER.csv'],'FRA':['ladder_FRA.csv']}
T={}
for line in open(f'{SP}/deliver/03 Data/ladders/final_tables_2025_26.txt'):
    if line.startswith('#') or not line.strip(): continue
    c,t,cl=line.strip().split('|'); T.setdefault(c,{})[int(t)]=cl.split(';')
def norm(s):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower(); s=re.sub(r'[^a-z0-9 ]',' ',s)
    drop={'fc','cf','ac','as','us','sc','cd','ud','sd','rcd','afc','calcio','club','de','1','ss','ssc','acf','cfc','rc','ogc','stade','olympique','tsg','vfl','vfb','sv','bsc','1899','spvgg','ea','es','aj','sco','fsv','hsc','osc','foot','63','38','af','united','town','city','hotspur','albion','wanderers','athletic','real'}
    return ' '.join(w for w in s.split() if w not in drop)
MAN={('ITA','Inter Milan'):'Inter',('GER','Bayern Munich'):'Bayern Munchen',('GER','RB Leipzig'):'RasenBallsport Leipzig',
     ('ESP','Valladolid'):'Real Valladolid',('ESP','Zaragoza'):'Real Zaragoza',('FRA','Laval'):'Stade Lavallois',('ESP','Espanyol'):'Espanyol Barcelona',('ESP','Athletic Bilbao'):'Athletic Bilbao',('ESP','Osasuna'):'CA Osasuna',('ESP','Mallorca'):'RCD Mallorca',('ITA','Pescara'):'Delfino Pescara',('FRA','Nancy'):'AS Nancy Lorraine',('FRA','Le Mans'):'Le Mans FC'}
NEW={('ESP','Ceuta'):('Ceuta','ceuta')}
log=[]
for c,files in FILE.items():
    for f in files:
        L=pd.read_csv(f'{IN}/{f}'); assert L.Season.max()==2024, (f, L.Season.max())
        for a,b in KEYFIX.get(c,{}).items():
            n=(L.k==a).sum()
            if n: log.append((c,f,a,b,int(n)))
            L.loc[L.k==a,'k']=b
        names=L.sort_values('Season').drop_duplicates('k',keep='last')[['club','k','Season']]
        add=[]
        for t,lst in T[c].items():
            for p,w in enumerate(lst,1):
                if (c,w) in NEW: club,k=NEW[(c,w)]
                else:
                    if (c,w) in MAN: m=names[names.club==MAN[(c,w)]]
                    else:
                        m=names[names.k==ck(w)]
                        if m.empty:
                            cand=names.assign(n=names.club.map(norm)); m=cand[cand.n==norm(w)]
                            if m.empty:
                                best=difflib.get_close_matches(norm(w),list(cand.n),n=1,cutoff=0.8); m=cand[cand.n==best[0]] if best else m
                    assert len(m)==1,(c,w,m)
                    club,k=m.iloc[0].club,m.iloc[0].k
                add.append(dict(club=club,Season=2025,tier=t,pos=p,k=k))
        A=pd.DataFrame(add); assert not A.k.duplicated().any(), A[A.k.duplicated(keep=False)]
        L=pd.concat([L,A[L.columns]],ignore_index=True); L.to_csv(f'{IN}/{f}',index=False)
        prev=set(L[L.Season==2024].k); now=set(A.k)
        print(f, len(A), 'out:',sorted(prev-now), '| in:',sorted(now-prev))
pd.DataFrame(log,columns=['country','file','old_key','new_key','rows']).to_csv(f'{SP}/deliver/03 Data/ladders/key_repairs_D295.csv',index=False)
print(log)
