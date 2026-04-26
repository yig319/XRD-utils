from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from sci_viz_utils.figures import set_axis_labels

from xrd_utils.xrd_utils import load_xrd_scans, process_input


def plot_xrd(
    inputs,
    labels,
    title=None,
    xrange=None,
    yrange=None,
    diff=1e3,
    fig=None,
    ax=None,
    yscale="log",
    legend_style="legend",
    colors=None,
    grid=False,
    text_offset_ratio=(1.0, 1.0),
):
    """Plot one or more XRD scans from `(Xs, Ys, length_list)` input."""
    xs, ys, _lengths = process_input(inputs)
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 4))
    if colors is None:
        colors = [None] * len(ys)

    for i, (x, y, label, color) in enumerate(zip(xs, ys, labels, colors)):
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float).copy()
        y[y <= 0] = np.nanmin(y[y > 0]) if np.any(y > 0) else 1
        scale = diff ** (len(ys) - i - 1) if diff else 1
        ax.plot(x, y * scale, label=label, color=color, linewidth=1.2)
        if legend_style == "label":
            text_x = x[-1] if text_offset_ratio[0] == 1.0 else x[int(len(x) * min(text_offset_ratio[0], 0.999))]
            text_y = np.nanmax(y * scale) * text_offset_ratio[1]
            ax.text(text_x, text_y, label, fontsize=8, ha="right")

    set_axis_labels(ax, xlabel="2theta or scan angle (deg)", ylabel="Intensity (a.u.)")
    if yscale:
        ax.set_yscale(yscale)
    if xrange:
        ax.set_xlim(*xrange)
    if yrange:
        ax.set_ylim(*yrange)
    if title:
        ax.set_title(title)
    if grid:
        ax.grid(True, alpha=0.25)
    if legend_style == "legend":
        ax.legend(frameon=False, fontsize=8)
    return fig, ax


def plot_stacked_scans(scans, ax=None, normalize: bool = True, offset: float = 1.2, xlim=None):
    if ax is None:
        _, ax = plt.subplots(figsize=(6, 4))
    for i, (name, df) in enumerate(scans.items()):
        x = df["angle"].to_numpy(float)
        y = df["intensity"].to_numpy(float)
        y = np.where(y <= 0, np.nan, y)
        if normalize and np.nanmax(y) > 0:
            y = y / np.nanmax(y)
        ax.semilogy(x, y * (offset**i), label=name, linewidth=1.2)
    set_axis_labels(ax, xlabel="2theta or scan angle (deg)", ylabel="Intensity (a.u.)")
    if xlim:
        ax.set_xlim(*xlim)
    if scans:
        ax.legend(frameon=False, fontsize=8)
    return ax


def render_xrd_preview(file_path: str | Path, *, label: str | None = None) -> tuple[str, Any]:
    """Render one XRD scan with the compact preview style used by GUIs."""
    figure, axis = plt.subplots(figsize=(6, 4))
    plot_xrd(
        load_xrd_scans([file_path]),
        [label or Path(file_path).name],
        fig=figure,
        ax=axis,
        diff=None,
        yscale="log",
    )
    figure.tight_layout()
    return "xrd_utils.xrd_viz.plot_xrd", figure
