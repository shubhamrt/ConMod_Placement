# Title: "Select the 1,500 study plots"
# Author: "Shubham Tiwari"
# Date Started: "2026-07-14"
# Date Updated: "2026-10-14"

# Description:
# Study plots come from the BLM Assessment, Inventory, and Monitoring (AIM) and
# NRCS Landscape Monitoring Framework (LMF) indicator tables downloaded from the
# Landscape Data Commons (LDC). We keep plots in the western US (longitude -125
# to -100, latitude 31 to 50) with more than 20% bare soil, a large-gap cover
# value, a vegetation height, and an AERO model configuration. Repeat visits to
# the same location are removed.
#
# Plots are classed by first-hit cover:
#   grass: graminoid >= 30% and shrub < 10%
#   shrub: shrub >= 20% and graminoid < 15%
#   mixed: graminoid >= 15% and shrub > 10%
# Plot height is graminoid height for grass, woody height for shrub and the mean
# of the two for mixed plots.
#
# We draw 1,500 candidates per class and screen them with the LDC gap and height
# records. A plot is kept if it has at least 5 canopy gaps, 3 transect lines,
# 3 gaps with a measured edge height and 3 distinct bordering heights (so that
# scaled-gap can differ from largest-gap). From the eligible AIM plots we draw
# 500 per class. LMF plots were screened but not used, because their height
# records give only about two distinct heights per plot.
#
# Data access: AIM indicators downloaded 10 June 2026, LDC gap and height
# records downloaded 14-15 July 2026. The final list is data/study_plots.csv.
# In the original run the order of the screened plots depended on when each
# download finished, so the random draw cannot be repeated exactly. Here the
# screened plots are sorted first, which makes reruns repeatable, but a rerun
# will not give the same 1,500 plots. Use data/study_plots.csv for the paper set.
#
# This script was used for the plot selection and Figure 2 in Tiwari et al.

# Inputs:  geoIndicators tables (AIM, LMF) from the LDC, AERO configuration
#          folders (one .ini per PrimaryKey), LDC API (dataGap, dataHeight)
# Outputs: output/plot_screen.csv, output/selected_plots.csv,
#          output/map_background_plots.csv

import os, re, json, time, statistics, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd

##### SETUP #####

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, 'output')
CACHE = os.path.join(OUT, 'ldc_cache')
os.makedirs(CACHE, exist_ok=True)

# Local copies of the LDC indicator tables and AERO configurations (change these)
DATA = r'C:\Users\shubhamt\Desktop\Postdoc\Aero\Data'
GEO = {'AIM': os.path.join(DATA, 'geoIndicators_all_indicators_AIM_06102026.csv'),
       'LMF': os.path.join(DATA, 'geoIndicators_all_vars_06052026.csv')}
CFG = {'AIM': os.path.join(DATA, 'AERO_AIM', 'AERO_AIM'),
       'LMF': os.path.join(DATA, 'AERO_LMF', 'AERO_LMF')}
API = 'https://api.landscapedatacommons.org/api/v1'

N_CANDIDATES = 1500     # candidates screened per class
N_SELECT = 500          # plots selected per class
SEED = 42
CM_TO_M = 100.0

##### CANDIDATE POOL #####

def num(x):
    return pd.to_numeric(x, errors='coerce')

def veg_class(grass, shrub):
    if grass >= 30 and shrub < 10: return 'grass'
    if shrub >= 20 and grass < 15: return 'shrub'
    if grass >= 15 and shrub > 10: return 'mixed'
    return 'unclassified'

# Location id without the visit date, to drop repeat visits
def loc_aim(pk): return re.sub(r'\d{4}-\d{2}-\d{2}$', '', re.sub(r'_V\d.*$', '', pk))
def loc_lmf(pk): return re.sub(r'B\d+$', '', pk)

COLS = ['PrimaryKey', 'Latitude_NAD83', 'Longitude_NAD83', 'BareSoil', 'FH_GraminoidCover',
        'FH_ShrubCover', 'TotalFoliarCover', 'GapCover_101_200', 'GapCover_200_plus',
        'Hgt_Graminoid_Avg', 'Hgt_Woody_Avg']

