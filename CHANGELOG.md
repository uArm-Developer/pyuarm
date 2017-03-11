##[2.4.0.12] - 2017-03-11
### Update -Alex Tan

- Firmware 2.2.1

#### Changes

1. Improve Firmware flash
2. Improve Log description

## [2.4.0.9] - 2017-03-10
### Updated -Alex Tan

- Firmware 2.2.1

# Changes
1. Rewrite threading part improve performance
2. Add Wait parameters for Set Functions.


## [2.3.0.7] - 2016-12-04
### Updated -Alex Tan

### Compatible
- Firmware 2.2

### Changes
1. Fix Bugs for Non-block Mode
2. Add Teach function

## [2.3.0.3] - 2016-12-04
### Updated -Alex Tan

### Compatible
- Firmware 2.2

### Changes
1.  Support Unblock Mode
2.  rewrite FlashFirmware & calibrate. Flash Firmware only support external avrdude, calibrate only support query
3.  Fix connect Flag support
4.  Add set_polar support


## [2.2.5.1] - 2016-11-25
### Updated -Alex Tan

### Compatible
- Firmware 2.2

### Changes
1. Support wait for set_position

## [2.2.5.1] - 2016-11-25
### Updated -Alex Tan

### Compatible
- Firmware 2.2

### Changes
1. Fix Tip Sensor return False always
2. Rewrite logger logic
3. Add Relative coordinate support
4. Use printf in Calibrate


## [2.2.4] - 2016-11-16
### Updated -Alex Tan

### Compatible
- Firmware 2.2

### Changes
1. Fix install bug


## [2.2.3] - 2016-11-16
### Updated -Alex Tan

### Compatible
- Firmware 2.2

### Changes
1. Add function check_port_plug_in (beta)
2. Get Hardware version once connect
3. Fix is_connected when uarm plug out but still return True
4. Add Set Debug for logger

## [2.2.2] - 2016-11-16
### Updated -Alex Tan

### Compatible
- Firmware 2.2

### Changes
1. Fix pyuarm.__version__
2. Fix pypi MANIFEST.in not found


## [2.2.0] - 2016-11-16
### Updated -Alex Tan

### Compatible
- Firmware 2.2

### Changes
1. Compatible with firmware 2.2 (Gcode)
2. Fix Camera Disconnect No response
3. Add Protocol Version

## [2.1.1] - 2016-10-28
### Updated -Alex Tan

### Compatible
- Firmware 2.1

### Changes
1. Compatible with firmware 2.1
2. Compatible with Python2.x and Python 3.x
3. Rewrite Calibration logic
4. Rewrite Firmware logic (Reduce 3rd-party library dependencies) Include `avrdude` on Mac/Windows/Linux
5. Rename Functions in uarm. get/set for all communication protocol.

## [2.0.7] - 2016-09-06
### Updated - Alex Tan

### Compatible
- Firmware 2.0

### Fix
1. Fix list port issue
2. Fix receive F start error

## [2.0.6] - 2016-09-06
### Updated - Alex Tan

### Compatible
- Firmware 2.0

### Fix
1. Protocol:  
- Support Raw Servo Angle, SET_ANGLE = "sAngN{}V{}", SET_RAW_ANGLE = "sSerN{}V{}", GET_RAW_ANGLE = "gSer", GET_ANGLE = "gAng"
- Buzzer add stop Duration, SET_BUZZER = "sBuzF{}T{}S{}"
- version start with "v"
2. pyuarm:  
- set Debug before any action.
- if response message start with "f", means error
- set & get EEPROM return value depend on data type
3. Calibrate:  
- Add version 1.1.0
- Compatible with 2.0 firmware
4. list_uarm:  
- get_uarm()
- get_uarm_port_cli()
5. Miniterm:
- change read_servo_angle to get_servo_angle, write_servo_angle to set_servo_angle
- Add version 0.1.3
6. Others:  
- `python -m pyuarm.version` will display the library version and support version


## [2.0.5] - 2016-08-31
### Updated - Alex Tan

### Compatible
- Firmware 2.0

### Fix
**uarm-cli**
- get_analog, get_eeprom, set_eeprom, get_serial_number

## [2.0.3] - 2016-08-10
### Updated - Alex Tan

### Compatible
- Firmware 0.9.9

### Fix
**uarm-cli**
- help topic hide welcome message
- compatible with 0.9.9
- uarm-cli add debug option
- uarm-firmware fix -d argument issue

## [2.0.2] - 2016-08-10
### Updated - Alex Tan

### Compatible
- Firmware 0.9.8b

### Fix
**uarm-cli**  
- Use colorama Compatible with Windows platform
- fix firmware error if no uarm connect
- Catch KeyboardInterrupt
- add shortcut tip when cli start, and help center


## [2.0.0] - 2016-07-13
### Updated - Alex Tan

### Compatible
- Firmware 2.0

### Changes
- Brand new Protocol

