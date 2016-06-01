<img src="https://ufactory.cc/viewpage/img/logo-whole-png.png" width="200">

# uArm For Python

This is a uArm Library for Python.

## Requirement

- Arduio Library - [uArmForArduino V1.5.8][UArmForArduino][a3fca171]
- uArmFirmata - [uArmFirmata V1.5][5bd49e15]

We recommend you to use [FirmwareUpgradeTool][328e8ff3], You could flash the firmware to uArm without pain.

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

[5bd49e15]: https://github.com/uArm-Developer/UArmFirmata "uArmFirmata V1.5"
[a3fca171]: https://github.com/uArm-Developer/UArmForArduino "UArmForArduino"
[328e8ff3]: https://github.com/uArm-Developer/FirmwareUpgradeTool "FirmwareUpgradeTool"
