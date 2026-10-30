# hyp — registered hypothesis tests

Implements `06 Analysis/H1_H2_Test_Protocol.md` and `H8_H9_Test_Protocol.md`. Results in `06 Analysis/H1_H2_Test_Results.md` and `H8_H9_Test_Results.md`.

```
export FR_SRC=<folder of public GitHub clones, see ../rcm/README.md>
export FR_LADDERS="<project>/03 Data/ladders"
python -I h1.py <outdir>          # H1: order test + mover–stayer, 30 configurations (~2 min)
python -I h2.py <outdir>          # H2: block trend + stationarity, 36 runs (~5 min)
python -I e3_mixture.py <outdir>  # exploratory E3, not a registered test
python -I h8_h9.py <outdir>       # H8 band retention vs null; H9 elite/churn correlation (~4 min)
```

Append `quick` to h1.py or h2.py for a fast smoke test with fewer permutations.

| File | Purpose |
|---|---|
| `common.py` | Ladders (England four tiers from `rcm/ladder.py`; two-tier ladders from `03 Data/ladders`), state definitions K5/K4/K6/EQ5, reachability-safe first-passage times |
| `h1.py` | Anderson–Goodman order test (within-season, within-state permutation; parametric bootstrap; power), mover–stayer EM vs first-order chain, ΔBIC |
| `h2.py` | Block index M = 1/G, restricted wild bootstrap (Webb weights, HC1), Mann–Kendall (exact for n ≤ 10), Anderson–Goodman homogeneity by season-pair permutation, power |
| `h8_h9.py` | H8: top- vs bottom-band retention against the permutation null, block-bootstrap CI. H9: elite-tier Shorrocks mobility vs churn breadth on rolling windows, moving-block bootstrap |
| `e3_mixture.py` | Mixture of first-order chains; does fixed club heterogeneity reproduce the order-test dependence? |

Seeds are fixed (20261008, 20261009, 20261010, 31415). Verified: vectorised G² equals a brute-force count; the permutation preserves every (season, state, next-state) count; Mann–Kendall p-values match `scipy.stats.kendalltau` exactly for n ≤ 10.
