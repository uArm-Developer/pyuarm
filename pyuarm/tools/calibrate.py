from pyuarm import *
from pyuarm.tools.list_uarms import uarm_ports
import copy
import argparse
import sys

INIT_POS_L = 139
INIT_POS_R = 26
SAMPLING_DEADZONE = 2


class Calibration(object):
    manual_calibration_trigger = True
    linear_calibration_start_flag = False
    stretch_calibration_flag = False

    linear_offset_template = {"INTERCEPT": 0.00, "SLOPE": 0.00}
    linear_offset = [linear_offset_template, linear_offset_template, linear_offset_template, linear_offset_template]
    linear_offset_servo_flag = [False, False, False, False]
    manual_offset = [0.00, 0.00, 0.00]
    stretch_offset_template = {"LEFT": 0.00, "RIGHT": 0.00}
    temp_manual_offset_arr = [0.00, 0.00, 0.00]
    manual_offset_correct_flag = [False, False, False]

    def __init__(self, uarm=None, log_function=None):
        if uarm is not None:
            self.uarm = uarm
        elif len(uarm_ports()) > 0:
            self.uarm = get_uarm()
        else:
            raise NoUArmPortException('No available uArm Founds')

        if log_function is not None:
            self.log_function = log_function
        else:
            self.log_function = self.default_log
        self.servo_calibrate_timeout = 300
        self.is_all_calibrated = False
        self.is_linear_calibrated = False
        self.is_manual_calibrated = False
        self.is_stretch_calibrated = False

    @staticmethod
    def default_log(msg):
        print msg

    def uf_print(self, msg):
        self.log_function(msg)

    def calibrate_all(self, linear_callback=None, manual_callback=None, stretch_callback=None):
        self.uf_print("0. Clearing Completed Flag in EEPROM.")
        self.write_completed_flag(CALIBRATION_FLAG, False)
        time.sleep(1)

        if linear_callback is None:  # If not provide callback function use default
            self.linear_calibration_section(None)
        else:
            linear_callback()

        if self.read_completed_flag(CALIBRATION_LINEAR_FLAG):
            if manual_callback is None:  # If not provide callback function use default
                self.manual_calibration_section(None)
            else:
                manual_callback()
            time.sleep(1)

        if self.read_completed_flag(CALIBRATION_SERVO_FLAG):
            # if stretch_callback is None:  # If not provide callback function use default
            self.stretch_calibration_section()
            # else:
            #     stretch_callback()
            time.sleep(1)

        if self.read_completed_flag(CALIBRATION_STRETCH_FLAG):
            self.write_completed_flag(CALIBRATION_FLAG, True)
            self.uf_print("Calibration DONE!!")

    def linear_calibration_section(self, callback=None):
        self.linear_calibration_start_flag = True
        self.uf_print("1.0. Clearing Linear Completed Flag in EEPROM.")
        self.write_completed_flag(CALIBRATION_LINEAR_FLAG, False)
        self.uf_print("1. Start Calibrate Linear Offset")
        for i in range(4):
            self.uf_print("    1.1. {0} Linear Offset - Servo {1}".format(str(i), str(i)))
            temp_linear_offset = self.calibrate_linear_servo_offset(i)
            linear_is_correct = False
            if check_linear_is_correct(temp_linear_offset):
                self.linear_offset[i] = temp_linear_offset
                linear_is_correct = True
            else:
                linear_is_correct = False
            if callback is not None:
                callback(i, linear_is_correct, temp_linear_offset)

        self.save_linear_offset()
        time.sleep(1)
        if self.read_linear_offset() == self.linear_offset:
            self.uf_print("    1.3 Mark Completed Flag in EEPROM")
            self.write_completed_flag(CALIBRATION_LINEAR_FLAG, True)
            self.linear_calibration_start_flag = False
        else:
            self.uf_print("Error - 1. Linear Offset not equal to EEPROM, Please retry.")
            self.uf_print("Error - 1. linear_offset(): {0}".format(self.read_linear_offset()))
            self.linear_calibration_start_flag = False

    def calibrate_linear_servo_offset(self, servo_number):
        global analog_read_pin, servo_analog_read
        angles = []
        analogs = []
        self.ab_values = []

        if servo_number == SERVO_BOTTOM:
            max_angle = 150
            min_angle = 30
            angle_step = min_angle
            analog_pin = SERVO_BOTTOM_ANALOG_PIN
            self.uarm.write_servo_angle(SERVO_BOTTOM, angle_step, False)
            self.uarm.write_servo_angle(SERVO_LEFT, 90, False)
            self.uarm.write_servo_angle(SERVO_RIGHT, 60, False)
        if servo_number == SERVO_LEFT:
            max_angle = 120
            min_angle = 35
            angle_step = min_angle
            analog_pin = SERVO_LEFT_ANALOG_PIN
            self.uarm.write_servo_angle(SERVO_BOTTOM, 90, False)
            self.uarm.write_servo_angle(SERVO_LEFT, angle_step, False)
            self.uarm.write_servo_angle(SERVO_RIGHT, 65, False)
        if servo_number == SERVO_RIGHT:
            max_angle = 120
            min_angle = 15
            angle_step = min_angle
            analog_pin = SERVO_RIGHT_ANALOG_PIN
            self.uarm.write_servo_angle(SERVO_BOTTOM, 90, False)
            self.uarm.write_servo_angle(SERVO_LEFT, 65, False)
            self.uarm.write_servo_angle(SERVO_RIGHT, angle_step, False)
        if servo_number == SERVO_HAND:
            max_angle = 160
            min_angle = 20
            angle_step = min_angle
            analog_pin = SERVO_HAND_ANALOG_PIN
            self.uarm.write_servo_angle(SERVO_BOTTOM, 90, False)
            self.uarm.write_servo_angle(SERVO_LEFT, 90, False)
            self.uarm.write_servo_angle(SERVO_RIGHT, 60, False)
            self.uarm.write_servo_angle(SERVO_HAND, angle_step, False)
        time.sleep(2)
        while angle_step < max_angle:

            self.uarm.write_servo_angle(servo_number, angle_step, False)

            servo_analog_read = 0
            for i in range(5):
                servo_analog_read += self.uarm.read_analog(analog_pin)
                time.sleep(0.05)

            servo_analog_read /= 5
            angles.append(angle_step)
            analogs.append(servo_analog_read)
            print ("Servo Number: {0}, Angle: {1}, Analog: {2}".format(servo_number, angle_step, servo_analog_read))
            angle_step += 1
            time.sleep(0.1)

        new_ab = basic_linear_regression(analogs, angles)

        linear_offset_template = copy.deepcopy(self.linear_offset_template)
        linear_offset_template['SLOPE'] = round(new_ab[0], 2)
        linear_offset_template['INTERCEPT'] = round(new_ab[1], 2)
        return linear_offset_template

    def manual_calibration_section(self, callback=None):
        self.uf_print("2.0. Clearing Servo Completed Flag in EEPROM.")
        self.write_completed_flag(CALIBRATION_SERVO_FLAG, False)
        self.uf_print("2. Start Calibrate Servo Offset")
        self.manual_operation_trigger = True
        self.uarm.write_servo_angle(SERVO_BOTTOM, 45, 0)
        time.sleep(1)
        self.uarm.write_left_right_servo_angle(130, 20, 0)
        time.sleep(1)
        self.uarm.detach_all_servos()
        time.sleep(0.3)

        time_counts = 0

        servo_1_offset = 0
        servo_2_offset = 0
        servo_3_offset = 0
        self.uf_print("Please move uArm in right position")
        self.uarm.alarm(3, 100, 100)
        while self.manual_operation_trigger:

            servo_1_offset = self.uarm.read_servo_angle(SERVO_BOTTOM, 0) - 45
            servo_2_offset = self.uarm.read_servo_angle(SERVO_LEFT, 0) - 130
            servo_3_offset = self.uarm.read_servo_angle(SERVO_RIGHT, 0) - 20

            if abs(servo_1_offset) < 5.5:
                self.manual_offset_correct_flag[0] = True
            else:
                self.manual_offset_correct_flag[0] = False
                # self.uf_print("Please try move the Servo 1")
            if abs(servo_2_offset) < 5.5:
                self.manual_offset_correct_flag[1] = True
            else:
                self.manual_offset_correct_flag[1] = False
                # self.uf_print("Please try move the Servo 2")
            if abs(servo_3_offset) < 5.5:
                self.manual_offset_correct_flag[2] = True
            else:
                self.manual_offset_correct_flag[2] = False
                # self.uf_print("Please try move the Servo 3")

            if time_counts > self.servo_calibrate_timeout:
                self.manual_operation_trigger = False
            time_counts += 1
            self.temp_manual_offset_arr[0] = servo_1_offset
            self.temp_manual_offset_arr[1] = servo_2_offset
            self.temp_manual_offset_arr[2] = servo_3_offset
            if self.manual_offset_correct_flag[0] & self.manual_offset_correct_flag[1] & \
                    self.manual_offset_correct_flag[2]:
                self.uf_print(str(self.servo_calibrate_timeout - time_counts) + ", Please Confirm the positions")
            if callback is not None:
                callback(self.temp_manual_offset_arr, self.manual_offset_correct_flag)
            else:
                confirm = raw_input(
                    "servo offset, bottom: {0}, left: {1}, right: {2},\nConfirm Please Press Y: ".format(servo_1_offset,servo_2_offset,servo_3_offset))
                if confirm == "Y" or confirm == "y":
                    self.manual_operation_trigger = False
            time.sleep(0.1)

        self.temp_manual_offset_arr[0] = round(servo_1_offset, 2)
        self.temp_manual_offset_arr[1] = round(servo_2_offset, 2)
        self.temp_manual_offset_arr[2] = round(servo_3_offset, 2)
        self.save_manual_offset()
        if self.read_manual_offset() == self.temp_manual_offset_arr:
            self.uf_print("    2.3 Mark Completed Flag in EEPROM")
            self.write_completed_flag(CALIBRATION_SERVO_FLAG, True)
        else:
            self.write_completed_flag(CALIBRATION_SERVO_FLAG, False)
            self.uf_print("Error - 2, Manual Calibration Servo offset not equal to EEPROM")
            self.uf_print("Error - 2, manual Servo Offset: {0}".format(self.temp_manual_offset_arr))
            self.uf_print("Error - 2, read_manual_offset: {0}".format(self.read_manual_offset()))
        self.uarm.attach_all_servos()

    def stretch_calibration_section(self):
        self.stretch_calibration_flag = True
        self.uf_print("3.0. Clearing Stretch Completed Flag in EEPROM.")
        self.write_completed_flag(CALIBRATION_STRETCH_FLAG, False)
        # self.uf_print("3. Start Calibrate Stretch Offset")
        #
        # self.uf_print("3.0 Moving uArm to Correct Place")
        # self.uarm.write_servo_angle(SERVO_BOTTOM, 45, 0)
        # time.sleep(1)
        # self.uarm.write_left_right_servo_angle(130, 20, 0)
        # time.sleep(1)
        #
        # initPosL = INIT_POS_L - 12
        # initPosR = INIT_POS_R - 12
        # minAngle_L = self.uarm.read_analog(SERVO_LEFT_ANALOG_PIN) - 16;
        # minAngle_R = self.uarm.read_analog(SERVO_RIGHT_ANALOG_PIN) - 16;
        # print ('minAngle_L: {0}'.format(minAngle_L))
        # print ('minAngle_R: {0}'.format(minAngle_R))
        #
        # self.uarm.write_servo_angle(SERVO_LEFT, initPosL, 0)
        # self.uarm.write_servo_angle(SERVO_RIGHT, initPosR, 0)
        # time.sleep(1)
        # while self.uarm.read_analog(SERVO_RIGHT_ANALOG_PIN) < (minAngle_R - SAMPLING_DEADZONE) \
        #         and self.stretch_calibration_flag:
        #     initPosR += 1
        #     self.uarm.write_servo_angle(SERVO_RIGHT, initPosR, 0)
        #     print ('initPosR: {0}'.format(initPosR))
        #     time.sleep(0.05)
        #
        # while self.uarm.read_analog(SERVO_RIGHT_ANALOG_PIN) > (minAngle_R + SAMPLING_DEADZONE) \
        #         and self.stretch_calibration_flag:
        #     initPosR -= 1
        #     self.uarm.write_servo_angle(SERVO_RIGHT, initPosR, 0)
        #     print ('initPosR: {0}'.format(initPosR))
        #     time.sleep(0.05)
        #
        # while self.uarm.read_analog(SERVO_LEFT_ANALOG_PIN) < (minAngle_L - SAMPLING_DEADZONE) \
        #         and self.stretch_calibration_flag:
        #     initPosL += 1
        #     self.uarm.write_servo_angle(SERVO_LEFT, initPosL, 0)
        #     print ('initPosL: {0}'.format(initPosL))
        #     time.sleep(0.05)
        #
        # while self.uarm.read_analog(SERVO_LEFT_ANALOG_PIN) > (minAngle_L + SAMPLING_DEADZONE) \
        #         and self.stretch_calibration_flag:
        #     initPosL -= 1
        #     self.uarm.write_servo_angle(SERVO_LEFT, initPosL, 0)
        #     print ('initPosL: {0}'.format(initPosL))
        #     time.sleep(0.05)
        #
        # offsetL = initPosL - INIT_POS_L + 3
        # offsetR = initPosR - INIT_POS_R + 3
        # offset_correct_flag = [False, False]
        # if abs(offsetL) < 20:
        #     offset_correct_flag[0] = True
        # if abs(offsetR) < 20:
        #     offset_correct_flag[1] = True
        #
        # stretch_offset = copy.deepcopy(self.stretch_offset_template)
        # stretch_offset['LEFT'] = offsetL
        # stretch_offset['RIGHT'] = offsetR
        # if callback is not None:
        #     callback(stretch_offset, offset_correct_flag)

        self.uf_print("    3.1 Saving Stretch Offset into EEPROM")
        self.uarm.write_eeprom(EEPROM_DATA_TYPE_FLOAT, OFFSET_STRETCH_START_ADDRESS, -10)
        self.uarm.write_eeprom(EEPROM_DATA_TYPE_FLOAT, OFFSET_STRETCH_START_ADDRESS + 4, -10)
        self.uf_print("    3.2 Mark Completed Flag in EEPROM")
        self.write_completed_flag(CALIBRATION_STRETCH_FLAG, True)
        # print offsetL, offsetR
        self.uarm.detach_all_servos()
        self.stretch_calibration_flag = False

    def save_linear_offset(self):
        self.uf_print("    1.2 Saving Servo Offset into EEPROM")
        intercept_address = LINEAR_INTERCEPT_START_ADDRESS
        slope_address = LINEAR_SLOPE_START_ADDRESS
        for i in range(4):
            print ("Intercept Address:{0}, Offset Value:{1}.".format(intercept_address, self.linear_offset[i]['INTERCEPT']))
            print ("Slope Address:{0}, Offset Value:{1}.".format(slope_address, self.linear_offset[i]['SLOPE']))
            self.uarm.write_eeprom(EEPROM_DATA_TYPE_FLOAT, intercept_address, self.linear_offset[i]['INTERCEPT'])
            time.sleep(0.5)
            self.uarm.write_eeprom(EEPROM_DATA_TYPE_FLOAT, slope_address, self.linear_offset[i]['SLOPE'])
            time.sleep(0.5)
            intercept_address += 4
            slope_address += 4

    def save_manual_offset(self):
        self.uf_print("    2.1 Saving Servo Offset into EEPROM")
        address = OFFSET_START_ADDRESS
        for i in self.temp_manual_offset_arr:
            self.uarm.write_eeprom(EEPROM_DATA_TYPE_FLOAT, address, i)
            address += 4

    def read_manual_offset(self):
        address = OFFSET_START_ADDRESS
        read_manual_offset = []
        for i in range(3):
            read_manual_offset.append(round(self.uarm.read_eeprom(EEPROM_DATA_TYPE_FLOAT, address), 2))
            address += 4
        return read_manual_offset

    def read_linear_offset(self):
        intercept_address = LINEAR_INTERCEPT_START_ADDRESS
        slope_address = LINEAR_SLOPE_START_ADDRESS
        linear_offset_data = []
        for i in range(4):
            linear_offset_template = copy.deepcopy(self.linear_offset_template)
            linear_offset_template['INTERCEPT'] = round(
                self.uarm.read_eeprom(EEPROM_DATA_TYPE_FLOAT, intercept_address), 2)
            linear_offset_template['SLOPE'] = round(self.uarm.read_eeprom(EEPROM_DATA_TYPE_FLOAT, slope_address), 2)
            linear_offset_data.append(linear_offset_template)
            intercept_address += 4
            slope_address += 4
        return linear_offset_data

    def read_stretch_offset(self):
        address = OFFSET_STRETCH_START_ADDRESS
        left_offset = round(self.uarm.read_eeprom(EEPROM_DATA_TYPE_FLOAT, address), 2)
        right_offset = round(self.uarm.read_eeprom(EEPROM_DATA_TYPE_FLOAT, address + 4), 2)
        stretch_offset = copy.deepcopy(self.stretch_offset_template)
        stretch_offset['LEFT'] = left_offset
        stretch_offset['RIGHT'] = right_offset
        return stretch_offset

    def init_calibration_completed_flag(self):
        self.is_all_calibrated = self.read_completed_flag(CALIBRATION_FLAG)
        self.is_linear_calibrated = self.read_completed_flag(CALIBRATION_LINEAR_FLAG)
        self.is_manual_calibrated = self.read_completed_flag(CALIBRATION_SERVO_FLAG)
        self.is_stretch_calibrated = self.read_completed_flag(CALIBRATION_STRETCH_FLAG)

    def write_completed_flag(self, flag_type, flag):
        if flag_type == CALIBRATION_FLAG:
            self.uarm.write_eeprom(EEPROM_DATA_TYPE_BYTE, CALIBRATION_FLAG, CONFIRM_FLAG if flag else 0)
        elif flag_type == CALIBRATION_LINEAR_FLAG:
            self.uarm.write_eeprom(EEPROM_DATA_TYPE_BYTE, CALIBRATION_LINEAR_FLAG, CONFIRM_FLAG if flag else 0)
        elif flag_type == CALIBRATION_SERVO_FLAG:
            self.uarm.write_eeprom(EEPROM_DATA_TYPE_BYTE, CALIBRATION_SERVO_FLAG, CONFIRM_FLAG if flag else 0)
        elif flag_type == CALIBRATION_STRETCH_FLAG:
            self.uarm.write_eeprom(EEPROM_DATA_TYPE_BYTE, CALIBRATION_STRETCH_FLAG, CONFIRM_FLAG if flag else 0)

    def read_completed_flag(self, flag_type):
        if flag_type == CALIBRATION_FLAG:
            if self.uarm.read_eeprom(EEPROM_DATA_TYPE_BYTE, CALIBRATION_FLAG) == CONFIRM_FLAG:
                return True
            else:
                return False
        elif flag_type == CALIBRATION_LINEAR_FLAG:
            if self.uarm.read_eeprom(EEPROM_DATA_TYPE_BYTE, CALIBRATION_LINEAR_FLAG) == CONFIRM_FLAG:
                return True
            else:
                return False
        elif flag_type == CALIBRATION_SERVO_FLAG:
            if self.uarm.read_eeprom(EEPROM_DATA_TYPE_BYTE, CALIBRATION_SERVO_FLAG) == CONFIRM_FLAG:
                return True
            else:
                return False
        elif flag_type == CALIBRATION_STRETCH_FLAG:
            if self.uarm.read_eeprom(EEPROM_DATA_TYPE_BYTE, CALIBRATION_STRETCH_FLAG) == CONFIRM_FLAG:
                return True
            else:
                return False


