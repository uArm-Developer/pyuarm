from tools.list_uarms import uarm_ports
import pyuarm

# parameters
SERVO_BOTTOM = 0
SERVO_LEFT = 1
SERVO_RIGHT = 2
SERVO_HAND = 3

SERVO_BOTTOM_ANALOG_PIN = 2
SERVO_LEFT_ANALOG_PIN = 0
SERVO_RIGHT_ANALOG_PIN = 1
SERVO_HAND_ANALOG_PIN = 3


CONFIRM_FLAG = 0x80
CALIBRATION_FLAG = 10
CALIBRATION_LINEAR_FLAG = 11
CALIBRATION_SERVO_FLAG = 12
CALIBRATION_STRETCH_FLAG = 13

LINEAR_INTERCEPT_START_ADDRESS = 70
LINEAR_SLOPE_START_ADDRESS = 50
OFFSET_START_ADDRESS = 30
OFFSET_STRETCH_START_ADDRESS = 20

SERIAL_NUMBER_ADDRESS = 100

EEPROM_DATA_TYPE_BYTE = 1
EEPROM_DATA_TYPE_INTEGER = 2
EEPROM_DATA_TYPE_FLOAT = 4

BUTTON_D7 = 7
BUTTON_D4 = 4
BUTTON_D2 = 2
PUMP_PIN = 6
VALVE_PIN = 5

PULL_UP = 1
INPUT = 0

HIGH = 1
LOW  = 0

ABSOLUTE = 0
RELATIVE = 1
PATH_LINEAR = 0   # path based on linear interpolation
PATH_ANGLES = 1   # path based on interpolation of servo angles

# interpolation types
INTERP_EASE_INOUT_CUBIC = 0  # original cubic ease in/out
INTERP_LINEAR           = 1
INTERP_EASE_INOUT       = 2  # quadratic easing methods
INTERP_EASE_IN          = 3
INTERP_EASE_OUT         = 4



def get_uarm():
    """
    ===============================
    Get First uArm Port instance
    ===============================
    It will return the first uArm Port detected by **pyuarm.tools.list_uarms**,
    If no available uArm ports, will print *There is no uArm port available*

    .. raw:python
    >>> import pyuarm
    >>> uarm = pyuarm.get_uarm()
    There is no uArm port available


    :returns: uArm() Instance

    """
    ports = uarm_ports()
    if len(ports) > 0:
        return pyuarm.UArm(port=ports[0])
    else:
        print("There is no uArm port available")


class NoUArmPortException(IOError):
    """
    .. _NoUArmPortException:
    """
    def __init__(self, error):
        self.error = error

    def __str__(self):
        return repr(self.error)


class UnknownFirmwareException(Exception):
    """
    .. UnknownFirmwareException:
    """
    def __init__(self, error):
        self.error = error
        self.message = error

    def __str__(self):
        return repr(self.error)


class UnSupportedFirmwareVersionException(Exception):
    """
    .. UnSupportFirmwareVersionException:
    """
    def __init__(self, error):
        self.error = error
        self.message = error

    def __str__(self):
        return repr(self.error)


class UArmConnectException(Exception):
    """

    """
    def __init__(self, error):
        self.error = error
        self.message = error

    def __str__(self):
        return repr(self.error)