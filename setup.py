from setuptools import setup

from distutils.util import convert_path

main_ns = {}
ver_path = convert_path('pyuarm/version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)


setup(name='pyuarm',
    version=main_ns['__version__'],
    author='Joey Song/Alex Tan',
    packages=['pyuarm', 'pyuarm.tools'],
    scripts=['pyuarm/tools/firmware_helper.py', 'pyuarm/tools/calibrate.py', 'pyuarm/tools/list_uarms.py'],
    package_data={'pyuarm.tools': ['avrdude/*'] },
    author_email='developer@ufactory.cc',
    description='A python library for uArm',
    url="https://github.com/uarm-developer/pyuarm",
    keywords="pyuarm uarm4py uarmForPython uarm ufactory",
)
