# XRD-utils Usage Guide

`XRD-utils` owns XRD line-scan loading, peak analysis, stacked scan plotting,
and reciprocal-space map visualization. Generic axis/figure helpers can come
from `sci-viz-utils`, but XRD conventions stay here.

## Install For Development

```bash
git clone https://github.com/yig319/XRD-utils.git
cd XRD-utils
python -m pip install -r requirements-dev.txt
python -m pip install -e .
```

## Load And Plot A Scan

```python
from xrd_utils.xrd_utils import load_xrd_scan
from xrd_utils.xrd_viz import plot_stacked_scans

scan = load_xrd_scan("scan.xy")
fig_ax = plot_stacked_scans({"sample": scan}, normalize=True, offset=1.2)
```

## Peak Table

```python
from xrd_utils.xrd_utils import find_peaks_table

peaks = find_peaks_table(
    scan,
    windows={"film": (20, 80)},
    prominence=0.1,
)
print(peaks)
```

## Reciprocal-Space Map

```python
from xrd_utils.rsm_viz import RSMPlotter

plotter = RSMPlotter(plot_params={"cmap": "viridis", "levels": 60})
fig, ax = None, None
qx, qz, intensity = plotter.plot("map.xrdml")
```

## What Belongs Here

Keep XRD/RSM-specific behavior in `XRD-utils`: scan parsing, peak analysis,
FWHM, lattice calculations, reciprocal-space transforms, and XRD plotting
defaults. Put only generic layout, colorbar, or axis helpers in
`sci-viz-utils`.
