from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors, ticker
from sci_viz_utils.figures import layout_fig, set_axis_labels


class RSMPlotter:
    """Small reciprocal-space map plotter for Panalytical XRDML maps."""

    def __init__(self, plot_params=None):
        self.plot_params = plot_params or {}

    def load_map(self, file):
        import xrayutilities as xu

        curve_shape = np.asarray(xu.io.getxrdml_scan(file)[0]).shape
        omega, two_theta, intensity = xu.io.panalytical_xml.getxrdml_map(file)
        omega = np.asarray(omega).reshape(curve_shape)
        two_theta = np.asarray(two_theta).reshape(curve_shape)
        intensity = np.asarray(intensity).reshape(curve_shape)
        intensity[intensity <= 0] = np.nanmin(intensity[intensity > 0]) if np.any(intensity > 0) else 1
        return omega, two_theta, intensity

    @staticmethod
    def to_reciprocal_space(omega, two_theta, wavelength=1.5406):
        qz = (1 / wavelength) * (
            np.sin(np.deg2rad(two_theta - omega)) + np.sin(np.deg2rad(omega))
        )
        qx = (1 / wavelength) * (
            np.cos(np.deg2rad(omega)) - np.cos(np.deg2rad(two_theta - omega))
        )
        return qx, qz

    def plot(self, file, ax=None, cbar_ax=None, reciprocal_space=True):
        if ax is None:
            _, ax = layout_fig(1, mod=1, figsize=(5, 4), layout=None)
        omega, two_theta, intensity = self.load_map(file)
        if reciprocal_space:
            qx, qz = self.to_reciprocal_space(
                omega,
                two_theta,
                wavelength=self.plot_params.get("wavelength", 1.5406),
            )
            x, z = qx, qz
            xlabel = "Qx (1/A)"
            ylabel = "Qz (1/A)"
        else:
            x, z = omega, two_theta
            qx, qz = x, z
            xlabel = "Omega (deg)"
            ylabel = "2theta (deg)"

        vmin = self.plot_params.get("vmin", np.nanpercentile(intensity, 1))
        vmax = self.plot_params.get("vmax", np.nanpercentile(intensity, 99.5))
        contour = ax.contourf(
            x,
            z,
            intensity,
            levels=self.plot_params.get("levels", 50),
            locator=ticker.LogLocator(),
            cmap=self.plot_params.get("cmap", "viridis"),
            norm=colors.LogNorm(vmin=max(vmin, 1e-12), vmax=max(vmax, vmin * 1.1)),
        )
        if self.plot_params.get("xlim"):
            ax.set_xlim(*self.plot_params["xlim"])
        if self.plot_params.get("ylim"):
            ax.set_ylim(*self.plot_params["ylim"])
        set_axis_labels(
            ax,
            xlabel=xlabel,
            ylabel=ylabel,
            title=self.plot_params.get("title"),
            yaxis_style=None,
        )
        if cbar_ax is not False:
            ax.figure.colorbar(contour, ax=ax, cax=cbar_ax)
        return qx, qz, intensity


def render_rsm_preview(file_path: str | Path, *, plot_params=None) -> tuple[str, Any]:
    """Render one reciprocal-space map with the compact preview style used by GUIs."""
    figure, axis = layout_fig(1, mod=1, figsize=(6, 5), layout=None)
    plotter = RSMPlotter(plot_params=plot_params)
    plotter.plot(file_path, ax=axis)
    figure.tight_layout()
    return "xrd_utils.rsm_viz.RSMPlotter.plot", figure


def plot_rsm(file, *, ax=None, reciprocal_space=True, title=None, wavelength=1.5406):
    """Plot an XRD reciprocal-space map using the migrated PlumeDynamics API."""

    plotter = RSMPlotter(plot_params={"title": title, "wavelength": wavelength})
    qx, qz, intensity = plotter.plot(
        file,
        ax=ax,
        reciprocal_space=reciprocal_space,
    )
    return qx, qz, intensity
