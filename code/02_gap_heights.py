# Title: "Bordering vegetation height for each canopy gap"
# Author: "Shubham Tiwari"
# Date Started: "2026-07-18"
# Date Updated: "2026-10-14"

# Description:
# The scaled-gap strategy ranks gaps by gap length divided by the height of the
# vegetation at the gap edges, so it needs a height for every gap. For each study
# plot we download the line-point intercept gap (dataGap) and height (dataHeight)
# records from the Landscape Data Commons (LDC) and match each canopy gap edge to
# the nearest height measurement on the same transect line. The bordering height
# is the mean of the two edge heights. Where no height is recorded on the line we
# use the plot median height. At each point the taller of the woody and
# herbaceous heights is used, because the taller plant forms the gap edge.
#
# This height is only used to rank gaps for placement. AERO uses one mean
# vegetation height per plot.
#
# The plot means of gap length and scaled gap (gap length / bordering height)
# in data/study_plots.csv come from this table.

# Inputs:  data/study_plots.csv, LDC API (dataGap, dataHeight)
# Outputs: output/ldc_gap_heights.csv (one row per canopy gap)
#          output/ldc_cache/ (downloaded LDC records)

import os, csv, json, time, statistics, urllib.parse, urllib.request

##### SETUP #####

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, 'data')
OUT = os.path.join(REPO, 'output')
CACHE = os.path.join(OUT, 'ldc_cache')
os.makedirs(CACHE, exist_ok=True)

API = 'https://api.landscapedatacommons.org/api/v1'
CM_TO_M = 100.0   # LDC gap positions, lengths and heights are in cm

##### LDC DOWNLOAD #####

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
    print('download failed:', table, pk)
    return []

def field(rec, names, cast=float):
    # LDC field names differ in case between tables, so try each name
    keys = {k.lower(): k for k in rec}
    for n in names:
        k = keys.get(n.lower())
        if k is not None and rec[k] not in (None, '', 'NA', 'null'):
            try:
                return cast(rec[k])
            except (ValueError, TypeError):
                if cast is float:
                    continue
                return rec[k]
    return None

GAP_LEN = ['Gap', 'GapSize']
GAP_START = ['GapStart']
GAP_END = ['GapEnd']
GAP_TYPE = ['RecType', 'GapType']
LINE = ['LineKey']
HT = ['Height']
HT_POS = ['PointLoc', 'PointNbr']

def nearest_height(pos, points):
    # Height of the measurement point closest to pos
    if not points:
        return None
    return min(points, key=lambda t: abs(t[0] - pos))[1]

##### ONE ROW PER CANOPY GAP #####

plots = list(csv.DictReader(open(os.path.join(DATA, 'study_plots.csv'))))
rows = []
for i, p in enumerate(plots, 1):
    pk, pid = p['PrimaryKey'], p['plot_id']
    gaps = fetch('dataGap', pk)
    hts = fetch('dataHeight', pk)

    # Heights by line as (position m, height m), taller plant at each point
    by_line = {}
    for h in hts:
        hv, pos, ln = field(h, HT), field(h, HT_POS), field(h, LINE, str)
        if hv is None or hv <= 0 or pos is None:
            continue
        pts = by_line.setdefault(ln, {})
        pts[pos / CM_TO_M] = max(pts.get(pos / CM_TO_M, 0.0), hv / CM_TO_M)
    by_line = {ln: sorted(pts.items()) for ln, pts in by_line.items()}
    all_h = [v for pts in by_line.values() for _, v in pts]
    plot_median = statistics.median(all_h) if all_h else None

    for g in gaps:
        # Canopy gaps only
        rt = field(g, GAP_TYPE, str)
        if rt is not None and not str(rt).lower().startswith('c') and 'canop' not in str(rt).lower():
            continue
        L = field(g, GAP_LEN)
        if L is None or L <= 0:
            continue
        gs, ge, ln = field(g, GAP_START), field(g, GAP_END), field(g, LINE, str)
        pts = by_line.get(ln, [])
        hs = nearest_height(gs / CM_TO_M, pts) if gs is not None and ge is not None else None
        he = nearest_height(ge / CM_TO_M, pts) if gs is not None and ge is not None else None

        # Bordering height = mean of edge heights, else plot median, else plot mean height
        edges = [x for x in (hs, he) if x]
        if edges:
            bh, source = sum(edges) / len(edges), 'measured'
        elif plot_median:
            bh, source = plot_median, 'plot_median'
        else:
            bh, source = float(p['veg_height_cm']) / 100.0, 'plot_mean'
        length = L / CM_TO_M
        rows.append({'PrimaryKey': pk, 'plot_id': pid, 'LineKey': ln,
                     'gap_start_m': None if gs is None else round(gs / CM_TO_M, 3),
                     'gap_end_m': None if ge is None else round(ge / CM_TO_M, 3),
                     'length_m': round(length, 4),
                     'h_start_m': None if hs is None else round(hs, 4),
                     'h_end_m': None if he is None else round(he, 4),
                     'bordering_height_m': round(bh, 4), 'height_source': source,
                     'scaled_gap': round(length / bh, 3)})
    if i % 100 == 0:
        print(f'{i} of {len(plots)} plots, {len(rows)} gaps')

##### SAVE #####

with open(os.path.join(OUT, 'ldc_gap_heights.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f'wrote output/ldc_gap_heights.csv: {len(rows)} gaps from {len(plots)} plots')
