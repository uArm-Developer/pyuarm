
from setuptools import setup, find_packages
import pyuarm
setup(name='pyuarm',
    version=pyuarm.VERSION,
    py_modules=['pyuarm'],
    author='Joey Song/Alex Tan',
    packages=['pyuarm'],
    author_email='developer@ufactory.cc',
    description='A python library for uArm',
    url="https://github.com/uarm-developer/pyuarm",
    keywords="pyuarm uarm4py uarmForPython uarm ufactory",
    install_requires = ['docutils>=0.3','pyserial>=3.0'],
)
