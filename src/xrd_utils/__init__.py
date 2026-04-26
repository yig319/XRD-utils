"""Utilities for XRD scan loading, peak analysis, and visualization."""

import sys
from importlib import import_module

try:
    from importlib.metadata import PackageNotFoundError, version
except Exception:  # pragma: no cover
    from importlib_metadata import PackageNotFoundError, version

try:
    __version__ = version("XRD-utils")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"

from xrd_utils.xrd_utils import *  # noqa: F401,F403,E402
from xrd_utils.xrd_viz import *  # noqa: F401,F403,E402

try:
    from xrd_utils.rsm_viz import *  # noqa: F401,F403,E402
except Exception:
    pass

for _name in ["rsm_viz", "skeleton", "xrd_utils", "xrd_viz"]:
    try:
        sys.modules[f"xrd_learn.{_name}"] = import_module(f"xrd_utils.{_name}")
    except Exception:
        pass

