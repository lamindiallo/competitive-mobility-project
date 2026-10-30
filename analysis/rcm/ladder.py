"""English ladder (tiers 1-4), engsoccerdata + openfootball patch for 2022-23. Rebuilt 8 Oct 2026."""
import re, unicodedata, numpy as np, pandas as pd, os
SRC=os.environ.get('FR_SRC')
STOP={'fc','afc','ac','as','sc','cf','city','town','united','utd','county','rovers','athletic','wanderers','albion','hotspur','the','and','of','football','club'}
def norm(s, keep_suffix=False):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()
    s=s.replace('&',' and ')
    s=re.sub(r'[^a-z0-9 ]',' ',s)
    return ' '.join(s.split())
def table_from(rows,wp=3):
    r={}
    for h,a,hg,ag in rows:
        for tm,gf,ga in ((h,hg,ag),(a,ag,hg)):
            d=r.setdefault(tm,[0,0,0,0]); d[0]+=(wp if gf>ga else (1 if gf==ga else 0)); d[1]+=gf-ga; d[2]+=gf; d[3]+=1
    t=pd.DataFrame([(k,*v) for k,v in r.items()],columns=['club','Pts','GD','GF','P'])
    return t.sort_values(['Pts','GD','GF'],ascending=False).reset_index(drop=True)
def parse_of(path):
    rows=[]
    for line in open(path,encoding='utf-8'):
        s=line.strip()
        if re.match(r'^[▪»].*(Play-?off|Playoff)',s,re.I): break
        m=re.match(r'^(?:\d{1,2}:\d{2}\s+)?(.+?)\s{2,}(\d+)-(\d+)(?:\s*\(\d+-\d+\))?\s{2,}(.+?)$',s)
        if m: rows.append((m.group(1).strip(),re.sub(r'\s*\[[^\]]*\]\s*$','',m.group(4)).strip(),int(m.group(2)),int(m.group(3))))  # strip [awarded] etc.
    return rows
def eng_ladder(maxtier=4,lo=1992,hi=2024):
    df=pd.read_csv(f'{SRC}/jalapic_engsoccerdata/data-raw/england.csv',low_memory=False)
    df=df[(df.tier<=maxtier)&(df.Season>=lo)&(df.Season<=hi)]
    out=[]
    for (s,t),g in df.groupby(['Season','tier']):
        tab=table_from(zip(g.home,g.visitor,g.hgoal,g.vgoal))
        tab['pos']=np.arange(1,len(tab)+1); tab['Season']=s; tab['tier']=t; tab['src']='esd'
        out.append(tab)
    names={1:'1-premierleague',2:'2-championship',3:'3-league1',4:'4-league2'}
    if lo<=2022<=hi and 2022 not in set(df.Season):
        for t in range(1,maxtier+1):
            tab=table_from(parse_of(f'{SRC}/openfootball_england/2022-23/{names[t]}.txt'))
            tab['pos']=np.arange(1,len(tab)+1); tab['Season']=2022; tab['tier']=t; tab['src']='openfootball'
            out.append(tab)
    d=pd.concat(out,ignore_index=True)
    n=d.groupby(['Season','tier']).size().unstack(fill_value=0)
    off={s:{t:int(n.loc[s,:t-1].sum()) if t>1 else 0 for t in n.columns} for s in n.index}
    d['rank']=[off[r.Season][r.tier]+r.pos for r in d.itertuples()]
    return d
