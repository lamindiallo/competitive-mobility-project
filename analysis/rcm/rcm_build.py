import sys, os, numpy as np, pandas as pd
sys.path.insert(0,os.path.dirname(__file__))
from ladder import eng_ladder
from clubkey import ck
SRC=os.environ['FR_SRC']
def build(lo=2006,hi=2022):
    lad=eng_ladder(2,2004,hi); lad['k']=lad.club.map(ck)
    tr=pd.concat([pd.read_csv(f'{SRC}/ewenme_transfers/data/{f}.csv') for f in ['premier-league','championship']])
    tr['Season']=tr.season.str[:4].astype(int); tr['k']=tr.club_name.map(ck)
    tr['fee']=pd.to_numeric(tr.fee_cleaned,errors='coerce').fillna(0.0)
    tin=tr[tr.transfer_movement=='in']; tout=tr[tr.transfer_movement=='out']
    def agg(df,mask=None):
        df=df if mask is None else df[mask(df)]
        return df.groupby(['k','Season']).fee.sum()
    gin=agg(tin); gout=agg(tout)
    gin_summer=agg(tin,lambda d:d.transfer_period.str.lower().eq('summer'))
    rows=[]
    for r in lad[(lad.Season>=lo)].itertuples():
        g=lambda ser,s: float(ser.get((r.k,s),0.0))
        R3=g(gin_summer,r.Season)+g(gin,r.Season-1)+g(gin,r.Season-2)   # predetermined w.r.t. season outcome (winter of s excluded)
        N3=R3-(g(gout,r.Season-1)+g(gout,r.Season-2))
        rows.append(dict(k=r.k,club=r.club,Season=r.Season,tier=r.tier,pos=r.pos,rank=r.rank,R3=R3,N3=N3,
                         gin=g(gin,r.Season),gout=g(gout,r.Season)))
    P=pd.DataFrame(rows)
    P['res_rank']=P.groupby('Season').R3.rank(ascending=False,method='average')   # 1 = biggest spender
    P['over']=P.res_rank-P['rank']        # positive = finishes higher than spend rank predicts
    present=set(zip(lad.k,lad.Season))  # window complete = club in tiers 1-2 in s, s-1, s-2 (no unrecorded League One spend)
    P['win_ok']=[all((k,s-j) in present for j in (0,1,2)) for k,s in zip(P.k,P.Season)]
    return P
if __name__=='__main__':
    P=build(); P.to_csv(sys.argv[1],index=False); print(P.shape); print(P.head())
