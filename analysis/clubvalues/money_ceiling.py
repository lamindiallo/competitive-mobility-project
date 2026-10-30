"""Money-aware realistic ceilings (D301), England and France.

The position-only ceiling (site/model.py) says what happened to clubs that finished where a club finished. This adds the
club's wage bill: a logistic model of each five-year goal on (a) position on the ladder of the top two divisions and
(b) the log of the club's wage bill relative to the season's average, fitted per country on every club-season with a
published wage bill. Five-year goals are used because wage data start in 2008/09 (France) and 2011/12 (England), which
leaves too few complete ten-year windows.

Goals and who they apply to:
  top4_5   reach the top four within five seasons      top-flight clubs that finished 5th or lower and stayed up
  stay5    stay in the top flight all five seasons      top-flight clubs that finished 8th or lower and stayed up
  tf5      be back in, or reach, the top flight within five seasons   relegated clubs and second-tier clubs not promoted

Checks: out-of-sample comparison with a position-only model (5-fold cross-validation grouped by club, Brier score and
log loss); club-level 95% ranges by refitting on clubs resampled with replacement.
Usage: python money_ceiling.py <data dir> <out dir>"""
import os, sys
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'site'))
from model import load

DATA, OUT = sys.argv[1:3]; os.makedirs(OUT, exist_ok=True)
L, _ = load(DATA)
TCS = pd.read_csv(os.path.join(DATA, 'tierC_seasons.csv'))
GOALS = {'top4_5': 'reached the top four within five seasons', 'stay5': 'stayed in the top flight for all of the next five seasons',
         'tf5': 'were in the top flight within five seasons'}
rng = np.random.default_rng(11)

def frame(c):
    d = L[c][L[c].tier <= 2].copy()
    n12 = d.groupby('Season').size(); d['p'] = (d['rank'] - 1) / (d.Season.map(n12) - 1)   # 0 = champions, 1 = bottom of tier 2
    S = {(r.k, r.Season): r for r in d.itertuples()}
    fut = lambda r, h: [S.get((r.k, r.Season + i)) for i in range(1, h + 1)]
    d['top4_5'] = [float(any(x is not None and x.tier == 1 and x.pos <= 4 for x in fut(r, 5))) for r in d.itertuples()]
    d['stay5'] = [float(all(x is not None and x.tier == 1 for x in fut(r, 5))) for r in d.itertuples()]
    d['tf5'] = [float(any(x is not None and x.tier == 1 for x in fut(r, 5))) for r in d.itertuples()]
    t = TCS[TCS.country == c].copy(); t['w'] = np.log(t.pay / t.groupby('season').pay.transform('mean'))
    d = d.merge(t[['k', 'season', 'w', 'pay', 'wage_rank', 'wage_n']].rename(columns={'season': 'Season'}), on=['k', 'Season'], how='left')
    return d

def rows_for(d, goal):
    if goal == 'top4_5': m = (d.tier == 1) & (d.pos >= 5) & (d.next_tier == 1)
    elif goal == 'stay5': m = (d.tier == 1) & (d.pos >= 8) & (d.next_tier == 1)
    else: m = ((d.tier == 1) & (d.next_tier > 1)) | ((d.tier == 2) & (d.band != 'prom'))
    return m

def fit(X, y): return LogisticRegression(C=1e6, max_iter=2000).fit(X, y)

models, preds = [], []
for c in ('ENG', 'FRA'):
    d = frame(c); last = int(L[c].Season.max())
    for goal in GOALS:
        m = rows_for(d, goal)
        tr = d[m & d.w.notna() & (d.Season <= last - 5) & ~d.reserve].copy()
        X2, X1, y, grp = tr[['p', 'w']].values, tr[['p']].values, tr[goal].values, tr.k.values
        # out-of-sample check, grouped by club
        b1 = b2 = l1 = l2 = 0.0
        for a, b in GroupKFold(n_splits=5).split(X2, y, grp):
            p1 = np.clip(fit(X1[a], y[a]).predict_proba(X1[b])[:, 1], 1e-4, 1 - 1e-4); p2 = np.clip(fit(X2[a], y[a]).predict_proba(X2[b])[:, 1], 1e-4, 1 - 1e-4)
            b1 += ((p1 - y[b]) ** 2).sum(); b2 += ((p2 - y[b]) ** 2).sum()
            l1 -= (y[b] * np.log(p1) + (1 - y[b]) * np.log(1 - p1)).sum(); l2 -= (y[b] * np.log(p2) + (1 - y[b]) * np.log(1 - p2)).sum()
        full = fit(X2, y)
        models.append(dict(country=c, goal=goal, n=len(tr), clubs=tr.k.nunique(), hits=int(y.sum()), first=int(tr.Season.min()), last=int(tr.Season.max()),
                           coef_position=round(full.coef_[0][0], 3), coef_wage=round(full.coef_[0][1], 3),
                           brier_position_only=round(b1 / len(tr), 4), brier_with_wages=round(b2 / len(tr), 4),
                           logloss_position_only=round(l1 / len(tr), 4), logloss_with_wages=round(l2 / len(tr), 4)))
        # club predictions from the latest season, using the most recent published wage bill (at most three seasons old)
        cur = d[(d.Season == last) & ~d.reserve].copy()
        cur = cur[rows_for(cur, goal)]
        lw = TCS[TCS.country == c].copy(); lw['w'] = np.log(lw.pay / lw.groupby('season').pay.transform('mean'))
        lw = lw.sort_values('season').groupby('k').tail(1).set_index('k')
        cur = cur[cur.k.isin(lw.index)]
        cur['w_season'] = cur.k.map(lw.season); cur['w'] = cur.k.map(lw.w); cur = cur[cur.w_season >= last - 3]
        if cur.empty: continue
        Xc = cur[['p', 'w']].values; base = full.predict_proba(Xc)[:, 1]
        clubs = np.unique(grp); boot = []
        for _ in range(500):
            pick = rng.choice(clubs, len(clubs)); idx = np.concatenate([np.where(grp == k)[0] for k in pick])
            if y[idx].min() == y[idx].max(): continue
            boot.append(fit(X2[idx], y[idx]).predict_proba(Xc)[:, 1])
        boot = np.array(boot)
        for i, r in enumerate(cur.itertuples()):
            preds.append(dict(country=c, k=r.k, goal=goal, season=last, pos=int(r.pos), tier=int(r.tier), wage_season=int(r.w_season),
                              wage_rank=int(lw.loc[r.k].wage_rank), wage_n=int(lw.loc[r.k].wage_n), relative_wage=round(float(np.exp(r.w)), 2),
                              p=round(float(base[i]), 4), lo=round(float(np.percentile(boot[:, i], 2.5)), 4), hi=round(float(np.percentile(boot[:, i], 97.5)), 4)))

M = pd.DataFrame(models); P = pd.DataFrame(preds)
M.to_csv(os.path.join(OUT, 'money_ceiling_models.csv'), index=False); P.to_csv(os.path.join(OUT, 'money_ceilings.csv'), index=False)
pd.set_option('display.width', 200); print(M.to_string(index=False)); print(len(P), 'club predictions')
