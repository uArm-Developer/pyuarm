from distutils.util import convert_path
from setuptools import setup, find_packages
import platform

if platform.system() == "Windows":
    package_data = {'pyuarm.tools.calibration': ['calibration.hex'], 'pyuarm.tools.firmware': ['avrdude/windows/*']}
elif platform.system() == "Darwin":
    package_data = {'pyuarm.tools.calibration': ['calibration.hex'], 'pyuarm.tools.firmware': ['avrdude/mac/*']}
else:
    package_data = {'pyuarm.tools.calibration': ['calibration.hex']}

# Get Version from version.py file
main_ns = {}
ver_path = convert_path('pyuarm/version.py')
with open(ver_path) as ver_file:
        exec(ver_file.read(), main_ns)
version = main_ns['__version__']

# Get README.rst for description
long_description = open('README.rst').read()

# Read requirements.txt as install_requires
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name='pyuarm',
    version=version,
    author='Alex Tan',
    packages=find_packages(),
    entry_points={
            'console_scripts': [
                'uarm_helper = pyuarm.tools.console_scripts:main',
            ]
    },
    # data_files=data_files,
    package_data=package_data,
    include_package_data=True,
    author_email='developer@ufactory.cc',
    url="https://github.com/uarm-developer/pyuarm",
    keywords="pyuarm uarm4py uarmForPython uarm ufactory",
    install_requires=requirements,
    long_description=long_description,
    description='A python library for uArm',
    license='MIT'
)
