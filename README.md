# uArm For Python

This is a uArm Library for Python.

## Requirement

- uArmForArduino - [uArmFirmata V1.5][5bd49e15]

  [5bd49e15]: https://github.com/uArm-Developer/UArmFirmata "uArmFirmata V1.5"

## Installation

### Using PYPI *Recommend*

- pip install pyuarm

### Manual Installation

- Download source code
- python setup.py install


## Usage
```Python
import pyuarm
pyuarm.list_uarms() #List All available uArm Ports
uarm = pyuarm.get_uarm() # Get the first uArm Instance
```
