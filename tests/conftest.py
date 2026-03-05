"""Shared pytest fixtures for XRD-tools."""

import sys
from pathlib import Path

import matplotlib
import pytest

# Use a non-interactive backend so tests run in headless CI.
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture(autouse=True)
def _close_figures():
    """Ensure figures do not leak between tests."""
    yield
    plt.close("all")


@pytest.fixture
def no_show(monkeypatch):
    """Disable ``plt.show()`` popups during tests."""
    monkeypatch.setattr(plt, "show", lambda *args, **kwargs: None)
