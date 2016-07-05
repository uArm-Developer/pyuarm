from distutils.util import convert_path
from setuptools import setup, find_packages

main_ns = {}
ver_path = convert_path('pyuarm/version.py')
with open(ver_path) as ver_file:
        exec(ver_file.read(), main_ns)

version = main_ns['__version__']

long_description = open('README.rst').read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name='pyuarm',
    version=version,
    author='Joey Song/Alex Tan',
    packages=find_packages(),
    entry_points={
            'console_scripts': [
                'uarm-firmware = pyuarm.tools.firmware_helper:main',
                'uarm-calibrate = pyuarm.tools.calibrate:main',
                'uarm-listport = pyuarm.tools.list_uarms:main']
    },
    package_data={'pyuarm.tools': ['avrdude/*']},
    include_package_data=True,
    author_email='developer@ufactory.cc',
    url="https://github.com/uarm-developer/pyuarm",
    keywords="pyuarm uarm4py uarmForPython uarm ufactory",
    install_requires=requirements,
    long_description=long_description,
    description='A python library for uArm',
)
