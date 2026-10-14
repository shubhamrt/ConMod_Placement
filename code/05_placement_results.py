# Title: "Flux reduction results for the placement strategies"
# Author: "Shubham Tiwari"
# Date Started: "2026-07-23"
# Date Updated: "2026-10-14"

# Description:
# This script takes the AERO runs with structures (placement_flux.csv) and without
# structures (baseline_flux.csv) and calculates flux reduction for each plot,
# strategy, density and wind speed:
#   pct         = percent reduction in horizontal flux
#   Q_avoided   = initial flux - flux with structures (g m-1 d-1)
#   per_avoided = Q_avoided / number of structures placed
#   ach_density = density actually achieved, from the share of structures placed
# A plot is a complete case at a wind speed when all 24 strategy x density runs
# finished (AERO failed for a few layouts with many gaps). Paired comparisons and
# the figures use complete cases only.
#
# The summary tables are then made from the complete cases: reliability (share of
# plots reaching 50, 75, 90% reduction), win rate (share of cases where a strategy
# gave the largest flux reduction, ties split), marginal benefit per added
# structure, and paired bootstrap differences of each strategy vs largest-gap.
# The numbers given in the Results section are printed at the end.
#
# This script was used for the Results, Figures 4-8 and Tables S2-S4 in Tiwari et al.

# Inputs:  data/study_plots.csv, data/baseline_flux.csv, data/placement_flux.csv
# Outputs: output/flux_reduction.csv, output/reliability.csv, output/win_rate.csv,
#          output/win_rate_pooled.csv, output/marginal_benefit.csv,
#          output/strategy_differences.csv, output/initial_flux_stats.csv

import os
import numpy as np
import pandas as pd

##### SETUP #####

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, 'data')
OUT = os.path.join(REPO, 'output')
os.makedirs(OUT, exist_ok=True)

STRATEGIES = ['largest_gap', 'scaled_gap', 'proportional', 'cell_grid']
DENSITIES = [100, 250, 500, 1000, 2000, 4000]
TYPES = ['grass', 'mixed', 'shrub']
WINDS = [8, 12, 16, 20]
rng = np.random.default_rng(7)   # bootstrap seed
B = 2000                         # bootstrap resamples

##### LOAD DATA #####

plots = pd.read_csv(os.path.join(DATA, 'study_plots.csv'))
base = pd.read_csv(os.path.join(DATA, 'baseline_flux.csv'))
runs = pd.read_csv(os.path.join(DATA, 'placement_flux.csv'))

##### FLUX REDUCTION FOR EACH RUN #####

# Match each run to the initial flux of the same plot and wind speed
base = base.rename(columns={'hflux_gmd': 'initial_gmd'})
df = runs.merge(base[['plot_id', 'wind_speed', 'initial_gmd']], on=['plot_id', 'wind_speed'], how='inner')

# Keep plots with some flux to reduce, and drop failed runs
df = df[df.initial_gmd > 0].copy()
df = df.dropna(subset=['hflux_gmd'])

df['pct'] = 100.0 * (df.initial_gmd - df.hflux_gmd) / df.initial_gmd
df['Q_avoided'] = df.initial_gmd - df.hflux_gmd
df['per_avoided'] = df.Q_avoided / df.n_placed.clip(lower=1)
df['ach_frac'] = df.n_placed / df.n_structures.clip(lower=1)
df['ach_density'] = df.density_ha * df.ach_frac ** 2

# Complete case: all 24 strategy x density runs at that plot and wind speed
ncell = df.groupby(['plot_id', 'wind_speed']).size().rename('ncell').reset_index()
df = df.merge(ncell, on=['plot_id', 'wind_speed'])
df['complete_case'] = df.ncell == len(STRATEGIES) * len(DENSITIES)
df = df.drop(columns='ncell')
df.to_csv(os.path.join(OUT, 'flux_reduction.csv'), index=False)

cc = df[df.complete_case].copy()
print(f'runs: {len(df)}, complete case runs: {len(cc)}')

##### RELIABILITY #####

cc['r50'] = cc.pct >= 50
cc['r75'] = cc.pct >= 75
cc['r90'] = cc.pct >= 90
rel = cc.groupby(['veg_type', 'wind_speed', 'density_ha', 'strategy']).agg(
    N=('pct', 'size'), p50=('r50', 'mean'), p75=('r75', 'mean'), p90=('r90', 'mean'),
    mean_pct=('pct', 'mean'), median_pct=('pct', 'median'),
    q25_pct=('pct', lambda x: x.quantile(0.25)), q75_pct=('pct', lambda x: x.quantile(0.75))).reset_index()
