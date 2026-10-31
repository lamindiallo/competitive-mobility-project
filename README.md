# Competitive Mobility Project

By Lamin Diallo.

How far can a football club climb? Every club in the top divisions of England, Spain, Italy, Germany and France since the early 1990s: realistic ceilings by position, each club's story, and — for England and France — how clubs perform against their wage bill.

Live site: https://competitive-mobility-project.vercel.app

## What is here

| Folder | Contents |
|---|---|
| `site/` | The static site generator (`build.py`, `model.py`), styles and page parts, and the browser script for this season's tables |
| `api/` | Two Vercel functions: `live.js` (this season's tables from football-data.org, openfootball as fallback) and `corrections.js` (error reports, stored privately) |
| `data/` | The inputs the site is built from: final positions, 2025/26 official tables, wage panels, against-the-money estimates |
| `analysis/` | The code behind every figure: ladders, registered hypothesis tests, wage readings, club values |
| `docs/` | The register of tests, written before the results were computed |

## Build

```
pip install pandas numpy
python site/build.py data public 2.2 "31 October 2026"
```

Vercel runs the same command on every push (see `vercel.json`). The function `api/live.js` needs an environment variable `FOOTBALL_DATA_TOKEN`; without it, it falls back to openfootball's public-domain files.

## Licence

Code: MIT (see `LICENSE`). Data in `data/`: GNU GPL v3 or later (see `data/LICENSE.md`), because the match data derive from the GPL-licensed engsoccerdata.

## Rules the project keeps

No individual's pay is shown. No transfer-market valuations. No club badges. No figure was read by a language model. Corrections are made only against a primary source.
