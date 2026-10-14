# Title: "Build gap files for the four placement strategies"
# Author: "Shubham Tiwari"
# Date Started: "2026-07-20"
# Date Updated: "2026-10-14"

# Description:
# AERO describes the plot surface as a list of canopy gap lengths. A restoration
# structure placed in a gap splits it into two shorter gaps, so we represent
# structures by splitting gaps in each plot's AERO gap file. Total gap length
# stays the same, only the gap size distribution changes.
#
# The four placement strategies are:
#   largest-gap:  split the longest gap at its midpoint, repeat
#   scaled-gap:   split the gap with the largest gap length / bordering height, repeat
#   proportional: give each gap a share of the structures in proportion to its length
#   cell-grid:    divide the transect into N equal cells and put one structure in the
#                 largest gap in each cell
#
# Structure density is given per hectare. For a square grid, n per ha = (n per 100 m)^2,
# so structures per 100 m of transect = sqrt(n per ha). A structure is not placed
# if it would make a sub-gap shorter than 0.25 m. Structures that could not be
# placed are counted as deployed but not placed (n_structures vs n_placed).
#
# For scaled-gap, each AERO gap gets the bordering height of the LDC gap with the
# nearest length on the same plot (from 02_gap_heights.py).
#
# Gap lengths are written with a small random jitter (+/-1%) because AERO's gap
# binning fails on lists with many identical lengths. The seed is fixed, and the
# loop order (plot, density, strategy) has to stay as it is to get the same files
# used in the paper. The paper files were made with Python 3.12 (sum() of floats
# changed in 3.12, which moves a few rounding ties in the proportional strategy).
#
# The AERO gap files (one per PrimaryKey) come with the AERO model configuration
# and are not included here. Contact the AERO developers (Edwards et al. 2022).
#
# This script was used to make the placement inputs for Tiwari et al. (Figures 3, 5-8).

# Inputs:  data/study_plots.csv, output/ldc_gap_heights.csv, AERO gap files
# Outputs: output/gap_files/<plot_id>__<strategy>__d<density>.txt
#          output/placement_layouts.csv

import os, csv, heapq, math, random

##### SETUP #####

# Repository folder (one level up from code/)
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, 'data')
OUT = os.path.join(REPO, 'output')
GAP_OUT = os.path.join(OUT, 'gap_files')
os.makedirs(GAP_OUT, exist_ok=True)

# Folder with the AERO gap files, <PrimaryKey>.txt (change to your copy)
AERO_GAP_DIR = r'C:\Users\shubhamt\Desktop\Postdoc\Aero\Data\AERO_AIM\AERO_AIM\gap'

DENSITIES = [100, 250, 500, 1000, 2000, 4000]   # structures per ha
CAP_PER_GAP = 3       # at most 3 structures per original gap, on average, in a plot
MIN_SUBGAP = 0.25     # m, shortest sub-gap a structure can create
JITTER = 0.01         # +/-1% on written gap lengths
random.seed(42)

##### READ DATA #####

# Load study plots
plots = list(csv.DictReader(open(os.path.join(DATA, 'study_plots.csv'))))

# Load LDC gap lengths and bordering heights, by PrimaryKey
ldc = {}
for row in csv.DictReader(open(os.path.join(OUT, 'ldc_gap_heights.csv'))):
    ldc.setdefault(row['PrimaryKey'], ([], []))
    ldc[row['PrimaryKey']][0].append(float(row['length_m']))
    ldc[row['PrimaryKey']][1].append(float(row['bordering_height_m']))

def read_gaps(path):
    gaps = []
    for line in open(path):
        line = line.strip()
        if line and not line.startswith('#'):
            try:
                gaps.append(float(line))
            except ValueError:
                pass
    return gaps

def bordering_heights(pk, gaps):
    # Height of the LDC gap with the nearest length
    lengths, heights = ldc[pk]
    out = []
    for g in gaps:
        i = min(range(len(lengths)), key=lambda j: abs(lengths[j] - g))
        out.append(heights[i])
    return out

def write_gaps(path, gaps):
    # Write one gap length per line, with jitter
    with open(path, 'w') as f:
        for g in gaps:
            f.write(f'{g * (1 + random.uniform(-JITTER, JITTER)):.5f}\n')

##### PLACEMENT STRATEGIES #####
# Each function returns the new gap list and the number of structures placed

def largest_gap(gaps, n):
    # Split the longest remaining gap in half, n times
    h = [-g for g in gaps]
    heapq.heapify(h)
    placed = 0
    for _ in range(n):
        if not h or -h[0] < 2 * MIN_SUBGAP:
            break
        g = -heapq.heappop(h)
        heapq.heappush(h, -g / 2.0)
        heapq.heappush(h, -g / 2.0)
        placed += 1
    return sorted((-x for x in h), reverse=True), placed

