=========
XRD-tools
=========

XRD-tools is a Python package for loading, aligning, analyzing, and visualizing
X-ray diffraction (XRD) data, including line scans and reciprocal space maps.

Project Links
=============

- Source: https://github.com/yig319/XRD-tools
- Issues: https://github.com/yig319/XRD-tools/issues
- PyPI: https://pypi.org/project/XRD-tools/

Installation
============

Install from PyPI:

.. code-block:: bash

   pip install XRD-tools

Install from source:

.. code-block:: bash

   git clone https://github.com/yig319/XRD-tools.git
   cd XRD-tools
   pip install -e .

Quick Start
===========

.. code-block:: python

   import numpy as np
   from xrd_learn.xrd_utils import detect_peaks, calculate_fwhm

   # Example synthetic profile
   x = np.linspace(40, 50, 500)
   y = np.exp(-((x - 45.0) ** 2) / 0.02) + 0.05

   peak_x, peak_y = detect_peaks(x, y, num_peaks=1, prominence=0.1)
   fwhm, amp, left, right = calculate_fwhm(x, y, peak_x[0])

Runnable Demo
=============

Try a full synthetic workflow (peak detection, FWHM, alignment, and plotting):

.. code-block:: bash

   # from repo root
   PYTHONPATH=src python examples/demo_xrd_scan.py

This writes a demo figure to ``examples/output/demo_xrd_scan.png``.

Features
========

- Peak detection and alignment utilities for XRD scans.
- FWHM estimation and fringe-based thickness estimation helpers.
- Visualization for stacked 1D XRD scans.
- Reciprocal space mapping (RSM) plotting tools.

Documentation
=============

Sphinx documentation is provided in the ``docs`` directory.

Build docs locally:

.. code-block:: bash

   pip install -r docs/requirements.txt
   pip install -e .
   sphinx-build -b html docs docs/_build/html

License
=======

This project is licensed under the MIT License. See ``LICENSE.txt``.
