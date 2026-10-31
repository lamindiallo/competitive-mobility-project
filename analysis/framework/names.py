import csv,glob,re,unicodedata,collections,pandas as pd,numpy as np
PTS3={'fr':1994,'es':1995,'it':1994,'de':1995,'eng':1981}
def norm(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()
    s=re.sub(r'[^a-z0-9 ]',' ',s)
    stop={'fc','ac','as','sc','us','usl','cf','cd','sd','ud','ss','ssc','ssd','acd','fbc','calcio','olympique','football','club','de','del','la','le','les','du','des','stade','athletic','sporting','sk','sv','sco','ea','lb','cs','sm','rc','sa','ogc','fec','asd','1899','1900','1907','1911','1912','1913','1914','1919','1926','2013','old','new','na','1'}
    toks=[t for t in s.split() if t not in stop]
    return ' '.join(toks)

def t1_tables(country,fn,lo=1992,hi=2024):
    df=pd.read_csv(fn,low_memory=False)
    df=df[df.tier==1]
    out=[]
    for s,g in df.groupby('Season'):
        if s<lo or s>hi: continue
        wp=3 if s>=PTS3[country] else 2
        r={}
        for _,x in g.iterrows():
            for tm,gf,ga in ((x.home,x.hgoal,x.vgoal),(x.visitor,x.vgoal,x.hgoal)):
                d=r.setdefault(tm,[0,0,0]); d[0]+=(wp if gf>ga else (1 if gf==ga else 0)); d[1]+=gf-ga; d[2]+=gf
        tt=pd.DataFrame([(k,v[0],v[1],v[2]) for k,v in r.items()],columns=['club','Pts','GD','GF'])
        tt=tt.sort_values(['Pts','GD','GF'],ascending=False).reset_index(drop=True)
        tt['pos']=np.arange(1,len(tt)+1); tt['Season']=s; tt['tier']=1
        out.append(tt[['club','Season','tier','pos']])
    return pd.concat(out,ignore_index=True)

def t2_tables(code):
    out=[]
    for f in sorted(glob.glob(f'/tmp/tier2/{code}2_*.csv')):
        y=int(f.split('_')[-1][:4])
        for r in csv.DictReader(open(f)):
            out.append((r['club'],y,2,int(r['pos'])))
    return pd.DataFrame(out,columns=['club','Season','tier','pos'])
