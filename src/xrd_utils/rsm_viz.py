from __future__ import annotations

from pathlib import Path
import pandas as pd
from typing import Any
import numpy as np

import xrayutilities as xu
import matplotlib.pyplot as plt
from matplotlib import colors, ticker
from matplotlib.patches import Rectangle
from sci_viz_utils.figures import layout_fig, set_axis_labels


class RSMPlotter:
    """Reciprocal-space map plotter for Panalytical XRDML maps.

    This follows the plotting convention used in the SrRuO3 structure notebook:
    Q is reported in reciprocal Angstrom using ``2*pi / wavelength``, intensity
    is shown on logarithmic contour levels, and multi-panel strips can share a
    dedicated colorbar axis.
    """

    DEFAULT_PARAMS = {
        "reciprocal_space": True,
        "title": None,
        "figsize": None,
        "cmap": plt.cm.viridis,
        "title_fontsize": 12,
        "label_fontsize": 10,
        "tick_fontsize": 8,
        "log_scale": True,
        "cbar_value_format": "actual",
        "cbar_levels": 20,
        "cbar_ticks": 10,
        "cbar_size": 8,
        "cbar_fraction": 0.05,
        "cbar_pad": 0.02,
        "show_xaxis": "last",
        "show_yaxis": "first",
        "vmin": 3,
        "vmax": 1000,
        "custom_bg_color": None,
        "save_path": None,
        "wavelength": 1.5406,
        "downsample_factor": 0.5,
        "rasterized": True,
    }

    def __init__(self, plot_params: dict | None = None):
        self.plot_params = {**self.DEFAULT_PARAMS, **(plot_params or {})}

    def load_map(self, file):
        """Load omega, two-theta, and intensity arrays from one XRDML RSM file."""

        curve_shape = np.asarray(xu.io.getxrdml_scan(file)[0]).shape
        omega, two_theta, intensity = xu.io.panalytical_xml.getxrdml_map(file)
        omega = np.asarray(omega, dtype=float).reshape(curve_shape)
        two_theta = np.asarray(two_theta, dtype=float).reshape(curve_shape)
        intensity = np.asarray(intensity, dtype=float).reshape(curve_shape)
        intensity[intensity <= 0] = np.nanmin(intensity[intensity > 0]) if np.any(intensity > 0) else 1
        return omega, two_theta, intensity

    def save_xrdml_to_csv(self, file, output_csv):
        """
        Save XRDML map data to a CSV file in long-table format.
        """
        omega, two_theta, intensity = self.load_map(file)
        df = pd.DataFrame({
            "omega_deg": omega.ravel(),
            "two_theta_deg": two_theta.ravel(),
            "intensity_counts": intensity.ravel(),
        })

        df.to_csv(output_csv, index=False)

        return df


    @staticmethod
    def to_reciprocal_space(omega, two_theta, wavelength=1.5406):
        """Convert omega/two-theta angles to Qx/Qz in Angstrom^-1."""

        k = 2 * np.pi / wavelength
        qz = k * (np.sin(np.deg2rad(two_theta - omega)) + np.sin(np.deg2rad(omega)))
        qx = k * (np.cos(np.deg2rad(omega)) - np.cos(np.deg2rad(two_theta - omega)))
        return qx, qz

    def plot(self, file, ax=None, figsize=None, cbar_ax=None, reciprocal_space=None, ignore_yaxis=False):
        """Plot one RSM and return ``(qx, qz, intensity)`` arrays.

        Parameters mirror the SRO notebook plotter. Pass an axis as ``cbar_ax``
        for a shared colorbar, ``"auto"`` to attach a colorbar to the panel, or
        ``False``/``None`` to suppress the colorbar.
        """

        if ax is None:
            fig, ax = plt.subplots(figsize=figsize or self.plot_params.get("figsize") or (5, 4))
        else:
            fig = ax.figure

        omega, two_theta, intensity = self.load_map(file)
        reciprocal_space = self.plot_params["reciprocal_space"] if reciprocal_space is None else reciprocal_space
        if reciprocal_space:
            qx, qz = self.to_reciprocal_space(
                omega,
                two_theta,
                wavelength=self.plot_params.get("wavelength", 1.5406),
            )
            contour = self._plot_reciprocal_space(ax, qx, qz, intensity)
        else:
            qx, qz = omega, two_theta
            contour = self._plot_direct_space(ax, omega, two_theta, intensity)

        if cbar_ax not in (None, False):
            self._add_colorbar(fig, ax, cbar_ax, contour)

        self._apply_plot_settings(ax, ignore_yaxis=ignore_yaxis, reciprocal_space=reciprocal_space)

        save_path = self.plot_params.get("save_path")
        if save_path:
            fig.savefig(f"{save_path}.svg", dpi=600)
            fig.savefig(f"{save_path}.png", dpi=600)

        return qx, qz, intensity

    def _downsample(self, *arrays):
        factor = self.plot_params.get("downsample_factor", 1)
        if factor in (None, 1, 1.0):
            return arrays
        try:
            from scipy.ndimage import zoom

            return tuple(zoom(array, factor) for array in arrays)
        except Exception:
            step = max(int(round(1 / float(factor))), 1)
            return tuple(array[::step, ::step] for array in arrays)

    def _plot_reciprocal_space(self, ax, qx, qz, intensity):
        qx, qz, intensity = self._downsample(qx, qz, intensity)
        log_scale = self.plot_params.get("log_scale", True)
        cmap = self.plot_params.get("cmap", plt.cm.viridis)
        vmin, vmax = self._get_intensity_limits(intensity)
        cbar_levels = self.plot_params.get("cbar_levels", self.plot_params.get("levels", 20))
        custom_bg_color = self.plot_params.get("custom_bg_color")

        if log_scale:
            intensity = self._adjust_intensity(intensity.copy(), vmin, vmax)
            levels = np.logspace(np.log10(vmin), np.log10(vmax), int(cbar_levels))
            cmap = self._create_custom_colormap(cmap, custom_bg_color)
            contour = ax.contourf(
                qx,
                qz,
                intensity,
                levels=levels,
                cmap=cmap,
                norm=colors.LogNorm(vmin=vmin, vmax=vmax),
                extend="neither",
            )
        else:
            contour = ax.contourf(qx, qz, intensity, levels=cbar_levels, cmap=cmap)

        if self.plot_params.get("rasterized", True):
            for collection in getattr(contour, "collections", []):
                collection.set_rasterized(True)
        self._blend_background_color(intensity, qx, qz, ax, contour, custom_bg_color)
        return contour

    def _plot_direct_space(self, ax, omega, two_theta, intensity):
        omega, two_theta, intensity = self._downsample(omega, two_theta, intensity)
        return ax.contourf(
            omega,
            two_theta,
            intensity,
            levels=self.plot_params.get("cbar_levels", self.plot_params.get("levels", 20)),
            cmap=self.plot_params.get("cmap", plt.cm.viridis),
        )

    def _get_intensity_limits(self, intensity):
        finite_positive = intensity[np.isfinite(intensity) & (intensity > 0)]
        if finite_positive.size == 0:
            return 1, 10
        vmin = self.plot_params.get("vmin", float(np.nanmin(finite_positive)))
        vmax = self.plot_params.get("vmax", float(np.nanmax(finite_positive)))
        return max(float(vmin), 1e-12), max(float(vmax), float(vmin) * 1.1)

    @staticmethod
    def _adjust_intensity(intensity, vmin, vmax):
        intensity[intensity <= vmin] = vmin - 1e-10
        intensity[intensity >= vmax] = vmax - 1e-10
        return intensity

    @staticmethod
    def _create_custom_colormap(cmap, custom_bg_color):
        if custom_bg_color:
            color_list = cmap(np.linspace(0, 1, 256))
            color_list[0] = colors.to_rgba(custom_bg_color)
            return colors.LinearSegmentedColormap.from_list("custom", color_list)
        return cmap

    @staticmethod
    def _blend_background_color(intensity, qx, qz, ax, contour, custom_bg_color):
        if custom_bg_color is None:
            values = intensity[np.isfinite(intensity)]
            if values.size == 0:
                return
            bg_value = np.bincount(values.astype(np.int32).ravel()).argmax()
            custom_bg_color = contour.cmap(contour.norm(bg_value))
        rect = Rectangle(
            (np.nanmin(qx), np.nanmin(qz)),
            np.nanmax(qx) - np.nanmin(qx),
            np.nanmax(qz) - np.nanmin(qz),
            facecolor=custom_bg_color,
            edgecolor="none",
            zorder=-1,
        )
        ax.add_patch(rect)

    def _add_colorbar(self, fig, ax, cbar_ax, contour):
        if cbar_ax == "auto":
            cbar = fig.colorbar(
                contour,
                ax=ax,
                orientation="vertical",
                fraction=self.plot_params.get("cbar_fraction", 0.05),
                pad=self.plot_params.get("cbar_pad", 0.02),
            )
        else:
            cbar = fig.colorbar(contour, cax=cbar_ax, orientation="vertical")

        tick_count = int(self.plot_params.get("cbar_ticks", 10))
        cbar_size = self.plot_params.get("cbar_size", self.plot_params.get("tick_fontsize", 8))
        vmin, vmax = contour.norm.vmin, contour.norm.vmax
        if isinstance(contour.norm, colors.LogNorm):
            cbar.set_ticks(np.logspace(np.log10(vmin), np.log10(vmax), num=tick_count))

        def format_func(value, _tick_number):
            if self.plot_params.get("cbar_value_format", "actual") == "log":
                return f"$10^{{{np.log10(value):.0f}}}$"
            return f"{value:.0f}"

        cbar.formatter = ticker.FuncFormatter(format_func)
        cbar.ax.tick_params(labelsize=cbar_size, direction="in")
        cbar.update_ticks()
        return cbar

    def _apply_plot_settings(self, ax, *, ignore_yaxis=False, reciprocal_space=True):
        if xlim := self.plot_params.get("xlim"):
            ax.set_xlim(*xlim)
        if ylim := self.plot_params.get("ylim"):
            ax.set_ylim(*ylim)

        ax.tick_params(axis="x", direction="in", top=True, labelsize=self.plot_params.get("tick_fontsize", 8))
        ax.tick_params(axis="y", direction="in", right=True, labelsize=self.plot_params.get("tick_fontsize", 8))

        if reciprocal_space:
            xlabel = r"$Q_x$ [$\AA^{-1}$]"
            ylabel = r"$Q_z$ [$\AA^{-1}$]"
        else:
            xlabel = r"$\omega$ [degree]"
            ylabel = r"$2	heta$ [degree]"

        set_axis_labels(
            ax,
            xlabel=xlabel,
            ylabel=ylabel,
            title=self.plot_params.get("title"),
            label_fontsize=self.plot_params.get("label_fontsize", 10),
            title_fontsize=self.plot_params.get("title_fontsize", 12),
            ticklabel_fontsize=self.plot_params.get("tick_fontsize", 8),
            yaxis_style=None,
            tick_padding=4,
        )
        ax.xaxis.label.set_fontweight("bold")
        ax.yaxis.label.set_fontweight("bold")

        if ignore_yaxis:
            ax.set_yticks([])
            ax.set_yticklabels([])
            ax.set_ylabel("")


def render_rsm_preview(file_path: str | Path, *, plot_params=None) -> tuple[str, Any]:
    """Render one reciprocal-space map with the compact preview style used by GUIs."""

    figure, axis = layout_fig(1, mod=1, figsize=(6, 5), layout=None)
    plotter = RSMPlotter(plot_params=plot_params)
    plotter.plot(file_path, ax=axis, cbar_ax="auto")
    figure.tight_layout()
    return "xrd_utils.rsm_viz.RSMPlotter.plot", figure


def plot_rsm(
    file,
    *,
    ax=None,
    reciprocal_space=True,
    title=None,
    wavelength=1.5406,
    plot_params=None,
    cbar_ax="auto",
):
    """Plot an XRD reciprocal-space map using the migrated convenience API."""

    params = {"title": title, "wavelength": wavelength, "reciprocal_space": reciprocal_space}
    if plot_params:
        params.update(plot_params)
    plotter = RSMPlotter(plot_params=params)
    return plotter.plot(file, ax=ax, cbar_ax=cbar_ax, reciprocal_space=reciprocal_space)
