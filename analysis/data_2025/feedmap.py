"""Maps openfootball team names (2025/26 and 2026/27 feeds) to ladder club keys. Writes feed_names.csv for review."""
import sys, json, re, unicodedata, difflib, pandas as pd
SP=sys.argv[1]; IN=f'{SP}/site_src/data_in'
FILE={'ENG':'ladder_ENG4.csv','ESP':'ladder_ESP.csv','ITA':'ladder_ITA.csv','GER':'ladder_GER.csv','FRA':'ladder_FRA.csv'}
FEEDS={'ENG':['en.1','en.2','en.3','en.4'],'ESP':['es.1','es.2'],'ITA':['it.1','it.2'],'GER':['de.1','de.2'],'FRA':['fr.1','fr.2']}
def norm(s):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower(); s=re.sub(r'[^a-z0-9 ]',' ',s)
    drop={'fc','cf','ac','as','us','sc','cd','ud','sd','rcd','afc','calcio','club','de','1','ss','ssc','acf','cfc','rc','ogc','stade','olympique','tsg','vfl','vfb','sv','bsc','1899','spvgg','ea','es','aj','sco','fsv','hsc','osc','foot','63','38','af','united','town','city','hotspur','albion','wanderers','athletic','real','1913','1907','1901','1904','1909','1919','1846','1910','1905','1900','1908','1911','04','05','07','96','98','29','footbal','football','balompie','sad','club','cp','calcio','bc','ud','rb','e','v','1860','sk','ag','sco','hac','fcsb','aca','nk'}
    return ' '.join(w for w in s.split() if w not in drop)
rows=[]
for c,f in FILE.items():
    L=pd.read_csv(f'{IN}/{f}'); recent=L[L.Season>=2015]
    names=recent.sort_values('Season').drop_duplicates('k',keep='last')
    names=names.assign(n=names.club.map(norm))
    for yr in ('2025-26','2026-27'):
        for fd in FEEDS[c]:
            try: J=json.load(open(f'{SP}/feeds/football.json/{yr}/{fd}.json'))
            except FileNotFoundError: continue
            for tm in sorted({m['team1'] for m in J['matches']}|{m['team2'] for m in J['matches']}):
                n=norm(tm); m=names[names.n==n]; how='exact'
                if len(m)!=1:
                    cands=[x for x in names.n if x and (x in n or n in x)]
                    if len(cands)==1: m=names[names.n==cands[0]]; how='contain'
                    else:
                        b=difflib.get_close_matches(n,list(names.n),n=1,cutoff=0.6); m=names[names.n==b[0]] if b else names.iloc[0:0]; how='fuzzy'
                rows.append(dict(country=c,season=yr,feed=fd,team=tm,club=m.club.iloc[0] if len(m) else '',k=m.k.iloc[0] if len(m) else '',how=how if len(m) else 'NONE'))
R=pd.DataFrame(rows).drop_duplicates(['country','team'])
R.to_csv(f'{SP}/v2/feed_names_draft.csv',index=False)
pd.set_option('display.width',220); pd.set_option('display.max_rows',500)
print(R[R.how!='exact'].to_string(index=False))
print('dups:',R[R.duplicated(['country','k'],keep=False)&(R.k!='')].sort_values('k').to_string(index=False))