def read_indicators(src):
    d = pd.read_csv(GEO[src], usecols=COLS, low_memory=False)
    d['LAT'] = num(d.Latitude_NAD83)
    d['LON'] = num(d.Longitude_NAD83)
    d = d[d.LON.between(-125, -100) & d.LAT.between(31, 50)].copy()
    d['PrimaryKey'] = d.PrimaryKey.astype(str)
    d['source'] = src
    d['loc'] = d.PrimaryKey.map(loc_aim if src == 'AIM' else loc_lmf)
    d['grass'] = num(d.FH_GraminoidCover)
    d['shrub'] = num(d.FH_ShrubCover)
    d['bare'] = num(d.BareSoil)
    d['cover'] = num(d.TotalFoliarCover)
    d['largegap'] = num(d.GapCover_101_200).fillna(0) + num(d.GapCover_200_plus).fillna(0)
    d['gh'] = num(d.Hgt_Graminoid_Avg)
    d['wh'] = num(d.Hgt_Woody_Avg)
    d['cls'] = [veg_class(g, s) for g, s in zip(d.grass, d.shrub)]
    return d

def plot_height(r):
    if r.cls == 'grass': return r.gh
    if r.cls == 'shrub': return r.wh
    both = [x for x in (r.gh, r.wh) if pd.notna(x)]
    return np.mean(both) if both else np.nan

# Plots with an AERO configuration
has_cfg = {s: set(f[:-4] for f in os.listdir(CFG[s]) if f.endswith('.ini')) for s in CFG}

pool = []
for src in ['AIM', 'LMF']:
    d = read_indicators(src)
    d = d[[pk in has_cfg[src] for pk in d.PrimaryKey]]
    d = d[(d.cls != 'unclassified') & (d.bare > 20) & d.cover.notna() & (d.largegap > 0)]
    pool.append(d.sort_values('PrimaryKey').drop_duplicates(['source', 'loc']))
pool = pd.concat(pool, ignore_index=True)
pool['height'] = pool.apply(plot_height, axis=1)
pool = pool[pool.height.notna()]
print('candidate pool:', pool.cls.value_counts().to_dict())

# Random draw of candidates per class
rng = np.random.default_rng(SEED)
cand = []
for t in ['grass', 'mixed', 'shrub']:
    sub = pool[pool.cls == t].reset_index(drop=True)
    cand.append(sub.iloc[rng.choice(len(sub), size=min(N_CANDIDATES, len(sub)), replace=False)])
cand = pd.concat(cand, ignore_index=True)

##### SCREEN WITH LDC GAP AND HEIGHT RECORDS #####

def fetch(table, pk):
    # Download LDC records for one plot, or read them from the cache
    path = os.path.join(CACHE, f'{table}_{urllib.parse.quote(pk, safe="")}.json')
    if os.path.exists(path):
        return json.load(open(path))
    url = f'{API}/{table}?PrimaryKey={urllib.parse.quote(pk)}'
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                data = json.load(r)
            json.dump(data, open(path, 'w'))
            return data
        except Exception:
            time.sleep(2 * (attempt + 1))
    return []

def field(rec, names, cast=float):
    keys = {k.lower(): k for k in rec}
    for n in names:
        k = keys.get(n.lower())
        if k is not None and rec[k] not in (None, '', 'NA', 'null'):
            try:
                return cast(rec[k])
            except (ValueError, TypeError):
                if cast is not float:
                    return rec[k]
    return None

