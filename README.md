<img src="https://ufactory.cc/viewpage/img/logo-whole-png.png" width="200">

# pyuarm

This is a uArm Library for Python.
## Requirement

- uArmFirmata - [uArmFirmata V1.5][5bd49e15]

We recommend you to use [FirmwareHelper][328e8ff3], You could flash the firmware to uArm without pain.

## Installation

### Using PYPI
*Recommend*

- pip install pyuarm

### Manual Installation

- Download source code
- python setup.py install

## Getting Start

### Initialize uArm
There are two methods to Initialize uArm.
- Use get_uarm()
```Python
>>> import pyuarm
>>> uarm = pyuarm.get_uarm()
Firmware Version: 1.5.9
```
if no uArm connected, will return `None` and display "There is no uArm Port available"
```Python
>>> import pyuarm
>>> uarm = pyuarm.get_uarm()
There is no uArm port available
>>> print uarm
None
```
- Use uArm()
``` Python
>>> import pyuarm
>>> uarm = pyuarm.uArm()
Firmware Version: 1.5.9
```
If no uArm connected, will raise `NoUArmPortException`.
```Python
>>> uarm = pyuarm.uArm()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "pyuarm.py", line 114, in __init__
    raise NoUArmPortException()
pyuarm.NoUArmPortException
```
You could turn on Debug Mode
```Python
>>> import pyuarm
>>> uarm = pyuarm.uArm(debug_mode=True)
f0aa23f7
Firmware Version: 1.5.9
```
Define the uArm port
```Python
>>> import pyuarm
>>> uarm = pyuarm.uArm(port='/dev/cu.usbserial-A600CVS1')
Firmware Version: 1.5.9
```

### Movement

```Python
>>> uarm.moveTo(15, -5, 15) ### Absolute coordinate in 2 seconds
>>> uarm.move(5, 5, 5) ### Relative coordinate
```

### Current Positions
```Python
>>> uarm.read_coords() ### Read Current Coordinate
```

### Pump control
```Python
>>> uarm.pump_control(True) ### Pump On
>>> uarm.pump_control(False) ### Pump Off
```

### Others

#### List uArm Ports
```Python
>>> import pyuarm
>>> pyuarm.list_uarms() #List All available uArm Ports
[u'/dev/cu.usbserial-A600CVS1']
```

[5bd49e15]: https://github.com/uArm-Developer/UArmFirmata "uArmFirmata V1.5"
[a3fca171]: https://github.com/uArm-Developer/UArmForArduino "UArmForArduino"
[328e8ff3]: https://github.com/uArm-Developer/FirmwareHelper "FirmwareHelper"
