
from setuptools import setup, find_packages
import pyuarm
setup(name='pyuarm',
    version=pyuarm.VERSION,
    author='Joey Song/Alex Tan',
    packages=['pyuarm', 'pyuarm.tools'],
    author_email='developer@ufactory.cc',
    description='A python library for uArm',
    url="https://github.com/uarm-developer/pyuarm",
    keywords="pyuarm uarm4py uarmForPython uarm ufactory",
    install_requires = ['pyserial>=3.0', 'pycurl>7.43.0', 'certifi>2016.02.28', 'tqdm>4.7.2', 'requests>2.10.0'],
)
