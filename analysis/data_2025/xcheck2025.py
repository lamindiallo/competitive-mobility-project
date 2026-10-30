import json, sys, pandas as pd
SP=sys.argv[1]; D=f'{SP}/feeds/football.json/2025-26'
T={}
for line in open(f'{SP}/deliver/03 Data/ladders/final_tables_2025_26.txt'):
    if line.startswith('#') or not line.strip(): continue
    c,t,cl=line.strip().split('|'); T[(c,int(t))]=cl.split(';')
F={('ENG',1):'en.1',('ENG',2):'en.2',('ENG',3):'en.3',('ENG',4):'en.4',('ESP',1):'es.1',('ESP',2):'es.2',('ITA',1):'it.1',('ITA',2):'it.2',('GER',1):'de.1',('GER',2):'de.2',('FRA',1):'fr.1',('FRA',2):'fr.2'}
for key,f in F.items():
    J=json.load(open(f'{D}/{f}.json')); t={}; n=0
    for m in J['matches']:
        s0=m.get('score'); sc=s0 if isinstance(s0,list) else (s0 or {}).get('ft')
        if not sc or not m['round'].startswith('Matchday'): continue
        n+=1
        for tm,gf,ga in ((m['team1'],sc[0],sc[1]),(m['team2'],sc[1],sc[0])):
            d=t.setdefault(tm,[0,0,0,0]); d[0]+=3 if gf>ga else (1 if gf==ga else 0); d[1]+=gf-ga; d[2]+=gf; d[3]+=1
    W=T[key]; N=len(W); exp=N*(N-1)
    tab=sorted(t.items(),key=lambda x:(-x[1][0],-x[1][1],-x[1][2]))
    status='complete' if n==exp else f'INCOMPLETE {n}/{exp}'
    print(key,f,status)
    if n<exp-1: continue
    for i,(tm,d) in enumerate(tab,1):
        w=W[i-1]
        a=tm.lower(); b=w.lower()
        flag='' if (b.split()[0] in a or a.split()[0] in b or any(x in a for x in b.split() if len(x)>3)) else '  <-- DIFF'
        if flag: print(f'   {i:2d} feed={tm} ({d[0]}pts gd{d[1]}) wiki={w}{flag}')
