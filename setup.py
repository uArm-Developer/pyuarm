from setuptools import setup, find_packages

from distutils.util import convert_path


long_description = open('README.rst').read()

main_ns = {}
ver_path = convert_path('pyuarm/version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name='pyuarm',
    version=main_ns['__version__'],
    author='Joey Song/Alex Tan',
    packages=find_packages(),
    scripts=['pyuarm/tools/firmware_helper.py', 'pyuarm/tools/calibrate.py', 'pyuarm/tools/list_uarms.py'],
    package_data={'pyuarm.tools': ['avrdude/*'] },
    include_package_data=True,
    author_email='developer@ufactory.cc',
    url="https://github.com/uarm-developer/pyuarm",
    keywords="pyuarm uarm4py uarmForPython uarm ufactory",
    install_requires=requirements,
    long_description=long_description,
    description='A python library for uArm',
)
