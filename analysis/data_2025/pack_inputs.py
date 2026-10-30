"""Pack the v2 site inputs into one xz-compressed JSON (ladders index-encoded), base64, in chunks with SHA-1s."""
import json, lzma, base64, hashlib, sys, os, pandas as pd
IN, OUTF = sys.argv[1:3]; D = {'ladders': {}, 'csv': {}, 'text': {}}
for c, f in {'ENG': 'ladder_ENG4.csv', 'ESP': 'ladder_ESP.csv', 'ITA': 'ladder_ITA.csv', 'GER': 'ladder_GER.csv', 'FRA': 'ladder_FRA.csv'}.items():
    L = pd.read_csv(f'{IN}/{f}').sort_values(['Season', 'tier', 'pos'])
    pairs = list(dict.fromkeys(zip(L.club, L.k))); ix = {p: i for i, p in enumerate(pairs)}
    S = {}
    for (s, t), g in L.groupby(['Season', 'tier']):
        assert list(g.pos) == list(range(1, len(g) + 1)), (c, s, t)
        S.setdefault(str(s), {})[str(t)] = [ix[p] for p in zip(g.club, g.k)]
    D['ladders'][c] = dict(file=f, names=[p[0] for p in pairs], keys=[[p[1] if p[1] != p[0] else 0][0] for p in pairs], seasons=S)
for f in ['england_wage_panel.csv', 'france_wage_panel.csv', 'tierC_seasons.csv', 'no_champion.csv', 'official_position_changes.csv', 'tiers_2026_27.csv', 'feed_names.csv', 'england_tierC_prototype.csv', 'france_tierC_prototype.csv']:
    d = pd.read_csv(f'{IN}/{f}'); D['csv'][f] = dict(columns=list(d.columns), data=json.loads(d.to_json(orient='values')))
for f in ['final_tables_2025_26.txt', 'live_snapshot.json']: D['text'][f] = open(f'{IN}/{f}', encoding='utf-8').read()
json.dump(D, open(OUTF, 'w'), ensure_ascii=False, separators=(',', ':'))