def basic_linear_regression(x, y):
    def float_data(a):
        for i in range(len(a)):
            a[i] = float(a[i])
        return a

    x = float_data(x)
    y = float_data(y)

    # Basic computations to save a little time.
    length = len(x)
    sum_x = sum(x)
    sum_y = sum(y)

    sum_x_squared = sum(map(lambda a: a * a, x))
    sum_of_products = sum([x[i] * y[i] for i in range(length)])

    # Magic formulae!
    a = (sum_of_products - (sum_x * sum_y) / length) / (sum_x_squared - ((sum_x ** 2) / length))
    b = (sum_y - a * sum_x) / length
    return a, b


def check_linear_is_correct(linear_offset):
    if linear_offset['SLOPE'] > 0.1 and linear_offset['INTERCEPT'] < 1:
        return True


def main():
    """
    uArm Calibration Library
        1. Linear Calibration section
          1.1 Write 20 times Angle to each Servo, in the meanwhile read the 20 times Servo Analog
          1.2 Using basic_linear_regression(analogs, angles) to generate the intercept & slope
              ``(In arduino library, angle = analog * INTERCEPT + SLOPE)``
          1.3 Save each servo linear offset in EEPROM (LINEAR_INTERCEPT_START_ADDRESS, LINEAR_SLOPE_START_ADDRESS)
          1.4 Mark Linear Calibration in EEPROM (CALIBRATION_LINEAR_FLAG)
         2. Manual Calibration section
          2.1 Set uArm at standard Angles. Left Angle - 130, Right Angle 30, Bottom Angle, 45.
          2.2 Put uArm into the calibration position.
          2.3 Confirm the Position.
         3. Stretch Calibration section
    """
    parser = argparse.ArgumentParser()
    # parser.add_argument("-d", "--download", help="download firmware into firmware.hex", action="store_true")
    parser.add_argument("-f", "--force", help="Force calibrate uArm, `all` , `linear`, `manual`")
    parser.add_argument("-c", "--check", help="Check If Calibration is completed? if completed, display the offset value", action="store_true")
    # parser.add_argument("-f", "--force", help="Will Force calibrate uArm", action="store_true")
    args = parser.parse_args()
    calibration = Calibration()
    time.sleep(2)
    # check
    if args.check:
        print ("\n");
        print ("-------------------------------------------------")
        print ("Checking Calibration information....")
        print ("-------------------------------------------------")
        is_linear_calibrated = calibration.read_completed_flag(CALIBRATION_LINEAR_FLAG)
        is_manual_calibrated = calibration.read_completed_flag(CALIBRATION_SERVO_FLAG)
        is_all_calibrated = calibration.read_completed_flag(CALIBRATION_FLAG)
        if is_linear_calibrated and is_manual_calibrated and is_all_calibrated:
            print ("Calibration All Completed !!!")
            linear_offset = calibration.read_linear_offset()
            print("Linear Offset:\n")
            print ("Bottom Servo, INTERCEPT: {0}, SLOPE: {1}".format(linear_offset[0]['INTERCEPT'],linear_offset[0]['SLOPE']))
            print ("Left Servo, INTERCEPT: {0}, SLOPE: {1}".format(linear_offset[1]['INTERCEPT'],linear_offset[1]['SLOPE']))
            print ("Right Servo, INTERCEPT: {0}, SLOPE: {1}".format(linear_offset[2]['INTERCEPT'],linear_offset[2]['SLOPE']))
            print ("Hand Servo, INTERCEPT: {0}, SLOPE: {1}".format(linear_offset[3]['INTERCEPT'],linear_offset[3]['SLOPE']))
            manual_offset = calibration.read_manual_offset()
            print("Manual Offset:\n")
            print ("Bottom Servo Offset: {0}".format(manual_offset[0]))
            print ("Left Servo Offset: {0}".format(manual_offset[1]))
            print ("Right Servo Offset: {0}".format(manual_offset[2]))
        elif is_linear_calibrated and is_manual_calibrated and not is_all_calibrated:
            print ("Calibration All Completed !!!")
        elif not is_linear_calibrated and is_manual_calibrated:
            print ("Linear Calibration not Completed !!!")
        elif is_linear_calibrated and not is_manual_calibrated:
            print ("Manual Calibration not Completed !!!")
        elif not is_linear_calibrated and not is_manual_calibrated:
            print ("Linear Calibration not Completed !!!")
            print ("Manual Calibration not Completed !!!")
        exit_fun()
    if args.force:
        print ("\n");
        print ("-------------------------------------------------")
        print ("Force Calibrating....")
        print ("-------------------------------------------------")
        if args.force == "all":
            calibration.calibrate_all()
        elif args.force == "linear":
            calibration.linear_calibration_section()
        elif args.force == "manual":
            if calibration.read_completed_flag(CALIBRATION_LINEAR_FLAG):
                calibration.manual_calibration_section()
            else:
                print ("Please Complete Linear Calibration First! You could use -f linear")
        else:
            print ("unrecognized command: {0}".format(args.force))
        exit_fun()

    # No Argument
    is_linear_calibrated = calibration.read_completed_flag(CALIBRATION_LINEAR_FLAG)
    is_manual_calibrated = calibration.read_completed_flag(CALIBRATION_SERVO_FLAG)
    is_all_calibrated = calibration.read_completed_flag(CALIBRATION_FLAG)
    if is_linear_calibrated and is_manual_calibrated and is_all_calibrated:
        print ("uArm has been calibrated already, Are you sure want to Calibrate it again?")
        confirm = raw_input("Press Y if you want to calibrate anyway...\n")
        if confirm == "Y" or confirm=="y":
            calibration.calibrate_all()
        else:
            exit_fun()
    else:
        calibration.calibrate_all()
    exit_fun()


def exit_fun():
    raw_input("\nPress Enter to Exit...")
    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        exit_fun()
