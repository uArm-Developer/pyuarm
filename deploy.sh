#!/bin/sh

python setup.py register -r pypi
python setup.py sdist upload -r pypi

pyinstaller -F pyuarm/tools/firmware_helper.py
pyinstaller -F pyuarm/tools/calibrate.py


