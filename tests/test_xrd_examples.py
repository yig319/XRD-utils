from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
import types

import matplotlib.pyplot as plt
import numpy as np
import pytest


def _load_module(name, path):
    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[name] = module
    return module


@pytest.fixture(scope="module")
def xrd_modules():
    src_dir = Path(__file__).resolve().parents[1] / "src" / "xrd_learn"

    pkg = types.ModuleType("xrd_learn")
    pkg.__path__ = [str(src_dir)]
    sys.modules["xrd_learn"] = pkg

    # Stub xrayutilities so tests run without real instrument files.
    fake_xu = types.ModuleType("xrayutilities")
    fake_xu.io = types.SimpleNamespace()
    fake_xu.io.panalytical_xml = types.SimpleNamespace()

    def _scan(file):
        if "map" in str(file):
            grid = np.linspace(44.0, 46.0, 20 * 20).reshape(20, 20)
            intensity = np.exp(-((grid - 45.0) ** 2) / 0.01)
            return grid, intensity
        x = np.linspace(44.0, 46.0, 300)
        y = np.exp(-((x - 45.0) ** 2) / 0.01) + 0.1
        return x, y

    def _map(file):
        omega_grid = np.linspace(20.0, 30.0, 20 * 20)
        two_theta_grid = np.linspace(40.0, 50.0, 20 * 20)
        center = 10.0
        intensity = np.exp(
            -(
                ((omega_grid - 25.0) ** 2) / center
                + ((two_theta_grid - 45.0) ** 2) / center
            )
        ) * 100
        return omega_grid, two_theta_grid, intensity

    fake_xu.io.getxrdml_scan = _scan
    fake_xu.io.panalytical_xml.getxrdml_map = _map
    sys.modules["xrayutilities"] = fake_xu

    xrd_utils = _load_module("xrd_learn.xrd_utils", src_dir / "xrd_utils.py")
    xrd_viz = _load_module("xrd_learn.xrd_viz", src_dir / "xrd_viz.py")
    rsm_viz = _load_module("xrd_learn.rsm_viz", src_dir / "rsm_viz.py")
    yield xrd_utils, xrd_viz, rsm_viz

    for name in [
        "xrd_learn.rsm_viz",
        "xrd_learn.xrd_viz",
        "xrd_learn.xrd_utils",
        "xrd_learn",
        "xrayutilities",
    ]:
        sys.modules.pop(name, None)


def test_detect_peaks_example(xrd_modules):
    xrd_utils, _, _ = xrd_modules
    x = np.linspace(40.0, 50.0, 1000)
    y = (
        np.exp(-((x - 43.0) ** 2) / 0.02)
        + 0.6 * np.exp(-((x - 45.5) ** 2) / 0.03)
        + 0.3
    )
    peak_x, peak_y = xrd_utils.detect_peaks(x, y, num_peaks=2, prominence=0.1)
    assert len(peak_x) == 2
    assert max(peak_y) > 0.9


def test_calculate_fwhm_example(xrd_modules):
    xrd_utils, _, _ = xrd_modules
    x = np.linspace(44.0, 46.0, 300)
    y = np.exp(-((x - 45.0) ** 2) / 0.01)
    fwhm, amp, left, right = xrd_utils.calculate_fwhm(x, y, px=45.0, fit_type="gaussian")
    assert fwhm > 0
    assert amp > 0
    assert left < 45.0 < right


def test_alignment_helpers_example(xrd_modules):
    xrd_utils, _, _ = xrd_modules
    x = np.linspace(44.0, 46.0, 300)
    y1 = np.exp(-((x - 44.8) ** 2) / 0.01)
    y2 = np.exp(-((x - 45.2) ** 2) / 0.01)

    Xs, Ys = [x.copy(), x.copy()], [y1.copy(), y2.copy()]
    Xs_shifted, Ys_shifted = xrd_utils.align_peak_to_value(Xs, Ys, target_x_peak=45.0)
    assert np.isclose(Xs_shifted[0][np.argmax(Ys_shifted[0])], 45.0, atol=1e-3)
    assert np.isclose(Xs_shifted[1][np.argmax(Ys_shifted[1])], 45.0, atol=1e-3)

    _, Ys_scaled = xrd_utils.align_peak_y_to_value(Xs_shifted, Ys_shifted, use_global_max=True)
    assert np.isclose(np.max(Ys_scaled[0]), np.max(Ys_scaled[1]), rtol=1e-6)


def test_process_input_tuple_validation(xrd_modules):
    xrd_utils, _, _ = xrd_modules
    x = np.linspace(44.0, 46.0, 100)
    y = np.ones_like(x)
    result = xrd_utils.process_input(([x], [y], [len(x)]))
    assert len(result) == 3
    with pytest.raises(ValueError):
        xrd_utils.process_input(([x], "not-a-list", [len(x)]))


def test_plot_xrd_example_runs(xrd_modules, no_show):
    _, xrd_viz, _ = xrd_modules
    x = np.linspace(44.0, 46.0, 200)
    y1 = np.exp(-((x - 44.9) ** 2) / 0.015) + 0.2
    y2 = np.exp(-((x - 45.1) ** 2) / 0.015) + 0.2

    fig, ax = plt.subplots(figsize=(6, 3))
    xrd_viz.plot_xrd(
        inputs=([x, x], [y1, y2], [len(x), len(x)]),
        labels=["sample A", "sample B"],
        yscale="linear",
        diff=None,
        fig=fig,
        ax=ax,
        legend_style="legend",
    )
    assert len(ax.lines) == 2


def test_rsm_plotter_example_runs(xrd_modules, no_show):
    _, _, rsm_viz = xrd_modules
    plotter = rsm_viz.RSMPlotter(plot_params={"title": "RSM Example"})
    fig, (ax, cax) = plt.subplots(1, 2, figsize=(8, 3), gridspec_kw={"width_ratios": [10, 1]})
    qx, qz, intensity = plotter.plot(file="synthetic_map", ax=ax, cbar_ax=cax)
    assert qx.shape == qz.shape == intensity.shape
    assert qx.ndim == 2
