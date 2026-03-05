#!/usr/bin/env python3
"""Runnable synthetic demo for XRD-tools.

This script generates three synthetic XRD scans, analyzes peaks/FWHM, aligns
the scans, and saves a side-by-side visualization.
"""

from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def _ensure_xrayutilities_stub():
    """Provide a minimal xrayutilities stub for synthetic-only demo usage."""
    try:
        import xrayutilities  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    fake_xu = types.ModuleType("xrayutilities")
    fake_xu.io = types.SimpleNamespace()

    def _not_available(*_args, **_kwargs):
        raise RuntimeError(
            "xrayutilities is not installed. Install requirements to read real XRD files."
        )

    fake_xu.io.getxrdml_scan = _not_available
    fake_xu.io.panalytical_xml = types.SimpleNamespace(getxrdml_map=_not_available)
    sys.modules["xrayutilities"] = fake_xu


_ensure_xrayutilities_stub()

try:
    from xrd_learn.xrd_utils import (
        align_peak_to_value,
        align_peak_y_to_value,
        calculate_fwhm,
        detect_peaks,
    )
    from xrd_learn.xrd_viz import plot_xrd
except ModuleNotFoundError:
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from xrd_learn.xrd_utils import (  # type: ignore
        align_peak_to_value,
        align_peak_y_to_value,
        calculate_fwhm,
        detect_peaks,
    )
    from xrd_learn.xrd_viz import plot_xrd  # type: ignore


def build_demo_scans(seed: int = 2026):
    """Build synthetic scans with slight peak shifts and noise."""
    rng = np.random.default_rng(seed)
    x = np.linspace(42.0, 48.0, 800)
    labels = ["sample A", "sample B", "sample C"]
    shifts = (-0.12, 0.0, 0.16)
    widths = (0.030, 0.028, 0.032)
    amps = (1.0, 0.9, 1.1)

    scans = []
    for shift, width, amp in zip(shifts, widths, amps):
        y = amp * np.exp(-((x - (45.0 + shift)) ** 2) / width)
        y += 0.12 + 0.02 * rng.random(x.size)
        scans.append(y)
    return x, scans, labels


def main():
    parser = argparse.ArgumentParser(description="Run XRD-tools synthetic demo.")
    parser.add_argument(
        "--output",
        default="examples/output/demo_xrd_scan.png",
        help="Path to save the demo figure.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the figure window in addition to saving.",
    )
    args = parser.parse_args()

    x, scans, labels = build_demo_scans()

    print("Peak summary:")
    for label, y in zip(labels, scans):
        peak_x, peak_y = detect_peaks(x, y, num_peaks=1, prominence=0.2)
        fwhm, *_ = calculate_fwhm(x, y, peak_x[0], fit_type="gaussian")
        print(f"  {label}: peak={peak_x[0]:.4f}, intensity={peak_y[0]:.4f}, fwhm={fwhm:.4f}")

    raw_xs = [x.copy() for _ in scans]
    raw_ys = [y.copy() for y in scans]

    aligned_xs = [x.copy() for _ in scans]
    aligned_ys = [y.copy() for y in scans]
    aligned_xs, aligned_ys = align_peak_to_value(aligned_xs, aligned_ys, target_x_peak=45.0)
    aligned_xs, aligned_ys = align_peak_y_to_value(
        aligned_xs, aligned_ys, use_global_max=True
    )

    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    plot_xrd(
        inputs=(raw_xs, raw_ys, [len(x)] * len(raw_ys)),
        labels=labels,
        title="Raw synthetic scans",
        yscale="linear",
        diff=None,
        fig=fig,
        ax=axes[0],
        legend_style="legend",
        grid=True,
    )
    plot_xrd(
        inputs=(aligned_xs, aligned_ys, [len(x)] * len(aligned_ys)),
        labels=labels,
        title="Aligned scans (x and y peak normalized)",
        yscale="linear",
        diff=None,
        fig=fig,
        ax=axes[1],
        legend_style="legend",
        grid=True,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    print(f"\nSaved demo figure to: {output_path}")

    if args.show:
        plt.show()
    else:
        plt.close(fig)


if __name__ == "__main__":
    main()
