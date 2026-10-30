"""Season-level Tier C for the v2 club pages: actual finish, the finish the wage bill normally buys, wage bill and its rank.
Same model as tierC.py (season effects, then a monotone curve); checked against the published club averages."""
import sys, numpy as np, pandas as pd
SP=sys.argv[1]; IN=f'{SP}/site_src/data_in'
sys.path.insert(0, f'{SP}/deliver/02 Framework/code/clubvalues'); from tierC import expected, ladder_rank
out=[]
for c, wf, lf, payc in (('ENG','england_wage_panel.csv','ladder_ENG4_results.csv','payroll_k'),('FRA','france_wage_panel.csv','ladder_FRA.csv','payroll_keur')):
    P=pd.read_csv(f'{IN}/{wf}'); L=ladder_rank(pd.read_csv(f'{IN}/{lf}'))
    if c=='ENG': P=P[~P.flag_xcheck_conflict.astype(bool)]
    else: P=P[P.consolidated.fillna(False)==False]
    P=P.drop(columns=['tier','pos'],errors='ignore').rename(columns={payc:'pay'})
    P=P.merge(L[['Season','k','club','tier','pos','lrank','N']].rename(columns={'Season':'season'}),on=['k','season']).reset_index(drop=True)
    P['w']=np.log(P.pay/P.groupby('season').pay.transform('mean')); P['p']=1-(P.lrank-1)/(P.N-1)
    P['phat']=expected(P); P['places']=(P.p-P.phat)*(P.N-1)
    P['exp_lrank']=1+(1-P.phat)*(P.N-1)
    P['wage_rank']=P.groupby('season').pay.rank(ascending=False,method='min').astype(int); P['wage_n']=P.season.map(P.groupby('season').size())
    P['country']=c; out.append(P[['country','k','club','season','tier','pos','lrank','N','exp_lrank','places','pay','wage_rank','wage_n']])
S=pd.concat(out); S.to_csv(f'{SP}/v2/tierC_seasons.csv',index=False)
for c,f in (('ENG','england_tierC_prototype.csv'),('FRA','france_tierC_prototype.csv')):
    T=pd.read_csv(f'{IN}/{f}').set_index('k'); m=S[S.country==c].groupby('k').places.agg(['mean','size'])
    j=T.join(m,how='left'); d=(j.places_above_expected-j['mean']).abs()
    print(c,'clubs',len(T),'max |diff| %.3f'%d.max(),'n mismatch',int((j.seasons!=j['size']).sum()))
    print(j[d>0.05][['places_above_expected','mean','seasons','size']].head())
