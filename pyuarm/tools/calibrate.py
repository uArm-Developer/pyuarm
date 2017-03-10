"""
pyuarm.tools.calibrate
This is part of pyuarm. Provide the calibrate information query. Include three sections.
1. Linear Offset
2. Manual Offset
3. Complete flag
If you want to calibrate uArm. Please use uArm assistant.
"""


from __future__ import print_function
import sys
import copy

from pyuarm import PY3
from pyuarm.uarm import UArm
from pyuarm.tools.list_uarms import get_uarm_port_cli
from pyuarm.protocol import *
from pyuarm.util import printf


if PY3:
    izip = zip
else:
    from itertools import izip

__version__ = "2.0.0"

def read_manual_offset(uarm):
    """
    Read Manual Offset from uArm EEPROM
    :param uarm: uArm instance
    :return:
    """
    address = OFFSET_START_ADDRESS
    read_manual_offset = []
    for i in range(4):
        read_manual_offset.append(round(uarm.get_rom_data(address, EEPROM_DATA_TYPE_FLOAT), 2))
        address += 4
    return read_manual_offset


def read_linear_offset(uarm):
    """
    Read Linear Offset from uArm EEPROM
    :param uarm: uArm instance
    :return:
    """
    linear_offset_template = {"INTERCEPT": 0.00, "SLOPE": 0.00}
    intercept_address = LINEAR_INTERCEPT_START_ADDRESS
    slope_address = LINEAR_SLOPE_START_ADDRESS
    linear_offset_data = []
    for i in range(4):
        linear_offset= copy.deepcopy(linear_offset_template)
        linear_offset['INTERCEPT'] = round(
            uarm.get_rom_data(intercept_address, EEPROM_DATA_TYPE_FLOAT), 2)
        linear_offset['SLOPE'] = round(uarm.get_rom_data(slope_address, EEPROM_DATA_TYPE_FLOAT), 2)
        linear_offset_data.append(linear_offset)
        intercept_address += 4
        slope_address += 4
    return linear_offset_data


def read_completed_flag(uarm, flag_type):
    """
    Read Complete Flag from EEPROM
    :param uarm: uArm instance
    :param flag_type: protocol.CALIBRATION_FLAG, protocol.CALIBRATION_LINEAR_FLAG, procotol.CALIBRATION_SERVO_FLAG
    :return:
    """
    if flag_type == CALIBRATION_FLAG:
        if uarm.get_rom_data(CALIBRATION_FLAG) == CONFIRM_FLAG:
            return True
        else:
            return False
    elif flag_type == CALIBRATION_LINEAR_FLAG:
        if uarm.get_rom_data(CALIBRATION_LINEAR_FLAG) == CONFIRM_FLAG:
            return True
        else:
            return False
    elif flag_type == CALIBRATION_SERVO_FLAG:
        if uarm.get_rom_data(CALIBRATION_SERVO_FLAG) == CONFIRM_FLAG:
            return True
        else:
            return False


def exit_fun():
    try:
        input("\nPress Enter to Exit...")
        sys.exit(0)
    except Exception:
        pass


def main(args):
    if args.port:
        port_name = args.port
    else:
        port_name = get_uarm_port_cli()

    if args.debug:
        debug = True
    else:
        debug = False

    uarm = UArm(port_name=port_name, debug=debug)
    uarm.connect()
    printf("All Calibration: {}".format("COMPLETED" if read_completed_flag(uarm, CALIBRATION_FLAG) else "NOT COMPLETED"))
    printf("Linear Calibration: {}".format("COMPLETED" if read_completed_flag(uarm, CALIBRATION_LINEAR_FLAG) else "NOT COMPLETED"))
    printf("Manual Calibration: {}".format("COMPLETED" if read_completed_flag(uarm, CALIBRATION_SERVO_FLAG) else "NOT COMPLETED"))
    for linear_offset, manual_offset, i in izip(read_linear_offset(uarm), read_manual_offset(uarm), range(4)):
        printf("Servo {} INTERCEPT: {}, SLOPE: {}, MANUAL: {}".format(i, linear_offset['INTERCEPT'], linear_offset['SLOPE'], manual_offset))


def run():
    try:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("-p", "--port", help="specify port number")
        parser.add_argument("-d", "--debug", help="Open Debug Message", action="store_true")
        args = parser.parse_args()
        main(args)
    except Exception as e:
        printf("{} - {}".format(type(e).__name__, e))

if __name__ == '__main__':
    run()
