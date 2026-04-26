from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _floats(text: str | None) -> list[float]:
    if not text:
        return []
    return [float(x) for x in re.findall(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", text)]


def _load_xrdml_fallback(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    root = ET.parse(path).getroot()

    counts = None
    for element in root.iter():
        if _local_name(element.tag) in {"counts", "intensities"}:
            values = _floats(element.text)
            if values:
                counts = np.asarray(values, dtype=float)
                break
    if counts is None:
        raise ValueError(f"No counts or intensities found in {path}")

    positions: dict[str, tuple[float | None, float | None, float | None]] = {}
    for element in root.iter():
        if _local_name(element.tag) != "positions":
            continue
        axis = element.attrib.get("axis", "angle")
        start = end = common = None
        for child in element:
            name = _local_name(child.tag)
            values = _floats(child.text)
            if not values:
                continue
            if name == "startPosition":
                start = values[0]
            elif name == "endPosition":
                end = values[0]
            elif name == "commonPosition":
                common = values[0]
        positions[axis] = (start, end, common)

    scan_axis = None
    for element in root.iter():
        if _local_name(element.tag) == "scan":
            scan_axis = element.attrib.get("scanAxis")
            break

    preferred_axes: list[str] = []
    if scan_axis:
        preferred_axes.extend(part.strip() for part in re.split(r"[-,\s]+", scan_axis) if part.strip())
    preferred_axes.extend(["2Theta", "Omega"])

    axis_name = None
    for axis in preferred_axes:
        if axis in positions and positions[axis][0] is not None and positions[axis][1] is not None:
            axis_name = axis
            break
    if axis_name is None:
        for axis, (start, end, _common) in positions.items():
            if start is not None and end is not None:
                axis_name = axis
                break

    if axis_name is None:
        axis_name = "index"
        x = np.arange(len(counts), dtype=float)
    else:
        start, end, _common = positions[axis_name]
        x = np.linspace(float(start), float(end), len(counts))

    return pd.DataFrame({"angle": x, "intensity": counts, "axis": axis_name, "source": str(path)})


def load_xrd_scan(path: str | Path) -> pd.DataFrame:
    """Load a 1D XRD scan from XRDML, CSV, TXT, or XY."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".xrdml":
        try:
            import xrayutilities as xu

            out = xu.io.getxrdml_scan(str(path))
            return pd.DataFrame(
                {
                    "angle": np.asarray(out[0], dtype=float).ravel(),
                    "intensity": np.asarray(out[1], dtype=float).ravel(),
                    "axis": "2Theta",
                    "source": str(path),
                }
            )
        except Exception:
            return _load_xrdml_fallback(path)

    df = pd.read_csv(path, comment="#", sep=None, engine="python", header=None)
    numeric = df.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all").dropna()
    if numeric.shape[1] < 2:
        raise ValueError(f"Expected at least two numeric columns in {path}")
    return pd.DataFrame(
        {
            "angle": numeric.iloc[:, 0].to_numpy(float),
            "intensity": numeric.iloc[:, 1].to_numpy(float),
            "axis": "angle",
            "source": str(path),
        }
    )


def load_many_scans(files: list[str | Path]) -> dict[str, pd.DataFrame]:
    return {Path(path).stem: load_xrd_scan(path) for path in files}


def load_xrd_scans(files: list[str | Path]):
    """Load files into the tuple API used by the original notebooks."""
    xs, ys, lengths = [], [], []
    for path in files:
        scan = load_xrd_scan(path)
        x = scan["angle"].to_numpy(float)
        y = scan["intensity"].to_numpy(float)
        xs.append(x)
        ys.append(y)
        lengths.append(len(x))
    return xs, ys, lengths


def detect_peaks(x, y, num_peaks: int = 2, prominence: float = 0.1, distance: int = 10):
    """Return peak x/y values sorted by x position."""
    from scipy.signal import find_peaks

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    y_work = y - np.nanmin(y)
    peaks, _ = find_peaks(y_work, prominence=prominence, distance=distance)
    if len(peaks) == 0:
        peaks = np.array([int(np.nanargmax(y_work))])
    if len(peaks) > num_peaks:
        order = np.argsort(y_work[peaks])[-num_peaks:]
        peaks = peaks[order]
    peaks = peaks[np.argsort(x[peaks])]
    return x[peaks], y[peaks]


def calculate_fwhm(x, y, px: float, fit_type: str | None = None):
    """Calculate FWHM around the peak nearest `px`."""
    from scipy.signal import peak_widths

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    peak_index = int(np.argmin(np.abs(x - px)))
    widths, height, left_ips, right_ips = peak_widths(y - np.nanmin(y), [peak_index], rel_height=0.5)
    dx = float(np.nanmedian(np.diff(x))) if len(x) > 1 else 1.0
    left_x = float(np.interp(left_ips[0], np.arange(len(x)), x))
    right_x = float(np.interp(right_ips[0], np.arange(len(x)), x))
    fwhm = float(widths[0] * abs(dx))
    amplitude = float(y[peak_index])
    return fwhm, amplitude, left_x, right_x


def upsample_XY(x, y, num_points: int = 5000):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    x_new = np.linspace(np.nanmin(x), np.nanmax(x), num_points)
    y_new = np.interp(x_new, x, y)
    return x_new, y_new


def align_peak_to_value(Xs, Ys, target_x_peak: float, viz: bool = False):
    out_xs, out_ys = [], []
    for x, y in zip(Xs, Ys):
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        peak_x = x[int(np.nanargmax(y))]
        out_xs.append(x + (target_x_peak - peak_x))
        out_ys.append(y)
    return out_xs, out_ys


def align_fwhm_center_to_value(Xs, Ys, target_x_peak: float = 0, viz: bool = False):
    out_xs, out_ys, fwhm_list = [], [], []
    for x, y in zip(Xs, Ys):
        peak_x = np.asarray(x)[int(np.nanargmax(y))]
        fwhm, _amp, left, right = calculate_fwhm(x, y, peak_x)
        center = (left + right) / 2
        out_xs.append(np.asarray(x) + (target_x_peak - center))
        out_ys.append(np.asarray(y))
        fwhm_list.append(fwhm)
    return out_xs, out_ys, fwhm_list


def align_peak_y_to_value(Xs, Ys, target_y_peak: float | None = None, use_global_max: bool = True, viz: bool = False):
    if target_y_peak is None:
        target_y_peak = max(float(np.nanmax(y)) for y in Ys) if use_global_max else 1.0
    out_ys = []
    for y in Ys:
        y = np.asarray(y, dtype=float)
        peak_y = float(np.nanmax(y))
        out_ys.append(y if peak_y == 0 else y * (target_y_peak / peak_y))
    return Xs, out_ys


def process_input(inputs):
    """Validate tuple input `(Xs, Ys, length_list)` for plotting."""
    if not isinstance(inputs, tuple) or len(inputs) != 3:
        raise ValueError("inputs must be a tuple: (Xs, Ys, length_list)")
    xs, ys, lengths = inputs
    if not isinstance(xs, list) or not isinstance(ys, list) or not isinstance(lengths, list):
        raise ValueError("Xs, Ys, and length_list must all be lists")
    return xs, ys, lengths


def find_peaks_table(
    scan: pd.DataFrame,
    windows: dict[str, tuple[float, float]] | None = None,
    prominence: float | None = None,
) -> pd.DataFrame:
    x = scan["angle"].to_numpy(float)
    y = scan["intensity"].to_numpy(float)
    windows = {"full_scan": (float(np.nanmin(x)), float(np.nanmax(x)))} if windows is None else windows
    rows = []
    for label, (lo, hi) in windows.items():
        mask = (x >= lo) & (x <= hi) & np.isfinite(y)
        if not mask.any():
            continue
        peak_x, peak_y = detect_peaks(x[mask], y[mask], num_peaks=1, prominence=prominence or 0.1)
        fwhm, *_ = calculate_fwhm(x[mask], y[mask], peak_x[0])
        rows.append(
            {
                "window": label,
                "two_theta_deg": float(peak_x[0]),
                "intensity": float(peak_y[0]),
                "fwhm_deg": fwhm,
                "source": scan["source"].iloc[0],
            }
        )
    return pd.DataFrame(rows)


def two_theta_to_d(two_theta_deg: float, wavelength_angstrom: float = 1.5406) -> float:
    theta = math.radians(two_theta_deg / 2)
    return wavelength_angstrom / (2 * math.sin(theta))


def lattice_from_peak(two_theta_deg: float, hkl=(0, 0, 2), wavelength_angstrom: float = 1.5406) -> float:
    d = two_theta_to_d(two_theta_deg, wavelength_angstrom=wavelength_angstrom)
    h, k, l = hkl
    if h == 0 and k == 0 and l != 0:
        return d * abs(l)
    return d * math.sqrt(h * h + k * k + l * l)

