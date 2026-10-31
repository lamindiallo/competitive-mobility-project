import re,pandas as pd,numpy as np
def parse_of(path):
    rows=[]; stop=False
    for line in open(path,encoding='utf-8'):
        s=line.strip()
        if re.match(r'^[▪»].*(Play-?off|Playoff)',s,re.I): break
        m=re.match(r'^(?:\d{1,2}:\d{2}\s+)?(.+?)\s{2,}(\d+)-(\d+)(?:\s*\(\d+-\d+\))?\s{2,}(.+?)$',s)
        if m:
            h,hg,ag,a=m.group(1).strip(),int(m.group(2)),int(m.group(3)),m.group(4).strip()
            if h and a: rows.append((h,a,hg,ag))
    return rows
def table_from(rows,wp=3):
    r={}
    for h,a,hg,ag in rows:
        for tm,gf,ga in ((h,hg,ag),(a,ag,hg)):
            d=r.setdefault(tm,[0,0,0,0]); d[0]+=(wp if gf>ga else (1 if gf==ga else 0)); d[1]+=gf-ga; d[2]+=gf; d[3]+=1
    t=pd.DataFrame([(k,*v) for k,v in r.items()],columns=['club','Pts','GD','GF','P'])
    return t.sort_values(['Pts','GD','GF'],ascending=False).reset_index(drop=True)
if __name__=='__main__':
    for f,t in [('1-premierleague',1),('2-championship',2)]:
        rows=parse_of(f'/tmp/of_eng/2022-23/{f}.txt')
        tab=table_from(rows)
        print(f,len(rows),'matches',len(tab),'clubs, played:',sorted(set(tab.P)))
        print(tab.head(4).to_string(index=False)); print(tab.tail(3).to_string(index=False))
