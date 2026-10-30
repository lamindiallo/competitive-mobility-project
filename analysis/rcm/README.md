# rcm — Resource-Conditional Mobility (interim, transfer-spend proxy)

Runs entirely from public GitHub sources. Clone them into one folder and point `FR_SRC` at it:

```
git clone --depth 1 https://github.com/jalapic/engsoccerdata   jalapic_engsoccerdata
git clone --depth 1 https://github.com/openfootball/england     openfootball_england
git clone --depth 1 https://github.com/ewenme/transfers         ewenme_transfers
export FR_SRC=<that folder>
```

England, tiers 1-2 (order matters — later steps add columns to the panel):

```
python -I rcm_build.py     panel.csv            # ladder + R3 resource measure + window completeness
python -I rcm_parachute.py panel.csv            # parachute eligibility; classifies large climbs
python -I rcm_final.py     panel.csv restricted # fit, persistence, climbs, conversion, reach (complete windows)
python -I rcm_placebo.py   panel.csv            # forward vs backward conversion test
```

Big Five top flights:

```
python -I xc_build.py    xc_panel.csv xc_audit.csv   # assignment-based club matching + audit of low-similarity pairs
python -I xc_analyse.py  xc_panel.csv
python -I xc_reach_ci.py xc_panel.csv
```

Verified 8 Oct 2026: a clean re-run reproduces `03 Data/resource_proxy/eng_rcm_panel.csv` exactly.
`rcm_analyse.py` and `rcm_robust.py` are the exploratory first passes and contain the withdrawn 29% climb figure (D204); they are kept for the record, not for use.

## Added later on 8 Oct 2026

Data quality (run these first; see D236, D239):

```
python -I audit_eng_sources.py                  # engsoccerdata vs openfootball, England tiers 1-4, 2000-2022
python -I audit_completeness.py out.csv         # double-round-robin check of every league-season in engsoccerdata
```

All top-flight scripts (`xc_*.py`, `../trend/trend_xc*.py`, `../trend/trend_outsider_xc*.py`) now load tables through
`../trend/topflight_clean.py`, which repairs the seasons the completeness audit flagged and maps patched seasons onto
engsoccerdata club names. **Do not bypass it**: an earlier unmapped patch silently dropped two England season-pairs (D240).

Further analyses: `xc_cliff.py` (spending shape; reach at equal relative spend), `xc_crowding.py` (exploratory H12 test),
`xc_entrants.py` (model-free classification of top-four entrants), `rcm_top4_entrants.py` (England, D218).
