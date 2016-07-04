#!/bin/sh
#if [[ $# -ne 0 ]] ; then
if [[ $1 == "upload" ]] ; then
    python setup.py register -r pypi
    python setup.py sdist upload -r pypi
fi
#fi

pyinstaller -F pyuarm/tools/firmware_helper.py
pyinstaller -F pyuarm/tools/calibrate.py

zip -j dist/release/calibrate_macosx.zip dist/calibrate
zip -j dist/release/firmware_helper_macosx.zip dist/firmware_helper
