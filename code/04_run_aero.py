# Title: "AERO runs with and without restoration structures"
# Author: "Shubham Tiwari"
# Date Started: "2026-07-20"
# Date Updated: "2026-10-14"

# Description:
# Runs the Aeolian EROsion (AERO) model (Edwards et al. 2022) for each study plot.
# Three sets of runs:
#   baseline:    original gaps (no structures), 1,500 plots, 8, 12, 16 and 20 m/s
#   placement:   gap files from 03_build_placement_layouts.py, 4 strategies x
#                6 densities, same plots and wind speeds
#   sensitivity: 90-plot subsample, 7 parameter sets, baseline plus 4 strategies x
#                4 densities (100, 250, 1,000, 2,000 per ha), 12, 16 and 20 m/s
#
# Soil sand and clay fraction, vegetation cover and mean vegetation height are
# taken from each plot's AERO configuration file. Model parameters are the GLUE
# posterior medians from Edwards et al. (2022, Table 3):
#   C (KAWAMURA_51_A) = 0.06, z0 (KAWAMURA_51_Z0) = 0.0003 m,
#   phi at l=0 (KAWAMURA_51_SSR0) = 0.18, r (KAWAMURA_51_EFOLD) = 6.11,
#   Gamma (IVERSEN_WHITE_82_COHES_FORCE) = 0.00037
# Gaps are read as a continuous distribution (GAP_PDIST_DISCRETE = 0).
# Horizontal flux is converted from kg m-1 s-1 to g m-1 d-1 (x 86,400,000).
#
# Each run is a separate AERO call. A few layouts with more than 100 gaps return
# "Error computing value." in AERO; these runs are left out (see README).
# Finished runs are not repeated, so the script can be stopped and restarted.
#
# The AERO model and the plot configuration files are not included here. They
# are available from the AERO developers (Edwards et al. 2022).
#
# Run from the repository folder:
#   python code/04_run_aero.py baseline
#   python code/04_run_aero.py placement
#   python code/04_run_aero.py sensitivity

# Inputs:  data/study_plots.csv, output/gap_files/, AERO model and configuration files
# Outputs: output/baseline_flux.csv, output/placement_flux.csv, output/sensitivity_flux.csv

import os, sys, csv, subprocess
from multiprocessing import Pool

##### SETUP #####

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, 'data')
OUT = os.path.join(REPO, 'output')
GAP_FILES = os.path.join(OUT, 'gap_files')

# AERO model folder and plot configuration folder (change these)
AERO = r'C:\Users\shubhamt\Desktop\Postdoc\Aero\AERO_Model\WEME_SOLUS_RON'
CFG = r'C:\Users\shubhamt\Desktop\Postdoc\Aero\Data\AERO_AIM\AERO_AIM'

RUN = sys.argv[1] if len(sys.argv) > 1 else 'baseline'
RUN_DIR = os.path.join(OUT, 'aero_runs', RUN)
os.makedirs(RUN_DIR, exist_ok=True)

# AERO needs the model folder and its WEME subfolder on the Python path
ENV = dict(os.environ)
ENV['PYTHONPATH'] = os.pathsep.join([AERO, os.path.join(AERO, 'WEME')])

CONV = 86400 * 1000   # kg m-1 s-1 to g m-1 d-1
STRATEGIES = ['largest_gap', 'scaled_gap', 'proportional', 'cell_grid']

# Calibrated parameters: medians, and the posterior quartiles used in the sensitivity runs
MEDIAN = {'C': 0.06, 'Z0': 0.0003, 'SSR0': 0.18, 'EFOLD': 6.11, 'G': 0.00037}
PARAM_SETS = {'median': {},
              'rlo_philo': {'EFOLD': 4.89, 'SSR0': 0.08},
              'rlo_phihi': {'EFOLD': 4.89, 'SSR0': 0.31},
              'rhi_philo': {'EFOLD': 7.19, 'SSR0': 0.08},
              'rhi_phihi': {'EFOLD': 7.19, 'SSR0': 0.31},
              'gamma_lo': {'G': 0.00028},
              'gamma_hi': {'G': 0.00045}}

##### AERO HELPERS #####

def plot_inputs(pk):
    # Soil and vegetation inputs from the plot's configuration file
    keep = ('soil_sand_fraction', 'soil_clay_fraction', 'veg_cover_fraction', 'veg_mean_height')
    vals = {}
    for line in open(os.path.join(CFG, pk + '.ini')):
        if ':' in line:
            k, v = line.split(':', 1)
            if k.strip() in keep:
                vals[k.strip()] = v.strip()
    return vals

