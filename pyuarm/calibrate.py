from pyuarm import *
import copy


INIT_POS_L = 139
INIT_POS_R = 26
SAMPLING_DEADZONE = 2

# uArm Calibration library
# 1. Linear Calibration section
#  1.1 Write 20 times Angle to each Servo, in the meanwhile read the 20 times Servo Analog
#  1.2 Using basic_linear_regression(analogs, angles) to generate the intercept & slope
#      (In arduino library, angle = analog * INTERCEPT + SLOPE)
#  1.3 Save each servo linear offset in EEPROM (LINEAR_INTERCEPT_START_ADDRESS, LINEAR_SLOPE_START_ADDRESS)
#  1.4 Mark Linear Calibration in EEPROM (CALIBRATION_LINEAR_FLAG)
# 2. Manual Calibration section
#  2.1
# 3. Stretch Calibration section


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
        elif len(list_uarms()) > 0:
            self.uarm = get_uarm()
        else:
            raise ValueError('No available uArm Founds')

        if log_function is not None:
            self.log_function = log_function
        else:
            self.log_function = self.default_log
        self.servo_calibrate_timeout = 300
        self.is_all_calibrated = False
        self.is_linear_calibrated = False
        self.is_manual_calibrated = False
        self.is_stretch_calibrated = False

    def default_log(self, msg):
        print msg

    def uf_print(self, msg):
        self.log_function(msg)

    def calibrate_all(self, linear_callback=None, manual_callback=None, stretch_callback=None):
        self.uf_print("0. Clearing Completed Flag in EEPROM.")
        self.write_completed_flag(CALIBRATION_FLAG, False)

        if linear_callback is None:  # If not provide callback function use default
            self.linear_calibration_section(None)
        else:
            linear_callback()

        if self.read_completed_flag(CALIBRATION_LINEAR_FLAG):
            if manual_callback is None:  # If not provide callback function use default
                self.manual_calibration_section(None)
            else:
                manual_callback()
            time.sleep(0.5)

        if self.read_completed_flag(CALIBRATION_SERVO_FLAG):
            if stretch_callback is None:  # If not provide callback function use default
                self.stretch_calibration_section(None)
            else:
                stretch_callback()
            time.sleep(0.5)

        if self.read_completed_flag(CALIBRATION_STRETCH_FLAG):
            self.write_completed_flag(CALIBRATION_FLAG, True)
            self.uf_print("Calibration DONE!!")

    def linear_calibration_section(self, callback=None):
        self.linear_calibration_start_flag = True
        self.uf_print("1.0. Clearing Linear Completed Flag in EEPROM.")
        self.write_completed_flag(CALIBRATION_LINEAR_FLAG, False)
        self.uf_print("1. Start Calibrate Linear Offset")
        for i in range(4):
            self.uf_print("    1.1." + str(i) + " Linear Offset - Servo " + str(i))
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
            # self.uf_print("    1.4 Disconnecting uArm to load offset")
            # self.uarm.disconnect()  # reconnect to load offset
            # time.sleep(1)
            # self.uf_print("    1.5 Reconnecting, Please wait...")
            # self.uarm.reconnect()
            self.linear_calibration_start_flag = False
        else:
            self.uf_print("Error - 1. Linear Offset not equal to EEPROM, Please retry.")
            # self.uf_print("Error - 1. manual_offset: " + self.temp_manual_offset_arr)
            self.uf_print("Error - 1. linear_offset(): " + self.read_linear_offset())
            self.linear_calibration_start_flag = False
        self.uarm.detach_all_servos()

    def calibrate_linear_servo_offset(self, number):
        moveTimes = 5
        ServoRangeIni = 20
        ServoRangeFin = 100
        angle_step = 0

        angles = []
        analogs = []
        self.ab_values = []
        while angle_step < ((ServoRangeFin - ServoRangeIni) / moveTimes + 1):
            angle = angle_step * moveTimes + ServoRangeIni
            if number == SERVO_ROT_NUM:
                analog_read_pin = SERVO_ROT_ANALOG_PIN
                self.uarm.write_servo_angle(SERVO_ROT_NUM, angle, 0)
                self.uarm.write_left_right_servo_angle(60, 30, 0)

            if number == SERVO_LEFT_NUM:
                analog_read_pin = SERVO_LEFT_ANALOG_PIN
                self.uarm.write_servo_angle(SERVO_ROT_NUM, 90, 0)
                self.uarm.write_left_right_servo_angle(angle, 30, 0)

            if number == SERVO_RIGHT_NUM:
                analog_read_pin = SERVO_RIGHT_ANALOG_PIN
                self.uarm.write_servo_angle(SERVO_ROT_NUM, 90, 0)
                self.uarm.write_left_right_servo_angle(30, angle, 0)

            if number == SERVO_HAND_ROT_NUM:
                analog_read_pin = SERVO_HAND_ROT_ANALOG_PIN
                self.uarm.write_servo_angle(SERVO_ROT_NUM, 90, 0)
                self.uarm.write_left_right_servo_angle(30, 60, 0)
                self.uarm.write_servo_angle(SERVO_HAND_ROT_NUM, angle, 0)

            if angle_step == 0:
                time.sleep(0.5)
            else:
                time.sleep(0.1)

            for i in range(2):
                servo_analog_read = self.uarm.read_analog(analog_read_pin)
                time.sleep(0.1)

            angles.append(angle)
            analogs.append(servo_analog_read)
            angle_step += 1
            time.sleep(0.2)

        new_ab = basic_linear_regression(analogs, angles)
        linear_offset_template = copy.deepcopy(self.linear_offset_template)
        linear_offset_template['SLOPE'] = round(new_ab[0], 2)
        linear_offset_template['INTERCEPT'] = round(new_ab[1], 2)
        return linear_offset_template
        # print new_ab[0]
        # print new_ab[1]
        # self.ab_values_a.append(new_ab[0])
        # self.ab_values_b.append(new_ab[1])
        # self.complete_display(number,'linear')

    def manual_calibration_section(self, callback=None):
        self.uf_print("2.0. Clearing Servo Completed Flag in EEPROM.")
        self.write_completed_flag(CALIBRATION_SERVO_FLAG, False)
        self.uf_print("2. Start Calibrate Servo Offset")
        self.manual_operation_trigger = True
        self.uarm.write_servo_angle(SERVO_ROT_NUM, 45, 0)
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
        while self.manual_operation_trigger:

            servo_1_offset = self.uarm.read_servo_angle(SERVO_ROT_NUM, 0) - 45
            servo_2_offset = self.uarm.read_servo_angle(SERVO_LEFT_NUM, 0) - 130
            servo_3_offset = self.uarm.read_servo_angle(SERVO_RIGHT_NUM, 0) - 20

            if abs(servo_1_offset) < 5.5:
                self.manual_offset_correct_flag[0] = True
            else:
                self.manual_offset_correct_flag[0] = False
                self.uf_print("Please try move the Servo 1")
            if abs(servo_2_offset) < 5.5:
                self.manual_offset_correct_flag[1] = True
            else:
                self.manual_offset_correct_flag[1] = False
                self.uf_print("Please try move the Servo 2")
            if abs(servo_3_offset) < 5.5:
                self.manual_offset_correct_flag[2] = True
            else:
                self.manual_offset_correct_flag[2] = False
                self.uf_print("Please try move the Servo 3")

            if time_counts > self.servo_calibrate_timeout:
                self.manual_operation_trigger = False
            time_counts += 1
            self.temp_manual_offset_arr[0] = servo_1_offset
            self.temp_manual_offset_arr[1] = servo_2_offset
            self.temp_manual_offset_arr[2] = servo_3_offset
            if self.manual_offset_correct_flag[0] & self.manual_offset_correct_flag[1] & self.manual_offset_correct_flag[2]:
                self.uf_print(str(self.servo_calibrate_timeout - time_counts) + ", Please Confirm the positions")
            if callback is not None:
                callback(self.temp_manual_offset_arr, self.manual_offset_correct_flag)
            time.sleep(0.1)

        # if self.manual_offset_correct_flag[0] & self.manual_offset_correct_flag[1] & self.manual_offset_correct_flag[2]:
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
            self.uf_print("Error - 2, manual Servo Offset: ", self.temp_manual_offset_arr)
            self.uf_print("Error - 2, read_manual_offset: ", self.read_manual_offset())
        self.uarm.detach_all_servos()

    def stretch_calibration_section(self, callback=None):
        self.stretch_calibration_flag = True
        self.uf_print("3.0. Clearing Stretch Completed Flag in EEPROM.")
        self.write_completed_flag(CALIBRATION_STRETCH_FLAG, False)
        self.uf_print("3. Start Calibrate Stretch Offset")

        self.uf_print("3.0 Moving uArm to Correct Place")
        self.uarm.write_servo_angle(SERVO_ROT_NUM, 45, 0)
        time.sleep(1)
        self.uarm.write_left_right_servo_angle(130, 20, 0)
        time.sleep(1)

        initPosL = INIT_POS_L - 12
        initPosR = INIT_POS_R - 12
        minAngle_L = self.uarm.read_analog(SERVO_LEFT_ANALOG_PIN) - 16;
        minAngle_R = self.uarm.read_analog(SERVO_RIGHT_ANALOG_PIN) - 16;
        print 'minAngle_L: ', minAngle_L
        print 'minAngle_R: ', minAngle_R

        self.uarm.write_servo_angle(SERVO_LEFT_NUM, initPosL, 0)
        self.uarm.write_servo_angle(SERVO_RIGHT_NUM, initPosR, 0)
        time.sleep(1)
        while self.uarm.read_analog(SERVO_RIGHT_ANALOG_PIN) < (minAngle_R - SAMPLING_DEADZONE) \
                and self.stretch_calibration_flag:
            initPosR += 1
            self.uarm.write_servo_angle(SERVO_RIGHT_NUM, initPosR, 0)
            print 'initPosR: ', initPosR
            time.sleep(0.05)

        while self.uarm.read_analog(SERVO_RIGHT_ANALOG_PIN) > (minAngle_R + SAMPLING_DEADZONE) \
                and self.stretch_calibration_flag:
            initPosR -= 1
            self.uarm.write_servo_angle(SERVO_RIGHT_NUM, initPosR, 0)
            print 'initPosR: ', initPosR
            time.sleep(0.05)

        while self.uarm.read_analog(SERVO_LEFT_ANALOG_PIN) < (minAngle_L - SAMPLING_DEADZONE) \
                and self.stretch_calibration_flag:
            initPosL += 1
            self.uarm.write_servo_angle(SERVO_LEFT_NUM, initPosL, 0)
            print 'initPosL: ', initPosL
            time.sleep(0.05)

        while self.uarm.read_analog(SERVO_LEFT_ANALOG_PIN) > (minAngle_L + SAMPLING_DEADZONE) \
                and self.stretch_calibration_flag:
            initPosL -= 1
            self.uarm.write_servo_angle(SERVO_LEFT_NUM, initPosL, 0)
            print 'initPosL: ', initPosL
            time.sleep(0.05)

        offsetL = initPosL - INIT_POS_L + 3
        offsetR = initPosR - INIT_POS_R + 3
        offset_correct_flag = [False, False]
        if abs(offsetL) < 20:
            offset_correct_flag[0] = True
        if abs(offsetR) < 20:
            offset_correct_flag[1] = True

        stretch_offset = copy.deepcopy(self.stretch_offset_template)
        stretch_offset['LEFT'] = offsetL
        stretch_offset['RIGHT'] = offsetR
        if callback is not None:
            callback(stretch_offset, offset_correct_flag)

        self.uf_print("    3.1 Saving Stretch Offset into EEPROM")
        self.uarm.write_eeprom(EEPROM_DATA_TYPE_FLOAT, OFFSET_STRETCH_START_ADDRESS, offsetL)
        self.uarm.write_eeprom(EEPROM_DATA_TYPE_FLOAT, OFFSET_STRETCH_START_ADDRESS + 4, offsetR)
        self.uf_print("    3.2 Mark Completed Flag in EEPROM")
        self.write_completed_flag(CALIBRATION_STRETCH_FLAG, True)
        print offsetL, offsetR
        self.uarm.detach_all_servos()
        self.stretch_calibration_flag = False

    def save_linear_offset(self):
        self.uf_print("    1.2 Saving Servo Offset into EEPROM")
        intercept_address = LINEAR_INTERCEPT_START_ADDRESS
        slope_address = LINEAR_SLOPE_START_ADDRESS
        for i in range(4):
            print intercept_address, self.linear_offset[i]['INTERCEPT']
            print slope_address, self.linear_offset[i]['SLOPE']
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
            linear_offset_template['INTERCEPT'] = round(self.uarm.read_eeprom(EEPROM_DATA_TYPE_FLOAT, intercept_address), 2)
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
    calibration = Calibration(get_uarm())
    calibration.calibrate_all()

if __name__ == '__main__':
    main()