rel.to_csv(os.path.join(OUT, 'reliability.csv'), index=False)

##### WIN RATE #####
# The best strategy for a plot, wind and density is the one with the largest
# Q_avoided. When strategies tie, the win is shared between them.

key = ['plot_id', 'wind_speed', 'density_ha']
cc['best'] = cc.groupby(key).Q_avoided.transform('max')
cc['regret'] = cc.best - cc.Q_avoided
cc['is_best'] = cc.regret <= 1e-9
cc['n_tied'] = cc.groupby(key).is_best.transform('sum')
cc['win'] = cc.is_best / cc.n_tied
win = cc.groupby(['veg_type', 'wind_speed', 'density_ha', 'strategy']).agg(
    N=('win', 'size'), win_rate=('win', 'mean'), median_regret=('regret', 'median')).reset_index()
win.to_csv(os.path.join(OUT, 'win_rate.csv'), index=False)

# Pooled over the erosive wind speeds (12, 16, 20 m/s), used in Figure 6d
win_pooled = cc[cc.wind_speed.isin([12, 16, 20])].groupby('strategy').win.mean().reset_index()
win_pooled = win_pooled.rename(columns={'win': 'win_rate'})
win_pooled.to_csv(os.path.join(OUT, 'win_rate_pooled.csv'), index=False)

##### MARGINAL BENEFIT #####
# Extra flux reduction per extra structure placed, between neighbouring densities

mb = cc.groupby(['veg_type', 'wind_speed', 'strategy', 'density_ha']).agg(
    Q=('Q_avoided', 'mean'), Np=('n_placed', 'mean')).reset_index()
rows = []
for (t, w, s), g in mb.groupby(['veg_type', 'wind_speed', 'strategy']):
    g = g.sort_values('density_ha')
    q, n, d = g.Q.values, g.Np.values, g.density_ha.values
    for i in range(1, len(d)):
        dn = n[i] - n[i - 1]
        rows.append({'veg_type': t, 'wind_speed': w, 'strategy': s,
                     'from_density': d[i - 1], 'to_density': d[i],
                     'dQ_avoided': q[i] - q[i - 1], 'dN_placed': dn,
                     'marg_per_structure': (q[i] - q[i - 1]) / dn if dn != 0 else np.nan})
pd.DataFrame(rows).to_csv(os.path.join(OUT, 'marginal_benefit.csv'), index=False)

##### PAIRED DIFFERENCES VS LARGEST-GAP #####
# Within each plot: pct reduction of a strategy minus pct reduction of largest-gap.
# Median difference with a 95% bootstrap interval.

def paired_boot(a, b):
    d = b - a
    n = len(d)
    if n < 3:
        return np.nan, np.nan, np.nan, np.nan
    idx = rng.integers(0, n, size=(B, n))
    meds = np.median(d[idx], axis=1)
    return np.median(d), np.percentile(meds, 2.5), np.percentile(meds, 97.5), (d > 0).mean()

wide = cc.pivot_table(index=['plot_id', 'veg_type', 'wind_speed', 'density_ha'],
                      columns='strategy', values='pct')
rows = []
for s in ['scaled_gap', 'proportional', 'cell_grid']:
    sub = wide.dropna(subset=['largest_gap', s])
    for (t, w, d), g in sub.groupby(['veg_type', 'wind_speed', 'density_ha']):
        md, lo, hi, fp = paired_boot(g['largest_gap'].values, g[s].values)
        rows.append({'veg_type': t, 'wind_speed': w, 'density_ha': d, 'strategy': s,
                     'N': len(g), 'median_diff': md, 'ci_lo': lo, 'ci_hi': hi,
                     'frac_positive': fp, 'sig': (lo > 0) or (hi < 0)})
diffs = pd.DataFrame(rows)
diffs.to_csv(os.path.join(OUT, 'strategy_differences.csv'), index=False)

##### INITIAL FLUX (NO STRUCTURES), TABLE S2 #####

def stats(x):
    return pd.Series({'N': len(x), 'mean': x.mean(), 'median': x.median(), 'sd': x.std(),
                      'IQR': x.quantile(0.75) - x.quantile(0.25), 'min': x.min(), 'max': x.max()})