def run_aero(name, pk, gap_file, wind, pset='median'):
    # Write the ini file, run AERO and return horizontal flux in g m-1 d-1
    out = os.path.join(RUN_DIR, name + '.txt')
    if read_flux(out) is None:
        p = dict(MEDIAN)
        p.update(PARAM_SETS[pset])
        ini = os.path.join(RUN_DIR, name + '.ini')
        with open(ini, 'w') as f:
            f.write('[DEFAULT_VALUES]\nGAP_PDIST_DISCRETE: 0\n')
            f.write(f"KAWAMURA_51_SSR0: {p['SSR0']}\nKAWAMURA_51_A: {p['C']}\n")
            f.write(f"KAWAMURA_51_Z0: {p['Z0']}\nKAWAMURA_51_EFOLD: {p['EFOLD']}\n")
            f.write(f"IVERSEN_WHITE_82_COHES_FORCE: {p['G']}\n\n[INPUT_VALUES]\n")
            for k, v in plot_inputs(pk).items():
                f.write(f'{k}: {v}\n')
            f.write(f'gap_obsv: {gap_file}\nwind_obsv: {wind}\n\n')
            f.write('[OUTPUTS]\nhorizontal_flux_total\nvertical_flux\n')
        subprocess.run([sys.executable, '-m', 'WEME.aero', ini, '-o', out],
                       cwd=AERO, env=ENV, capture_output=True, text=True)
    q = read_flux(out)
    return None if q is None else q * CONV

def read_flux(out):
    # Horizontal flux from an AERO output file, None if missing or failed
    if not os.path.exists(out):
        return None
    for line in open(out):
        parts = line.strip().split('\t')
        if len(parts) == 2 and parts[0] == 'horizontal_flux_total':
            try:
                return float(parts[1])
            except ValueError:
                return None
    return None

##### RUNS FOR ONE PLOT #####

def plot_runs(p):
    pid, pk, vt = p['plot_id'], p['PrimaryKey'], p['veg_type']
    base_gaps = os.path.join(CFG, 'gap', pk + '.txt')
    rows = []
    if RUN == 'baseline':
        for w in [8, 12, 16, 20]:
            q = run_aero(f'{pid}__baseline_U{w}', pk, base_gaps, w)
            if q is not None:
                rows.append({'plot_id': pid, 'veg_type': vt, 'wind_speed': w, 'hflux_gmd': q})
    elif RUN == 'placement':
        for s in STRATEGIES:
            for d in [100, 250, 500, 1000, 2000, 4000]:
                lay = layouts[(pid, s, d)]
                for w in [8, 12, 16, 20]:
                    q = run_aero(f'{pid}__{s}__d{d}_U{w}', pk, os.path.join(GAP_FILES, lay['gap_file']), w)
                    if q is not None:
                        rows.append({'plot_id': pid, 'veg_type': vt, 'strategy': s, 'density_ha': d,
                                     'wind_speed': w, 'n_structures': lay['n_structures'],
                                     'n_placed': lay['n_placed'], 'hflux_gmd': q})
    elif RUN == 'sensitivity':
        for ps in PARAM_SETS:
            jobs = [('baseline', 0, base_gaps)]
            jobs += [(s, d, os.path.join(GAP_FILES, f'{pid}__{s}__d{d}.txt'))
                     for s in STRATEGIES for d in [100, 250, 1000, 2000]]
            for s, d, gf in jobs:
                for w in [12, 16, 20]:
                    q = run_aero(f'{ps}__{pid}__{s}__d{d}_U{w}', pk, gf, w, ps)
                    if q is not None:
                        rows.append({'param_set': ps, 'plot_id': pid, 'veg_type': vt, 'strategy': s,
                                     'density_ha': d, 'wind_speed': w, 'hflux_gmd': q})
    return rows

##### MAIN #####

plots = list(csv.DictReader(open(os.path.join(DATA, 'study_plots.csv'))))
if RUN == 'sensitivity':
    plots = [p for p in plots if p['sensitivity_group']]

layouts = {}
if RUN == 'placement':
    for r in csv.DictReader(open(os.path.join(OUT, 'placement_layouts.csv'))):
        layouts[(r['plot_id'], r['strategy'], int(r['density_ha']))] = r

if __name__ == '__main__':
    with Pool() as pool:
        results = pool.map(plot_runs, plots, chunksize=10)
    rows = [r for res in results for r in res]
    with open(os.path.join(OUT, f'{RUN}_flux.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f'{RUN}: {len(rows)} runs written to output/{RUN}_flux.csv')
