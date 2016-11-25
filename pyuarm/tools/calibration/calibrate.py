from __future__ import print_function
import sys
import copy
import time
import os
import serial

from ... import PY3
from ...uarm import UArm
from ..list_uarms import get_uarm_port_cli
from ...protocol import *
from ..firmware  import flash,get_uarm_port_cli, download, default_config
from ...util import printf


if PY3:
    izip = zip
else:
    from itertools import izip


__version__ = "2.0.0"

if getattr(sys, 'frozen', False):
    FROZEN_APP = False
else:
    FROZEN_APP = True

if FROZEN_APP:
    application_path = os.path.dirname(__file__)
else:
    application_path = os.path.dirname(sys.executable)

default_calibration_hex = 'calibration.hex'



def calibrate(port_name):
      # Flash the calibration firmware
    sp = serial.Serial(port=port_name, baudrate=115200)
    READY = '[STEP]READY'
    START = '[STEP]START'
    COMPLETE = '[STEP]COMPLETE'
    if PY3:
        ready_msg = bytes(READY, encoding='ascii')
        start_msg = bytes(START, encoding='ascii')
        complete_msg = bytes(COMPLETE, encoding='ascii')
    else:
        ready_msg = READY
        start_msg = START
        complete_msg = COMPLETE
    while True:
        if get_serial_line(sp).startswith(ready_msg):  # Waiting For READY MESSAGE
            break
        time.sleep(0.01)
    while True:
        if get_serial_line(sp).startswith(start_msg):  # Waiting For START MESSAGE
            break
        time.sleep(0.01)
    while True:
        if get_serial_line(sp).startswith(complete_msg):  # Waiting For COMPLETED MESSAGE
            break
        time.sleep(0.01)


def get_serial_line(sp):
    line = sp.readline()
    if line != b'':
        printf(line)
    return line



def read_manual_offset(uarm):
    address = OFFSET_START_ADDRESS
    read_manual_offset = []
    for i in range(4):
        read_manual_offset.append(round(uarm.get_rom_data(address, EEPROM_DATA_TYPE_FLOAT), 2))
        address += 4
    return read_manual_offset


def read_linear_offset(uarm):
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

    if args.check:
        uarm = UArm(port_name=port_name, debug=debug)
        printf("All Calibration: {}".format("COMPLETED" if read_completed_flag(uarm, CALIBRATION_FLAG) else "NOT COMPLETED"))
        printf("Linear Calibration: {}".format("COMPLETED" if read_completed_flag(uarm, CALIBRATION_LINEAR_FLAG) else "NOT COMPLETED"))
        printf("Manual Calibration: {}".format("COMPLETED" if read_completed_flag(uarm, CALIBRATION_SERVO_FLAG) else "NOT COMPLETED"))
        for linear_offset,manual_offset, i in izip(read_linear_offset(uarm), read_manual_offset(uarm), range(4)):
            print ("Servo {} INTERCEPT: {}, SLOPE: {}, MANUAL: {}".format(i,linear_offset['INTERCEPT'], linear_offset['SLOPE'], manual_offset))
    else:
        uarm = UArm(port_name=port_name, debug=debug)
        calibration_completed_flag = read_completed_flag(uarm, CALIBRATION_FLAG)
        printf("All Calibration: {}".format("COMPLETED" if calibration_completed_flag else "NOT COMPLETED"))
        if calibration_completed_flag:
            if PY3:
                choice = input("Calibration Completed, Are you sure to continue? Yes, please press Y\n")
            else:
                choice = raw_input("Calibration Completed, Are you sure to continue? Yes, please press Y\n")
            if choice.lower() == 'y':
                if PY3:
                    input("Please don't quit until calibration completed. Continue please press Enter.\n")
                else:
                    raw_input("Please don't quit until calibration completed. Continue please press Enter.\n")
                firmware_path = os.path.join(os.getcwd(), default_config['filename'])
                download(default_config['download_url'], firmware_path)
                flash(port_name, default_calibration_hex)
                calibrate(port_name)
                flash(port_name, firmware_path)
            else:
                print ("Exit")
        else:
            if PY3:
                input("Please don't quit until calibration completed. Continue please press Enter.\n")
            else:
                raw_input("Please don't quit until calibration completed. Continue please press Enter.\n")
            firmware_path = os.path.join(os.getcwd(), default_config['filename'])
            download(default_config['download_url'], firmware_path)
            flash(port_name, default_calibration_hex)
            calibrate(port_name)
            flash(port_name, firmware_path)


if __name__ == '__main__':
    try:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("-p", "--port", help="specify port number")
        parser.add_argument("-d", "--debug", help="Open Debug Message", action="store_true")
        parser.add_argument("-c", "--check", help="Check the calibrate offset values", action="store_true")
        args = parser.parse_args()
        main(args)
    except Exception as e:
        print (str(e))