def scaled_gap(gaps, heights, n):
    # Split the gap with the largest length/height ratio, n times.
    # The two halves keep the bordering height of the original gap.
    h = [(-(L / H), L, H) for L, H in zip(gaps, heights)]
    heapq.heapify(h)
    too_short = []
    placed = 0
    while placed < n and h:
        _, L, H = heapq.heappop(h)
        if L < 2 * MIN_SUBGAP:
            too_short.append(L)
            continue
        heapq.heappush(h, (-((L / 2.0) / H), L / 2.0, H))
        heapq.heappush(h, (-((L / 2.0) / H), L / 2.0, H))
        placed += 1
    return sorted([L for _, L, _ in h] + too_short, reverse=True), placed

def proportional(gaps, n):
    # Number of structures in each gap is proportional to its length
    # (largest remainder rounding). Each gap is split into equal pieces.
    total = float(sum(gaps))
    if total <= 0 or n <= 0:
        return list(gaps), 0
    cap = [max(0, int(g / MIN_SUBGAP) - 1) for g in gaps]
    share = [g / total * n for g in gaps]
    k = [min(int(x), cap[i]) for i, x in enumerate(share)]
    order = sorted(range(len(gaps)), key=lambda i: share[i] - k[i], reverse=True)
    left = n - sum(k)
    while left > 0:
        added = False
        for i in order:
            if left <= 0:
                break
            if k[i] < cap[i]:
                k[i] += 1
                left -= 1
                added = True
        if not added:
            break
    out = []
    for g, ki in zip(gaps, k):
        out.extend([g / (ki + 1)] * (ki + 1))
    return out, sum(k)

def cell_grid(gaps, n, transect):
    # Cell width w = transect / n. A gap of length L covers at most ceil(L/w)
    # cells, so it can hold at most that many structures. Structures go into the
    # largest available gap first. At high density some cells have no gap long
    # enough, so fewer than n structures may be placed.
    if n <= 0 or not gaps:
        return list(gaps), 0
    w = float(transect) / n
    cap = [max(1, math.ceil(g / w)) for g in gaps]
    k = [0] * len(gaps)
    h = [(-g, i) for i, g in enumerate(gaps)]
    heapq.heapify(h)
    placed = 0
    while placed < n and h:
        _, i = heapq.heappop(h)
        if k[i] >= cap[i]:
            continue
        if gaps[i] / (k[i] + 2) < MIN_SUBGAP:
            continue
        k[i] += 1
        placed += 1
        heapq.heappush(h, (-(gaps[i] / (k[i] + 1)), i))
    out = []
    for g, ki in zip(gaps, k):
        out.extend([g / (ki + 1)] * (ki + 1))
    return out, placed

##### BUILD GAP FILES FOR EVERY PLOT, DENSITY AND STRATEGY #####

layouts = []
for i, p in enumerate(plots, 1):
    pid, pk = p['plot_id'], p['PrimaryKey']
    gaps = read_gaps(os.path.join(AERO_GAP_DIR, pk + '.txt'))
    heights = bordering_heights(pk, gaps)
    transect = float(p['transect_length_m'])

    for dens in DENSITIES:
        per100 = math.sqrt(dens)
        N = max(1, int(round(per100 * transect / 100.0)))
        N = min(N, CAP_PER_GAP * len(gaps))
        result = {'largest_gap': largest_gap(gaps, N),
                  'scaled_gap': scaled_gap(gaps, heights, N),
                  'proportional': proportional(gaps, N),
                  'cell_grid': cell_grid(gaps, N, transect)}
        for strategy, (new_gaps, placed) in result.items():
            fname = f'{pid}__{strategy}__d{dens}.txt'
            write_gaps(os.path.join(GAP_OUT, fname), new_gaps)
            layouts.append({'plot_id': pid, 'PrimaryKey': pk, 'veg_type': p['veg_type'],
                            'strategy': strategy, 'density_ha': dens,
                            'n_structures': N, 'n_placed': placed,
                            'n_gaps_before': len(gaps), 'n_gaps_after': len(new_gaps),
                            'gap_file': fname})
    if i % 250 == 0:
        print(f'{i} of {len(plots)} plots done')

# Save the list of layouts
with open(os.path.join(OUT, 'placement_layouts.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(layouts[0].keys()))
    w.writeheader()
    w.writerows(layouts)
print(f'wrote {len(layouts)} gap files and output/placement_layouts.csv')
