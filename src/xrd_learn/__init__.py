"""Backward-compatible wrapper for the legacy ``xrd_learn`` namespace."""

from importlib import import_module
import sys

from xrd_utils import *  # noqa: F401,F403
from xrd_utils import __version__

_MODULES = [
    "rsm_viz",
    "skeleton",
    "xrd_utils",
    "xrd_viz",
]

for _name in _MODULES:
    try:
        sys.modules[f"{__name__}.{_name}"] = import_module(f"xrd_utils.{_name}")
    except Exception:
        pass