### detail -2016-07-13
- Fix timeout issue when new Serial port
- remove time.sleep(3) after new Serial port, use is_ready() function instead
- Add UArmConnectException
- add disconnect() function
- flushInput before read anything
- use readline() replace old read logic
- add validate_coordinate()
- update move_to,pump_on, pump_off, set_buzzer, is_moving, get_servo_angle, get_tip_sensor
- add write_servos_angle
- update firmware_helper.py with new Protocol
- add cmd for for control

### detail - 2016-08-09
- connect() function after open port
- cli add serial mode

### detail - 2016-08-03
- Compatible with v0.9.7b

## [1.3.27] - 2016-07-08
### Updated - Alex Tan

### Compatible
- Firmware 1.7

### Fix
- Fix calibrate issue when use GUI.

## [1.3.26] - 2016-07-05
### Updated - Alex Tan

### Compatible
- Firmware 1.7

### Fix
- Firmware helper support port argument.
- improve firmware helper in mac os x if not install avrdude.
- add console-script: uarm-firmware, uarm-calibrate, uarm-list.

## [1.3.25] - 2016-07-01
### Updated - Alex Tan

### Compatible
- Firmware 1.7

### Fix
- Move Back to use version.py due to pyinstaller encounter error

## [1.3.24] - 2016-06-30
### Updated - Alex Tan

### Compatible
- Firmware 1.7

