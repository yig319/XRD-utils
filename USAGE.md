# XRD-utils Usage Guide

`XRD-utils` is responsible for XRD line-scan loading, peak/FWHM/lattice helpers,
scan alignment, stacked plotting, and reciprocal-space map previews.

## Install For Development

```bash
cd XRD-utils
python -m pip install -r requirements-dev.txt
python -m pip install -e .
```

## Workflow: Load 1D XRD Scans

Main entry point: `load_xrd_scan`.
Helpers: `load_many_scans`, `load_xrd_scans`, `process_input`.

Use `load_xrd_scan(path)` for new code; it returns a table with angle/intensity
columns. Use `load_xrd_scans(files)` when an older plotting helper expects the
legacy `(Xs, Ys, length_list)` tuple.

```python
from xrd_utils.xrd_utils import load_xrd_scan, load_xrd_scans

scan = load_xrd_scan("sample.xy")
legacy_inputs = load_xrd_scans(["sample.xy", "reference.xrdml"])
```

## Workflow: Align And Compare Scans

Main entry points: `align_peak_to_value`, `align_fwhm_center_to_value`,
`align_peak_y_to_value`.
Helpers: `upsample_XY`, `plot_xrd`, `plot_xrd_files`, `plot_stacked_scans`.

Use x-alignment when scans have small instrument/sample offsets. Use y-alignment
when relative peak-height comparison matters. Plot with `plot_stacked_scans` for
DataFrame scans or `plot_xrd` for the legacy tuple API.

```python
from xrd_utils.xrd_utils import align_peak_to_value
from xrd_utils.xrd_viz import plot_stacked_scans, plot_xrd_files

Xs_aligned, Ys_aligned = align_peak_to_value(Xs, Ys, target_x_peak=46.5)
ax = plot_stacked_scans({"sample": scan}, normalize=True, offset=1.2)
fig, ax = plot_xrd_files(["sample.xrdml"], ["sample"])
```

## Workflow: Peak, FWHM, And Lattice Analysis

Main entry points: `detect_peaks`, `find_peaks_table`, `calculate_fwhm`,
`two_theta_to_d`, `lattice_from_peak`.

Use `detect_peaks` for quick peak positions, `find_peaks_table` for named peak
windows, and `calculate_fwhm` after selecting an expected peak center. Lattice
helpers require a two-theta value and an `hkl` tuple.

```python
from xrd_utils.xrd_utils import detect_peaks, calculate_fwhm, lattice_from_peak

px, py = detect_peaks(scan["angle"], scan["intensity"], num_peaks=5, prominence=0.05)
fwhm = calculate_fwhm(scan["angle"], scan["intensity"], px=px[0])
lattice = lattice_from_peak(px[0], hkl=(0, 0, 1))
```

## Workflow: Reciprocal-Space Maps

Main entry points: `RSMPlotter`, `plot_rsm`, `render_rsm_preview`.
Helper: `RSMPlotter.to_reciprocal_space`.

Use `render_rsm_preview` for compact GUI/notebook previews. Use `RSMPlotter`
directly when you need control over colormap, log limits, axes, or reciprocal vs
angle-space display. RSM support depends on `xrayutilities`.

```python
from xrd_utils.rsm_viz import render_rsm_preview, RSMPlotter, plot_rsm

source_name, figure = render_rsm_preview("map.xrdml")
plotter = RSMPlotter(plot_params={"cmap": "viridis", "levels": 60})
qx, qz, intensity = plot_rsm("map.xrdml")
```

## Function Map

This compact map is for lookup after you know the workflow you need.

### `xrd_utils.rsm_viz`
Functions: `render_rsm_preview(file_path, *, plot_params=None)`, `plot_rsm(file, *, ax=None, reciprocal_space=True, title=None, wavelength=1.5406)`
Classes: `RSMPlotter` (load_map, to_reciprocal_space, plot)

### `xrd_utils.skeleton`
Functions: `fib(n)`, `main(args=None)`

### `xrd_utils.xrd_utils`
Functions: `load_xrd_scan(path)`, `load_many_scans(files)`, `load_xrd_scans(files)`, `detect_peaks(x, y, num_peaks=2, prominence=0.1, distance=10)`, `calculate_fwhm(x, y, px, fit_type=None)`, `upsample_XY(x, y, num_points=5000)`, `align_peak_to_value(Xs, Ys, target_x_peak, viz=False)`, `align_fwhm_center_to_value(Xs, Ys, target_x_peak=0, viz=False)`, `align_peak_y_to_value(Xs, Ys, target_y_peak=None, use_global_max=True, viz=False)`, `process_input(inputs)`, `find_peaks_table(scan, windows=None, prominence=None)`, `two_theta_to_d(two_theta_deg, wavelength_angstrom=1.5406)`, `lattice_from_peak(two_theta_deg, hkl=(0, 0, 2), wavelength_angstrom=1.5406)`

### `xrd_utils.xrd_viz`
Functions: `plot_xrd(inputs, labels, title=None, xrange=None, yrange=None, diff=1000.0, fig=None, ax=None, yscale='log', legend_style='legend', colors=None, grid=False, text_offset_ratio=(1.0, 1.0))`, `plot_xrd_files(files, labels, *, ax=None, title=None, xrange=(0, 90), diff=1000.0, pad_sequence=None, save_file=None)`, `plot_stacked_scans(scans, ax=None, normalize=True, offset=1.2, xlim=None)`, `render_xrd_preview(file_path, *, label=None)`
