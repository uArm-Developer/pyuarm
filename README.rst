===============================
pyuarm
===============================

Overview
========

This module encapsulates the operations for uArm. It provides basic Movement on Python.
Also provides Firmware_helper and Calibration. The module named "pyuarm" makes the API more pythonic.

Other pages (online)

- `project page on Github`_
- `Download Page`_ with releases
- This page, when viewed online is at https://pyuarm.readthedocs.io/en/latest/.


Features
========
- Auto uArm Port detection
- Provide firmware_helper, firmware upgrade online
- Provide Auto Calibration tool

Requirements
============
- Python 2.7x (Python3.x not supported yet)
- uArmProtocol Firmware (Please use ``python -m pyuarm.tools.firmware_helper`` to upgrade your firmware)

Installation
============

pyuarm
------
This install a package that can be used from Python (``import pyuarm``).

To install for all users on the system, administrator rights (root) may be required.

From PyPI
~~~~~~~~~
pyuarm can be installed from PyPI, either manually downloading the files and installing as described below or using::

    pip install pyuarm

From source (tar.gz or checkout)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Download the archive from http://pypi.python.org/pypi/pyuarm.
Unpack the archive, enter the ``pyuarm-x.y`` directory and run::

    python setup.py install

.. _`project page on GitHub`: https://github.com/uArm-Developer/pyuarm
.. _`Download Page`: http://pypi.python.org/pypi/pyuarm