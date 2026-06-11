from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from sci_viz_utils.figures import layout_fig, set_axis_labels

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
    legend_ncol: int | str = "auto",
    colors=None,
    grid=False,
    text_offset_ratio=(1.0, 1.0),
):
    """Plot one or more XRD scans from `(Xs, Ys, length_list)` input.

    Parameters
    ----------
    legend_ncol : int or ``"auto"``
        Number of legend columns.  ``"auto"`` (default) splits into 2–4
        columns when there are many labels, keeping the legend compact.
    """
    xs, ys, _lengths = process_input(inputs)
    if ax is None:
        fig, ax = layout_fig(1, mod=1, figsize=(6, 4))
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

    if yscale:
        ax.set_yscale(yscale)
    set_axis_labels(ax, xlabel="2theta or scan angle (deg)", ylabel="Intensity (a.u.)")
    if xrange:
        ax.set_xlim(*xrange)
    if yrange:
        ax.set_ylim(*yrange)
    if title:
        ax.set_title(title)
    if grid:
        ax.grid(True, alpha=0.25)
    if legend_style == "legend":
        ncol = legend_ncol
        if ncol == "auto":
            n_cols = len(labels)
            if n_cols <= 3:
                ncol = 1
            elif n_cols <= 6:
                ncol = 2
            elif n_cols <= 12:
                ncol = 3
            else:
                ncol = 4
        ax.legend(frameon=False, fontsize=8, ncol=ncol)
    return fig, ax


def plot_xrd_files(
    files,
    labels,
    *,
    ax=None,
    title=None,
    xrange=(0, 90),
    yrange=None,
    diff=1e3,
    pad_sequence=None,
    save_file=None,
):
    """Plot one or more XRD files using the migrated PlumeDynamics convenience API.

    Parameters mirror the old ``plume_dynamics.materials.xrd.plot_xrd`` helper,
    while internally using the XRD-utils loading and plotting stack.
    """

    inputs = load_xrd_scans(files)
    xs, ys, lengths = inputs
    if pad_sequence:
        ys = [
            np.pad(y, pad_sequence[index], mode="median")
            for index, y in enumerate(ys)
        ]
        inputs = (xs, ys, lengths)

    fig = ax.figure if ax is not None else None
    fig, ax = plot_xrd(
        inputs,
        labels,
        title=title,
        xrange=xrange,
        yrange=yrange,
        diff=diff,
        fig=fig,
        ax=ax,
    )
    if save_file:
        fig.savefig(save_file, dpi=300, bbox_inches="tight")
    return fig, ax


def render_xrd_preview(file_path: str | Path, *, label: str | None = None) -> tuple[str, Any]:
    """Render one XRD scan with the compact preview style used by GUIs."""
    figure, axis = layout_fig(1, mod=1, figsize=(6, 4))
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