s2 = base.groupby(['veg_type', 'wind_speed']).initial_gmd.apply(stats).unstack().reset_index()
s2.round(1).to_csv(os.path.join(OUT, 'initial_flux_stats.csv'), index=False)

##### NUMBERS FOR THE RESULTS SECTION #####

print('\nInitial flux, median g/m/d (percent of plots with zero flux)')
for w in WINDS:
    line = []
    for t in TYPES:
        x = base[(base.veg_type == t) & (base.wind_speed == w)].initial_gmd
        line.append(f'{t} {x.median():7.1f} ({100 * (x <= 0).mean():4.1f}%)')
    print(f'  {w:2d} m/s: ' + ' | '.join(line))

print('\nShare of total flux from the highest-flux plots, 16 m/s')
x = np.sort(base[base.wind_speed == 16].initial_gmd.values)[::-1]
print(f'  top 10%: {100 * x[:int(0.1 * len(x))].sum() / x.sum():.1f}%  '
      f'top 20%: {100 * x[:int(0.2 * len(x))].sum() / x.sum():.1f}%')

print('\nMean percent reduction at 16 m/s, all types (complete case)')
print('  density  ' + '  '.join(f'{s:>12}' for s in STRATEGIES))
for d in DENSITIES:
    r = [cc[(cc.strategy == s) & (cc.wind_speed == 16) & (cc.density_ha == d)].pct.mean() for s in STRATEGIES]
    print(f'  {d:7d}  ' + '  '.join(f'{v:12.1f}' for v in r))

print('\nWin rate pooled over 12, 16, 20 m/s (%)')
for _, r in win_pooled.iterrows():
    print(f'  {r.strategy:12s} {100 * r.win_rate:5.1f}')

print('\nScaled-gap minus largest-gap (percentage points), cells where 95% CI excludes 0')
sd = diffs[diffs.strategy == 'scaled_gap']
for w in [12, 16, 20]:
    s = sd[(sd.wind_speed == w) & sd.sig]
    print(f'  {w} m/s: {int((s.median_diff > 0).sum())} positive, {int((s.median_diff < 0).sum())} negative')
print('  shrub, 20 m/s:', {int(r.density_ha): round(r.median_diff, 1)
                           for _, r in sd[(sd.veg_type == 'shrub') & (sd.wind_speed == 20)].iterrows()})

print('\nLowest tested density where median reduction >= 50, 75, 90% (largest-gap, 16 m/s)')
for t in TYPES:
    s = rel[(rel.veg_type == t) & (rel.strategy == 'largest_gap') & (rel.wind_speed == 16)]
    out = []
    for target in [50, 75, 90]:
        ok = s[s.median_pct >= target]
        out.append(f'{target}%: {int(ok.density_ha.min()) if len(ok) else "> 4000"}')
    print(f'  {t:6s} ' + ' | '.join(out))

print('\nMedian initial and remaining flux at 1,000 structures per ha, largest-gap (Table S4)')
for w in [12, 16, 20]:
    for t in TYPES:
        s = cc[(cc.veg_type == t) & (cc.wind_speed == w) & (cc.density_ha == 1000) & (cc.strategy == 'largest_gap')]
        print(f'  {w} m/s {t:6s} n = {len(s):3d}  initial {s.initial_gmd.median():8.1f}  remaining {s.hflux_gmd.median():7.1f}')

print('\nTotal vs mean plot-level reduction, largest-gap, 16 m/s')
for d in [250, 500, 1000]:
    s = cc[(cc.strategy == 'largest_gap') & (cc.wind_speed == 16) & (cc.density_ha == d)]
    print(f'  {d:5d}/ha: total {100 * s.Q_avoided.sum() / s.initial_gmd.sum():.1f}%  '
          f'mean of plots {s.pct.mean():.1f}%  (n = {len(s)})')

print('\nTreating the highest-flux 25% of plots first, largest-gap, 1,000 per ha, 16 m/s')
s = cc[(cc.strategy == 'largest_gap') & (cc.wind_speed == 16) & (cc.density_ha == 1000)]
s = s.sort_values('initial_gmd', ascending=False)
k = round(0.25 * len(s))
print(f'  {len(s)} plots; top quarter gives {100 * s.Q_avoided.iloc[:k].sum() / s.initial_gmd.sum():.1f}% '
      f'of total flux reduction vs about {100 * 0.25 * s.Q_avoided.sum() / s.initial_gmd.sum():.1f}% '
      f'for the same number of plots chosen without priority')
