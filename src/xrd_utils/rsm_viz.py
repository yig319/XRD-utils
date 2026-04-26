from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors, ticker


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
            _, ax = plt.subplots(figsize=(5, 4))
        omega, two_theta, intensity = self.load_map(file)
        if reciprocal_space:
            qx, qz = self.to_reciprocal_space(
                omega,
                two_theta,
                wavelength=self.plot_params.get("wavelength", 1.5406),
            )
            x, z = qx, qz
            ax.set_xlabel("Qx (1/A)")
            ax.set_ylabel("Qz (1/A)")
        else:
            x, z = omega, two_theta
            qx, qz = x, z
            ax.set_xlabel("Omega (deg)")
            ax.set_ylabel("2theta (deg)")

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
        if self.plot_params.get("title"):
            ax.set_title(self.plot_params["title"])
        if cbar_ax is not False:
            ax.figure.colorbar(contour, ax=ax, cax=cbar_ax)
        return qx, qz, intensity


def render_rsm_preview(file_path: str | Path, *, plot_params=None) -> tuple[str, Any]:
    """Render one reciprocal-space map with the compact preview style used by GUIs."""
    figure, axis = plt.subplots(figsize=(6, 5))
    plotter = RSMPlotter(plot_params=plot_params)
    plotter.plot(file_path, ax=axis)
    figure.tight_layout()
    return "xrd_utils.rsm_viz.RSMPlotter.plot", figure
