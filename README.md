# Strategic placement of restoration structures for wind erosion control

Data and code for:

Tiwari, S., Edwards, B. L., Young, K. E., Duniway, M. C., & Webb, N. P. Strategic placement of restoration structures increases wind erosion control in drylands. *Communications Earth & Environment* (in review).

## Overview

Restoration structures such as brush barriers, straw checkerboards and connectivity modifiers (ConMods) reduce wind erosion by breaking up long bare-soil gaps between plants. This study asked where to place a limited number of structures. We used the Aeolian EROsion (AERO) model to compare four placement strategies across 1,500 monitoring plots in grass-dominated, mixed grass-shrub and shrub-dominated drylands of the western United States, at six structure densities (100 to 4,000 structures per hectare) and four wind speeds (8, 12, 16 and 20 m s-1).

The four placement strategies are:

- **Largest-gap**: structures go into the longest canopy gaps first.
- **Scaled-gap**: structures go into gaps with the largest ratio of gap length to bordering vegetation height first.
- **Proportional**: structures are spread among gaps in proportion to gap length.
- **Cell-grid**: the transect is divided into equal cells with one structure placed in each.

## Data collection and modeling approach

**Plot data.** All plot data are from the Bureau of Land Management Assessment, Inventory, and Monitoring (AIM) program and are publicly available from the Landscape Data Commons (LDC; https://landscapedatacommons.org). Plots are identified here by their LDC `PrimaryKey`. Plot indicators were downloaded on 10 June 2026, and line-point intercept gap and height records on 14-15 July 2026 through the LDC API. We selected 500 plots per vegetation type with more than 20% bare soil in the western United States (see `code/01_select_study_plots.py`).

**AERO model.** Horizontal sediment flux was modeled with AERO (Edwards et al. 2022) using the GLUE posterior-median parameters from Edwards et al. (2022): C = 0.06, z0 = 0.0003 m, phi at l=0 = 0.18, r = 6.11 and Gamma = 0.00037. Each plot was run with its own soil texture, vegetation cover, mean vegetation height and canopy gap distribution. Structures were represented by splitting canopy gaps in the plot's gap distribution, keeping total gap length the same. The AERO model and the plot model inputs (configuration and gap files) are not included in this repository. AERO is described by Edwards et al. (2022) and is available from its developers.

**Sensitivity runs.** A 90-plot subsample (30 per vegetation type, 10 from each tertile of initial flux at 16 m s-1) was rerun with six other parameter sets from the posterior quartiles of r, phi at l=0 and Gamma.

## Repository contents

```
data/
  study_plots.csv           1,500 study plots: PrimaryKey, vegetation type, location and plot indicators
  baseline_flux.csv         Modeled flux without structures (1,500 plots x 4 wind speeds)
  placement_flux.csv        Modeled flux with structures (plot x strategy x density x wind speed)
  sensitivity_flux.csv      Parameter sensitivity runs (90 plots x 7 parameter sets)
  map_background_plots.csv  All unique AIM plot locations in the study region (Figure 2)
  metadata.csv              Description and units of every column
code/
  01_select_study_plots.py      Plot selection from LDC indicators and gap and height records
  02_gap_heights.py             Bordering vegetation height of each canopy gap (LDC records)
  03_build_placement_layouts.py Gap files for the four strategies and six densities
  04_run_aero.py                AERO runs (baseline, placement, sensitivity)
  05_placement_results.py       Flux reduction, win rate, bootstrap comparisons; Results numbers
  06_sensitivity_checks.py      Parameter sensitivity (Table S5) and low-density check (Table S7)
  figures/
    Fig2_study_plots.m          Figure 2
    Fig4_initial_flux.m         Figure 4
    Fig5to8_placement.m         Figures 5-8
```

## How to use

Python 3.12 or later with numpy and pandas; MATLAB R2023a or later for the figures.

The results and figures can be reproduced from the archived data. Run from the repository folder:

```
python code/05_placement_results.py
python code/06_sensitivity_checks.py
```

then run the MATLAB scripts in `code/figures`. Outputs are written to `output/`.

Scripts 01 to 04 document how the data were made. Scripts 01 and 02 download records from the LDC API. Scripts 03 and 04 need the AERO model and plot configuration files, which are not included; set the folder paths at the top of these scripts. The paper files were made with Python 3.12 or later. Older Python versions add floats slightly differently and change a few rounding ties in the proportional strategy.

## Limitations and considerations

- AERO represents each plot as a one-dimensional distribution of canopy gap lengths and one mean vegetation height. Structures were treated as vegetation of the plot mean height, with no porosity or structure-specific height.
- In some runs AERO predicts more flux with structures than without, mostly at low density and low wind speed. This comes from how AERO represents the gap size distribution when a long gap is split, not from the structures themselves. These increases were kept in the main results; Table S7 (`06_sensitivity_checks.py`) shows how they affect the low-density comparison.
- In a small number of runs with more than 100 gaps, AERO returned no value (about 0.7% at 16 m s-1). These runs are missing from `placement_flux.csv`, and comparisons between strategies use only plots where all 24 strategy x density runs finished (`complete_case` in `05_placement_results.py`).
- Wind speeds are fixed reference values, not site wind records, so fluxes show relative differences between strategies and plots rather than annual sediment loss.
- The plots are a balanced sample by vegetation type and are not area-weighted.
- The selection draw depended on the order of parallel downloads and cannot be repeated exactly. `data/study_plots.csv` lists the plots used.

## References

Edwards, B. L., Webb, N. P., Galloza, M. S., Van Zee, J. W., Courtright, E. M., Cooper, B. F., et al. (2022). Parameterizing an aeolian erosion model for rangelands. *Aeolian Research*, 54, 100769. https://doi.org/10.1016/j.aeolia.2021.100769

McCord, S. E., et al. (2023). The Landscape Data Commons: A system for standardizing, accessing, and applying large environmental datasets for agroecosystem research and management. *Agricultural & Environmental Letters*, 8(2), e20120. https://doi.org/10.1002/ael2.20120

Okin, G. S. (2008). A new model of wind erosion in the presence of vegetation. *Journal of Geophysical Research: Earth Surface*, 113, F02S10. https://doi.org/10.1029/2007JF000758

## Contact

Shubham Tiwari (GitHub: shubhamrt)

## License

CC BY 4.0
