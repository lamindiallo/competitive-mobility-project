# Framework scripts (first analysis rounds)

These are the scripts that produced the first framework results, including the registered pyramid mobility figures
(G: England 4.00, Spain 3.44, Italy 3.28, Germany 2.56, France 2.38; decisions D167 and D213). They are kept as they were run,
so that the registered results can be traced. Only one change was made when they were added here: the line that pointed
Python at the working folder (`/tmp/work`) now points at this folder.

They still read and write fixed working paths. To re-run them, create these folders (or links) first:

| Path in the scripts | What it must contain |
|---|---|
| `/tmp/fr/` | Match-result files from engsoccerdata (`england.csv`, `germany.csv`, `spain.csv`, `italy.csv`, `france.csv`, `scotland.csv`) |
| `/tmp/fr/03/` | Output folder for panels and ladders |
| `/tmp/esd/data-raw/` | The engsoccerdata repository's `data-raw` folder |
| `/tmp/of_eng/2022-23/` | openfootball England 2022/23 text files |
| `/tmp/tier2/` | Second-division result files from football-data.co.uk |
| `/tmp/schochastics_football-data/` | The schochastics football-data repository |

Main entry points: `framework_run.py` (England), `multi_country.py` and `run5.py` / `run5b.py` (five countries, pyramid G),
`robustness.py`, `power.py`, `depthG.py` (ladder depth).

The figures shown on the website are recomputed from the site's own tables by `analysis/site_checks/g_intervals.py`,
which needs no fixed paths.
