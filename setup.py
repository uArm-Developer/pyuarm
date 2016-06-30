from setuptools import setup, find_packages
import os
import json

long_description = open('README.rst').read()

module_dir = os.path.dirname(os.path.abspath(__file__))
version_file = os.path.join(module_dir, 'pyuarm','version.json')
with open(version_file,'r') as v:
    data = json.load(v)
    v.close()

# pyuarm version
version = data['module_version']
__version__ = VERSION = version

# support version
support_versions = data['support_versions']

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name='pyuarm',
    version=version,
    author='Joey Song/Alex Tan',
    packages=find_packages(),
    scripts=['pyuarm/tools/firmware_helper.py', 'pyuarm/tools/calibrate.py', 'pyuarm/tools/list_uarms.py'],
    package_data={'pyuarm.tools': ['avrdude/*'], 'pyuarm':['version.json']},
    include_package_data=True,
    author_email='developer@ufactory.cc',
    url="https://github.com/uarm-developer/pyuarm",
    keywords="pyuarm uarm4py uarmForPython uarm ufactory",
    install_requires=requirements,
    long_description=long_description,
    description='A python library for uArm',
)
