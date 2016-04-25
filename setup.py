
from setuptools import setup, find_packages
import uarm
setup(name='uarm',
    version=uarm.VERSION,
    py_modules=['uarm4py'],
    author='Joey Song/Alex Tan',
    packages=['uarm'],
    author_email='developer@ufactory.cc',
    description='A python library for uArm',
    url="https://github.com/UFactory-Alex/uarm4py",
    keywords="uarm4py uarm ufactory",
    install_requires = ['docutils>=0.3','pyserial>=3.0'],
)
