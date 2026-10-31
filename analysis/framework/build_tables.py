import pandas as pd, numpy as np
df=pd.read_csv('england.csv',low_memory=False)
df=df[df.tier.isin([1,2,3,4])].copy()

def season_tables(g, season):
    win_pts = 3 if season>=1981 else 2      # England moved to 3pts in 1981-82
    rows={}
    for _,r in g.iterrows():
        for team,gf,ga in ((r.home,r.hgoal,r.vgoal),(r.visitor,r.vgoal,r.hgoal)):
            d=rows.setdefault(team,dict(P=0,W=0,D=0,L=0,GF=0,GA=0,Pts=0))
            d['P']+=1; d['GF']+=gf; d['GA']+=ga
            if gf>ga: d['W']+=1; d['Pts']+=win_pts
            elif gf==ga: d['D']+=1; d['Pts']+=1
            else: d['L']+=1
    t=pd.DataFrame(rows).T.reset_index().rename(columns={'index':'club'})
    t['GD']=t.GF-t.GA
    t=t.sort_values(['Pts','GD','GF'],ascending=False).reset_index(drop=True)
    t['pos']=np.arange(1,len(t)+1)
    return t

out=[]
for (season,tier),g in df.groupby(['Season','tier']):
    t=season_tables(g,season); t['Season']=season; t['tier']=tier
    out.append(t)
tab=pd.concat(out,ignore_index=True)
tab.to_csv('tables.csv',index=False)
print('club-seasons:',len(tab))
print(tab[tab.Season==2023].groupby('tier').size())
# sanity: champions of recent seasons
for s in [2019,2020,2021,2022,2023]:
    c=tab[(tab.Season==s)&(tab.tier==1)&(tab.pos==1)].club.values
    print(s,'tier-1 winner:',c)