def screen(r):
    gaps = fetch('dataGap', r.PrimaryKey)
    hts = fetch('dataHeight', r.PrimaryKey)

    # Heights by transect line as (position m, height m)
    by_line = {}
    for h in hts:
        hv, pos, ln = field(h, ['Height']), field(h, ['PointLoc', 'PointNbr']), field(h, ['LineKey'], str)
        if hv is None or hv <= 0 or pos is None:
            continue
        by_line.setdefault(ln, []).append((pos / CM_TO_M, hv / CM_TO_M))
    all_h = [v for pts in by_line.values() for _, v in pts]
    plot_median = statistics.median(all_h) if all_h else None

    lines, line_len, bh_all = set(), {}, []
    n_meas = 0
    for g in gaps:
        rt = field(g, ['RecType'], str)
        if rt is not None and not str(rt).lower().startswith('c') and 'canop' not in str(rt).lower():
            continue
        L = field(g, ['Gap'])
        if L is None or L <= 0:
            continue
        ln = field(g, ['LineKey'], str)
        lines.add(ln)
        ll = field(g, ['LineLengthAmount'])   # already in m
        if ll:
            line_len[ln] = ll
        gs, ge = field(g, ['GapStart']), field(g, ['GapEnd'])
        pts = by_line.get(ln, [])
        def near(x):
            return min(pts, key=lambda t: abs(t[0] - x))[1] if pts else None
        edges = [x for x in (near(gs / CM_TO_M) if gs is not None else None,
                             near(ge / CM_TO_M) if ge is not None else None) if x]
        if edges:
            bh = sum(edges) / len(edges)
            n_meas += 1
        elif plot_median:
            bh = plot_median
        else:
            bh = r.height / 100.0
        bh_all.append(round(bh, 4))

    n_gaps = len(bh_all)
    tlen = sum(line_len.values()) if line_len else np.nan
    n_dist = len(set(bh_all))
    ok = n_gaps >= 5 and len(lines) >= 3 and n_meas >= 3 and n_dist >= 3
    return {'PrimaryKey': r.PrimaryKey, 'source': r.source, 'loc': r.loc, 'cls': r.cls,
            'LON': r.LON, 'LAT': r.LAT, 'cover': r.cover, 'largegap': r.largegap,
            'height': round(r.height, 3), 'bare': round(r.bare, 2),
            'n_lines': len(lines), 'n_canopy_gaps': n_gaps,
            'transect_length_m': round(tlen, 2) if tlen == tlen else '',
            'n_measured_gaps': n_meas, 'n_distinct_heights': n_dist, 'eligible': int(ok)}

screened = []
with ThreadPoolExecutor(max_workers=12) as ex:
    jobs = [ex.submit(screen, r) for r in cand.itertuples(index=False)]
    for k, job in enumerate(as_completed(jobs), 1):
        screened.append(job.result())
        if k % 500 == 0:
            print(f'screened {k} of {len(cand)}')
screened = pd.DataFrame(screened).sort_values(['cls', 'PrimaryKey']).reset_index(drop=True)
screened.to_csv(os.path.join(OUT, 'plot_screen.csv'), index=False)

##### SELECT 500 AIM PLOTS PER CLASS #####

elig = screened[(screened.eligible == 1) & (screened.source == 'AIM')]
print('eligible AIM plots:', elig.cls.value_counts().to_dict())

rng = np.random.default_rng(SEED)
sel = []
for t in ['grass', 'mixed', 'shrub']:
    sub = elig[elig.cls == t].reset_index(drop=True)
    sel.append(sub.iloc[rng.choice(len(sub), size=N_SELECT, replace=False)])
sel = pd.concat(sel, ignore_index=True)
sel['plot_id'] = [f'{c}_{i:04d}' for c, i in zip(sel.cls, sel.groupby('cls').cumcount() + 1)]
sel.to_csv(os.path.join(OUT, 'selected_plots.csv'), index=False)

##### MAP BACKGROUND: ALL WESTERN AIM LOCATIONS #####

aim = read_indicators('AIM').sort_values('PrimaryKey').drop_duplicates(['source', 'loc'])
aim[['LON', 'LAT']].rename(columns={'LON': 'longitude', 'LAT': 'latitude'}).to_csv(
    os.path.join(OUT, 'map_background_plots.csv'), index=False)
print('selected:', sel.cls.value_counts().to_dict(), '| background locations:', len(aim))
