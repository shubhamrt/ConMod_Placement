# Title: "Sensitivity checks for the placement comparison"
# Author: "Shubham Tiwari"
# Date Started: "2026-07-29"
# Date Updated: "2026-10-14"

# Description:
# Two checks on how much the strategy comparison depends on model choices.
#
# 1. AERO parameters (Table S5). The 90-plot subsample (30 per vegetation type,
#    10 from each tertile of initial flux at 16 m/s) was run with seven parameter
#    sets from the Edwards et al. (2022) GLUE posterior: the posterior medians,
#    the four combinations of low/high r (EFOLD) and phi at l=0 (SSR0), and low
#    and high cohesion (Gamma). For each set we calculate the share of plot x wind
#    x density cases in which each strategy gave the largest flux reduction, at
#    12, 16 and 20 m/s. Only cases where all four strategies ran are used.
#
# 2. Flux increases at low density (Table S7). In some runs AERO predicts more
#    flux with structures than without. This comes from how AERO represents the
#    gap size distribution when a long gap is split, not from the structures. Here we check whether the low-density differences
#    between strategies hold when these increases are set to zero or when plots
#    with any increase are left out. Values are mean paired differences in flux
#    reduction (other strategy minus largest-gap, g m-1 d-1); * means the 95%
#    bootstrap interval of the mean excludes zero.
#
# This script was used for Tables S5 and S7 in Tiwari et al.

# Inputs:  data/sensitivity_flux.csv, output/flux_reduction.csv (from 05_placement_results.py)
# Outputs: output/sensitivity_win_share.csv, output/low_density_check.csv

import os
import numpy as np
import pandas as pd

##### SETUP #####

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, 'data')
OUT = os.path.join(REPO, 'output')

STRATEGIES = ['largest_gap', 'scaled_gap', 'proportional', 'cell_grid']
PSETS = ['median', 'rlo_philo', 'rlo_phihi', 'rhi_philo', 'rhi_phihi', 'gamma_lo', 'gamma_hi']

##### 1. WIN SHARE UNDER EACH PARAMETER SET #####

sens = pd.read_csv(os.path.join(DATA, 'sensitivity_flux.csv'))

# Match runs with structures to the run without structures
base = sens[sens.strategy == 'baseline'][['param_set', 'plot_id', 'wind_speed', 'hflux_gmd']]
base = base.rename(columns={'hflux_gmd': 'initial_gmd'})
runs = sens[sens.strategy.isin(STRATEGIES)]
df = runs.merge(base, on=['param_set', 'plot_id', 'wind_speed'], how='inner')
df = df[df.initial_gmd > 0].copy()
df['Q_avoided'] = df.initial_gmd - df.hflux_gmd

# Keep cases where all four strategies ran
key = ['param_set', 'plot_id', 'wind_speed', 'density_ha']
df['n_runs'] = df.groupby(key).strategy.transform('size')
df = df[df.n_runs == 4].copy()

# Win share, ties split between strategies
df['best'] = df.groupby(key).Q_avoided.transform('max')
df['is_best'] = df.Q_avoided >= df.best - 1e-9
df['n_tied'] = df.groupby(key).is_best.transform('sum')
df['win'] = df.is_best / df.n_tied

share = df.groupby(['param_set', 'strategy']).win.mean().mul(100).unstack()
share = share.reindex(PSETS)[STRATEGIES].round(1)
share['n_plots'] = df.groupby('param_set').plot_id.nunique().reindex(PSETS)
share.to_csv(os.path.join(OUT, 'sensitivity_win_share.csv'))
print('Win share (%) by parameter set, 12-20 m/s')
print(share.to_string())

##### 2. LOW-DENSITY CHECK FOR FLUX INCREASES #####

fr = pd.read_csv(os.path.join(OUT, 'flux_reduction.csv'))
cc = fr[fr.complete_case].copy()
cc['Q_zero'] = cc.Q_avoided.clip(lower=0)   # increases set to zero
rng = np.random.default_rng(7)

def mean_diff(d):
    # Mean paired difference with 95% bootstrap interval; * if it excludes zero
    idx = rng.integers(0, len(d), (2000, len(d)))
    lo, hi = np.percentile(d[idx].mean(1), [2.5, 97.5])
    star = '*' if (lo > 0 or hi < 0) else ''
    return f'{d.mean():+.0f}{star}'

rows = []
for w in [12, 16, 20]:
    for dens in [100, 250]:
        s = cc[(cc.wind_speed == w) & (cc.density_ha == dens)]
        wide = s.pivot_table(index=['plot_id', 'veg_type'], columns='strategy', values=['Q_avoided', 'Q_zero'])
        any_increase = (wide['Q_avoided'] < 0).any(axis=1).values
        for t in ['grass', 'mixed', 'shrub']:
            sel = wide.index.get_level_values(1) == t
            r = {'wind_speed': w, 'density_ha': dens, 'veg_type': t}
            for lab, dat in [('as_modeled', wide['Q_avoided'][sel]),
                             ('increase_set_to_zero', wide['Q_zero'][sel]),
                             ('plots_with_increase_removed', wide['Q_avoided'][sel & ~any_increase])]:
                for s2 in STRATEGIES[1:]:
                    r[f'{lab}_{s2}'] = mean_diff((dat[s2] - dat['largest_gap']).values)
            r['n'] = int(sel.sum())
            r['n_without_increase'] = int((sel & ~any_increase).sum())
            rows.append(r)

low = pd.DataFrame(rows)
low.to_csv(os.path.join(OUT, 'low_density_check.csv'), index=False)
print('\nOther strategy minus largest-gap, mean difference in flux reduction (g m-1 d-1)')
print(low.to_string())