### Fix
- Use version.json replace version.py
- Add Support firmware version in version.json, if not Compatible will raise UnsupportFirmwareVersionException
- Add argument for calibrate.py
- Disable Stretch Calibration
- Change Linear Calibration, Increasing moving points
- Merge [frankyjuang](https://github.com/frankyjuang), fix typo

## [1.3.21] - 2016-06-28
### Updated - Alex Tan

### Compatible
- Firmware 1.7.1

### Fix
- rewrite Firmware helper. remove pycurl

## [1.3.20] - 2016-06-28
### Updated - Alex Tan

### Compatible
- Firmware 1.7.1

### Fix
- Increase More delay on calibrate. rewrite Linear Offset points.
- Update requirements.txt


## [1.3.19] - 2016-06-27
### Updated - Alex Tan

### Fix
- Increase More delay on calibrate. rewrite Linear Offset points.
- Update requirements.txt

## [1.3.18] - 2016-06-22
### Updated - Alex Tan

### Fix
- firmware_helper -f won't download the firmware.hex use firmware_helper -d instead

## [1.3.17] - 2016-06-22
### Updated - Alex Tan

### Fix
- firmware_helper remove access token

### To-Do
- Setup Firmware_checker at UFactory Server

## [1.3.16] - 2016-06-22
### Updated - Alex Tan

### Fix
- firmware_helper add APIError check

## [1.3.15] - 2016-06-22
### Updated - Alex Tan

### Fix
- Add enable_hand support Firmware 1.6.1

## [1.3.14] - 2016-06-22
### Updated - Alex Tan

### Fix
- Raise UnkwonFirmwareException when init uArm.

## [1.3.13] - 2016-06-14
### Updated - Alex Tan

### Changes
- Try NetworkError in firmware_helper

## [1.3.12] - 2016-06-14
### Updated - Alex Tan

### Changes
- Compatible with Firmware 1.6.0
- Time.sleep(3) when init Serial Port
- read_servo_angle() when servo_number is none, if servo_number is None, will return all servo angles (SERVO_BOTTOM, SERVO_LEFT, SERVO_RIGHT, SERVO_HAND).
- Update Firmware Release URL

### Fix
- Fix pyuarm.tools.calibrate print format & raw_input

## [1.3.11] - 2016-06-14
### Updated - Alex Tan

### Changes
- include requirements, README.rst

## [1.3.10] - 2016-06-14
### Updated - Alex Tan

### Changes
- include requirements, README.rst

## [1.3.9] - 2016-06-14
### Updated - Alex Tan

### Changes
- add version.py for version variable

## [1.3.8] - 2016-06-14
### Updated - Alex Tan

### Changes
- Replace progressbar with tqdm
- Rewrite firmware_helper into class
- calibrate.py confirm manual trigger in raw_input: y

## [1.3.7] - 2016-06-13
### Updated - Alex Tan

### Changes
- Add requirements.txt

## [1.3.7] - 2016-06-13
### Updated - Alex Tan

### Changes
- Update read_coordinate()
- Update util.py function name getOne7BitBytesFloatArray, getThree7BitBytesFloatArray

## [1.3.6] - 2016-06-13
### Updated - Alex Tan

### Changes
- Update read_coordinate()
- Update util.py function name getOne7BitBytesFloatArray, getThree7BitBytesFloatArray

## [1.3.5] - 2016-06-13
### Updated - Alex Tan

### Changes
- Update Version 1.3.5
- Update Documentation
- Update README.md to README.rst

## [1.3.4] - 2016-06-10
### Updated - Alex Tan

### Changes
- move pyuarm.calibrate to pyuarm.tools.calibrate
- move pyuarm.list_uarms function to pyuarm.tools.list_uarms
- pyuarm.py replace serial_read_byte() with sp.read(1), support debug read message
- firmware_helper.py add NetworkError
- Docstring
- move Exception get_uarm to pyuarm.util
- pyuarm.py set_firmware_version, set_firmata_version to get_firmware_version, get_firmata_version.
- pyuarm.py move_to_opts, move_to_simple, move integrate with one Function move_to
- pyuarm.py changes alert() function to alarm()

## [1.3.3] - 2016-06-08
### Updated - Alex Tan

### Fix
- fix setup.py package_data avrdude folder, MANIFEST.in

## [1.3.2] - 2016-06-08
### Updated - Alex Tan

### Fix
- fix setup.py 'pycurl>=7.43.0', 'certifi>=2016.02.28', 'tqdm>=4.7.2', 'requests>=2.10.0'

## [1.3.2] - 2016-06-08
### Updated - Alex Tan

### Fix
- firmware_helper, improve download progress bar

## [1.3.0] - 2016-06-08
### Updated - Alex Tan

### Changes
- Add moudle pyuarm.tools, integrate with firmware_helper, list_uarms

## [1.2.11] - 2016-06-04
### Updated - Alex Tan

### Fix
- Add NoUArmPortException, UnkwonFirmwareException

## [1.2.10] - 2016-06-04
### Updated - Alex Tan

### Fix
- uArm() Default use list_uarm()[0]

## [1.2.9] - 2016-06-01
### Updated - Alex Tan

### Fix
- Add firmware_version and firmata_version

## [1.2.8] - 2016-05-11
### Updated - Alex Tan

### Fix
- Add Default Timeout is 5 sec

## [1.2.7] - 2016-05-11
### Updated - Alex Tan

### Fix
- Changes Alert as 3, 100, 100

## [1.2.6] - 2016-05-11
### Updated - Alex Tan

### Changes
- alert uarm when start manual calibration
- Reduce delay during linear calibration

## [1.2.5] - 2016-05-10
### Updated - Alex Tan

### Changes
- Add BUZZER_ALERT 0x24

## [1.2.4] - 2016-05-06
### Updated - Alex Tan

### Fix
- remove py_modules

## [1.2.3] - 2016-05-06
### Updated - Alex Tan

### Fix
- remove docutils from dependency

## [1.2.2] - 2016-05-06
### Updated - Alex Tan

### Fix
- Callback Function default to None
- Update SERIAL_NUMBER_ADDRESS to 100

## [1.2.1] - 2016-05-03
### Updated - Alex Tan

### Fix
- Change all function names as lowercase
- Use CONFIRM_FLAG 0x80 for Confirmation Flag

## [1.2.0] - 2016-05-03
### Updated - Alex Tan

### Changes
- Add uArm Library Version (Firmware Version) and Firmata Version

## [1.1.9] - 2016-05-03
### Updated - Alex Tan

### Fix
- Add Stretch Calibration Flag support stop during Stretch Calibration
- Add PUMP_PIN, VALVE_PIN Constant Values

## [1.1.8] - 2016-05-02
### Updated - Alex Tan

### Changes
- Add readSerialNumber and writeSerialNumber Function

## [1.1.7] - 2016-05-01
### Updated - Alex Tan

### Fix
- Change calibrate function name "calibrate" to calibration

## [1.1.6] - 2016-05-01
### Updated - Alex Tan

### Changes
- Changes library name uarm4py to pyuarm  

## [1.1.6] - 2016-04-30
### Updated - Alex Tan

### Fix
- read Analog, read EEPROM, read Digital, read Servo Angle, add pin number/ address / servo number before receive data

## [1.1.5] - 2016-04-29
### Updated - Alex Tan

### Fix
- uarm.py Fix MoveTo, Move, moveToOpts


## [1.1.4] - 2016-04-25
### Updated - Alex Tan

### Fix
- calibrate.py Fix is_all_calibrated, is_manual_calibrated, is_linear_calibrated, name issue
- uarm.py Fix PumpStatus , GripperStatus

### Changes

- Add Comment into calibrate.py
- Add Function Complete Flag
- Add Calibrate All Function


## [1.1.3] - 2016-04-25
### Updated - Alex Tan

### Fix
- calibrate.py is_all_calibrated, is_stretch_calibrated, is_manual_calibrated, is_linear_calibrated rename


## [1.1.2] - 2016-04-24
### Updated - Alex Tan

### Changes
- add setup.py for script install
- rename calibrate.py function names to match the Python Standard

## [1.1.1] - 2016-04-21
### Updated - Alex Tan

### Fix
- rename self.uarm to self.sp

### Changes
- Provide uarm isConnected Function


## [1.1.0] - 2016-04-18
### Updated - Alex Tan

### Fix
- Fix float decimal accuracy

### Changes
- Compatible with uArm Firmata v1.5
- New function *list_uarms()* will return all the available uArm ports
- New function *get_uarm()* will return the instance from first port of *list_uarms()*
- get Firmware version when initialize
- Move(x,y,z) Relative action control
