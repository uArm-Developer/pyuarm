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
