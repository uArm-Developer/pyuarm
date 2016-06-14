from setuptools import setup, find_packages
import pyuarm
setup(name='pyuarm',
    version=pyuarm.VERSION,
    author='Joey Song/Alex Tan',
    packages=['pyuarm', 'pyuarm.tools'],
    scripts=['pyuarm/tools/firmware_helper.py', 'pyuarm/tools/calibrate.py', 'pyuarm/tools/list_uarms.py'],
    package_data={'pyuarm.tools': ['avrdude/*'] },
    author_email='developer@ufactory.cc',
    description='A python library for uArm',
    url="https://github.com/uarm-developer/pyuarm",
    keywords="pyuarm uarm4py uarmForPython uarm ufactory",
    platform="any",
)
