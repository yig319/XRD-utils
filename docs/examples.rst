========
Examples
========

Runnable demo (synthetic data)
==============================

The repository includes a runnable demo script:

- ``examples/demo_xrd_scan.py``

It generates synthetic XRD scans, runs peak/FWHM analysis, aligns scans, and
saves a comparison figure.

Run from repository root:

.. code-block:: bash

   # Option 1: with installed package
   python examples/demo_xrd_scan.py

   # Option 2: without install (use local source)
   PYTHONPATH=src python examples/demo_xrd_scan.py

Expected output:

- Console summary of peak position and FWHM per sample
- Figure saved at ``examples/output/demo_xrd_scan.png``

