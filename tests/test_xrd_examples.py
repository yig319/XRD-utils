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
    """Load local source modules with a stubbed ``xrayutilities`` backend."""
    src_dir = Path(__file__).resolve().parents[1] / "src" / "xrd_learn"

    pkg = types.ModuleType("xrd_learn")
    pkg.__path__ = [str(src_dir)]
    sys.modules["xrd_learn"] = pkg

    fake_xu = types.ModuleType("xrayutilities")
    fake_xu.io = types.SimpleNamespace()
    fake_xu.io.panalytical_xml = types.SimpleNamespace()

    rng = np.random.default_rng(2026)

    def _scan(file):
        if "map" in str(file):
            n = 32
            tth = np.linspace(44.0, 46.0, n)
            tth_grid = np.tile(tth, (n, 1))
            base = np.exp(-((tth_grid - 45.0) ** 2) / 0.015)
            noise = 0.02 * rng.standard_normal(size=(n, n))
            intensity = np.clip(base + noise + 0.05, 1e-4, None)
            return tth_grid, intensity

        x = np.linspace(42.0, 48.0, 600)
        y = (
            0.75 * np.exp(-((x - 44.7) ** 2) / 0.02)
            + 1.00 * np.exp(-((x - 45.6) ** 2) / 0.03)
            + 0.03 * rng.random(size=x.size)
            + 0.2
        )
        return x, y

    def _map(file):
        n = 32
        omega = np.linspace(20.0, 30.0, n)
        two_theta = np.linspace(40.0, 50.0, n)
        om_grid, tt_grid = np.meshgrid(omega, two_theta, indexing="ij")

        peak = np.exp(-(((om_grid - 25.0) ** 2) / 1.2 + ((tt_grid - 45.0) ** 2) / 1.5))
        noise = 4.0 * rng.random(size=peak.shape)
        intensity = np.clip(1200.0 * peak + noise + 3.0, 1e-3, None)
        return om_grid.ravel(), tt_grid.ravel(), intensity.ravel()

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


def test_detect_peaks_random_demo(xrd_modules):
    xrd_utils, _, _ = xrd_modules
    x = np.linspace(40.0, 50.0, 1200)
    rng = np.random.default_rng(7)
    y = (
        np.exp(-((x - 43.2) ** 2) / 0.02)
        + 0.8 * np.exp(-((x - 45.5) ** 2) / 0.03)
        + 0.02 * rng.random(size=x.size)
        + 0.2
    )
    peak_x, peak_y = xrd_utils.detect_peaks(x, y, num_peaks=2, prominence=0.2)
    assert len(peak_x) == 2
    assert len(peak_y) == 2
    assert np.all(np.isfinite(peak_x))


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


def test_plot_xrd_random_demo_visualization(xrd_modules, no_show, tmp_path):
    _, xrd_viz, _ = xrd_modules
    x = np.linspace(44.0, 46.0, 300)
    rng = np.random.default_rng(123)

    y_a = np.exp(-((x - 44.8) ** 2) / 0.02) + 0.02 * rng.random(x.size) + 0.2
    y_b = np.exp(-((x - 45.0) ** 2) / 0.02) + 0.02 * rng.random(x.size) + 0.2
    y_c = np.exp(-((x - 45.2) ** 2) / 0.02) + 0.02 * rng.random(x.size) + 0.2

    fig, ax = plt.subplots(figsize=(6, 3))
    xrd_viz.plot_xrd(
        inputs=([x, x, x], [y_a, y_b, y_c], [len(x), len(x), len(x)]),
        labels=["sample A", "sample B", "sample C"],
        yscale="linear",
        diff=None,
        fig=fig,
        ax=ax,
        legend_style="legend",
        grid=True,
    )

    output = tmp_path / "xrd_demo_plot.png"
    fig.savefig(output, dpi=100)

    assert len(ax.lines) == 3
    assert output.exists()
    assert output.stat().st_size > 0


def test_rsm_plotter_random_demo_visualization(xrd_modules, no_show, tmp_path):
    _, _, rsm_viz = xrd_modules
    plotter = rsm_viz.RSMPlotter(
        plot_params={"title": "RSM Example", "vmin": 3, "vmax": 1500, "cbar_ticks": 6}
    )

    fig, (ax, cax) = plt.subplots(1, 2, figsize=(8, 3), gridspec_kw={"width_ratios": [10, 1]})
    qx, qz, intensity = plotter.plot(file="synthetic_map", ax=ax, cbar_ax=cax)

    output = tmp_path / "rsm_demo_plot.png"
    fig.savefig(output, dpi=100)

    assert qx.shape == qz.shape == intensity.shape
    assert qx.ndim == 2
    assert np.isfinite(intensity).all()
    assert len(ax.collections) > 0
    assert output.exists()
    assert output.stat().st_size > 0
