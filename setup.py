from distutils.util import convert_path
from setuptools import setup, find_packages
import sys
import os
import platform

OS_TYPE = None

if platform.system() == 'Darwin':
    OS_TYPE = 'macosx'
elif platform.system() == 'Linux':
    OS_TYPE = 'linux'
elif platform.system() == 'Windows':
    OS_TYPE = 'windows'

if OS_TYPE is None:
    print ("System not supported {}".format(platform.system()))
    sys.exit(1)

avrdude_list = []
avrdude_path = os.path.join('.', 'pyuarm', 'tools', 'firmware', 'avrdude')
if OS_TYPE.lower() == 'macosx':
    avrdude_list = [os.path.join(avrdude_path, 'mac', 'avrdude'),
                    os.path.join(avrdude_path, 'mac', 'avrdude.conf'),
                    os.path.join(avrdude_path, 'mac', 'avrdude_bin'),
                    os.path.join(avrdude_path, 'mac', 'libusb.dylib'),
                    os.path.join(avrdude_path, 'mac', 'libusb-0.1.4.dylib'),
                    os.path.join(avrdude_path, 'mac', 'libusb-1.0.0.dylib'),
                    os.path.join(avrdude_path, 'mac', 'libusb-1.0.dylib'),
                    ]
elif OS_TYPE.lower()  == 'linux':
    avrdude_list = [os.path.join(avrdude_path, 'linux', 'avrdude'),
                    os.path.join(avrdude_path, 'linux', 'avrdude-x64'),
                    os.path.join(avrdude_path, 'linux', 'avrdude.conf'),

    ]
elif OS_TYPE.lower()  == 'windows':
    avrdude_list = [os.path.join(avrdude_path, 'windows', 'avrdude.exe'),
                    os.path.join(avrdude_path, 'windows', 'libusb0.dll'),
                    os.path.join(avrdude_path, 'windows', 'avrdude.conf'),

    ]

data_files = [(avrdude_path, avrdude_list ),
              ]
print ("OSTYPE: " + OS_TYPE)
for a in avrdude_list:
    print (a)
package_data = {
                os.path.join('.', 'pyuarm', 'tools', 'calibration'): ['calibration.hex']
                }


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
    author='Alex Tan',
    packages=find_packages(),
    entry_points={
            'console_scripts': [
                'uarm_helper = pyuarm.tools.console_scripts:main',
            ]
    },
    data_files=data_files,
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
