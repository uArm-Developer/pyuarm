import sys
import serial
import time
import datetime
from uarm4py import *
import copy


LINEAR_OFFSET = 1
SERVO_OFFSET = 2
STRETCH_OFFSET = 3

def basic_linear_regression(x, y):

    def float_data(x):
        for i in range(len(x)):
            x[i] = float(x[i])
        return x

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

class uArmCalibration(object):

    manual_operation_trigger = True

    linear_data = {"INTERCEPT":0.00, "SLOPE":0.00}
    linear_offset = [linear_data,linear_data,linear_data,linear_data]
    servo_offset = [0.00,0.00,0.00]
    stretch_offset = {"LEFT":0.00, "RIGHT":0.00}

    def __init__(self,uarm):
        self.uarm = uarm

    def calibrate(self):
        print "0. Clearing Completed Flag in EEPROM."
        self.uarm.writeEEPROM(EEPROM_DATA_TYPE_BYTE, CALIBRATION_LINEAR_FLAG, 0)
        self.uarm.writeEEPROM(EEPROM_DATA_TYPE_BYTE, CALIBRATION_SERVO_FLAG, 0)
        self.uarm.writeEEPROM(EEPROM_DATA_TYPE_BYTE, CALIBRATION_STRETCH_FLAG, 0)
        self.uarm.writeEEPROM(EEPROM_DATA_TYPE_BYTE, CALIBRATION_FLAG, 0)
        print "1. Start Calibrate Linear Offset"
        for i in range(4):
            print "    1.1." + str(i) + " Linear Offset - Servo " + str(i)
            self.linear_offset[i] = self.calibrate_linear_offset(i)
        self.saveLinearOffset()
        if self.readLinearOffset() == self.linear_offset:
            print "    1.3 Mark Completed Flag in EEPROM"
            self.uarm.writeEEPROM(EEPROM_DATA_TYPE_BYTE, CALIBRATION_LINEAR_FLAG, CALIBRATION_LINEAR_FLAG)
            print "    1.4 Disconnecting uArm to load offset"
            self.uarm.disconnect() # reconnect to load offset
            time.sleep(1)
            print "    1.5 Reconnecting, Please wait..."
            self.uarm.reconnect()
        else:
            print "Error - 1. Linear Offset not equal to EEPROM, Please retry."
            print "Error - 1.servo_offset: ", self.servo_offset
            print "Error - 1.readLinearOffset(): ", self.readLinearOffset()
        if self.uarm.readEEPROM(EEPROM_DATA_TYPE_BYTE, CALIBRATION_LINEAR_FLAG) == CALIBRATION_LINEAR_FLAG:
            self.calibrate_servo_offset()
            time.sleep(0.5)
        if self.uarm.readEEPROM(EEPROM_DATA_TYPE_BYTE, CALIBRATION_SERVO_FLAG) == CALIBRATION_SERVO_FLAG:
            self.calibrate_stretch_servo_offset()
            time.sleep(0.5)
        if self.uarm.readEEPROM(EEPROM_DATA_TYPE_BYTE, CALIBRATION_STRETCH_FLAG) == CALIBRATION_STRETCH_FLAG:
            self.uarm.writeEEPROM(EEPROM_DATA_TYPE_BYTE, CALIBRATION_FLAG, CALIBRATION_FLAG)
            print "Calibration DONE!!"


    def calibrate_linear_offset(self,number):
        moveTimes = 5
        ServoRangeIni = 20
        ServoRangeFin = 100
        angle_step = 0

        angles = []
        analogs = []
        self.ab_values = []
        while angle_step < ((ServoRangeFin-ServoRangeIni)/moveTimes+1):
            angle = angle_step*moveTimes + ServoRangeIni
            if number == SERVO_ROT_NUM:
                analog_read_pin = SERVO_ROT_ANALOG_PIN
                self.uarm.writeServoAngle(SERVO_ROT_NUM,angle,0)
                self.uarm.writeLeftRightServoAngle(60,30,0)

            if number == SERVO_LEFT_NUM:
                analog_read_pin = SERVO_LEFT_ANALOG_PIN
                self.uarm.writeServoAngle(SERVO_ROT_NUM,90,0)
                self.uarm.writeLeftRightServoAngle(angle,30,0)

            if number == SERVO_RIGHT_NUM:
                analog_read_pin = SERVO_RIGHT_ANALOG_PIN
                self.uarm.writeServoAngle(SERVO_ROT_NUM,90,0)
                self.uarm.writeLeftRightServoAngle(30,angle,0)

            if number == SERVO_HAND_ROT_NUM:
                analog_read_pin = SERVO_HAND_ROT_ANALOG_PIN
                self.uarm.writeServoAngle(SERVO_ROT_NUM,90,0)
                self.uarm.writeLeftRightServoAngle(30,60,0)
                self.uarm.writeServoAngle(SERVO_HAND_ROT_NUM,angle,0)

            if angle_step == 0:
                time.sleep(0.5)
            else:
                time.sleep(0.1)

            for i in range(2):
                servo_analog_read = self.uarm.readAnalog(analog_read_pin)
                time.sleep(0.1)

            angles.append(angle)
            analogs.append(servo_analog_read)
            angle_step += 1
            time.sleep(0.2)

        new_ab = basic_linear_regression(analogs,angles)
        linear_data = copy.deepcopy(self.linear_data)
        linear_data['SLOPE'] = round(new_ab[0],2)
        linear_data['INTERCEPT'] = round(new_ab[1],2)
        return linear_data
        # print new_ab[0]
        # print new_ab[1]
        # self.ab_values_a.append(new_ab[0])
        # self.ab_values_b.append(new_ab[1])
        # self.complete_display(number,'linear')

    def calibrate_servo_offset(self):
        print "2. Start Calibrate Servo Offset"
        self.manual_operation_trigger = True
        self.uarm.writeServoAngle(SERVO_ROT_NUM,45,0)
        time.sleep(1)
        self.uarm.writeLeftRightServoAngle(130, 20,0)
        time.sleep(1)
        self.uarm.detachAll()
        time.sleep(0.3)

        time_counts = 0

        servo_1_offset = 0
        servo_2_offset = 0
        servo_3_offset = 0
        while self.manual_operation_trigger:

            servo_1_offset = self.uarm.readServoAngle(SERVO_ROT_NUM,0) - 45
            servo_2_offset = self.uarm.readServoAngle(SERVO_LEFT_NUM,0) - 130
            servo_3_offset = self.uarm.readServoAngle(SERVO_RIGHT_NUM,0) - 20

            # if self.manual_operation_trigger:
            #     for i in range(3):
            #         self.complete_display(i+1,'offset')

            if abs(servo_1_offset) < 5.5:
                servo_1_count = True
                # self.servo_1_offset_signal.setStyleSheet(self.style_circle_green)
            else:
                servo_1_count = False
                # self.servo_1_offset_signal.setStyleSheet(self.style_circle_yellow)
            if abs(servo_2_offset) < 5.5:
                servo_2_count = True
                # self.servo_2_offset_signal.setStyleSheet(self.style_circle_green)
            else:
                servo_2_count = False
                # self.servo_2_offset_signal.setStyleSheet(self.style_circle_yellow)
            if abs(servo_3_offset) < 5.5:
                servo_3_count = True
                # self.servo_3_offset_signal.setStyleSheet(self.style_circle_green)
            else:
                servo_3_count = False
                # self.servo_3_offset_signal.setStyleSheet(self.style_circle_yellow)

            # self.servo_count_all = servo_1_count+servo_2_count+servo_3_count
            # self.hand_progress_bar.setValue(self.servo_count_all*33+1)

            if time_counts > 100:
                self.manual_operation_trigger = False
            time_counts += 1
            time.sleep(0.1)

            print servo_1_count, servo_2_count, servo_3_count
            print servo_1_offset, servo_2_offset, servo_3_offset
        if servo_1_count & servo_2_count & servo_3_count :
            self.servo_offset[0] = round(servo_1_offset,2)
            self.servo_offset[1] = round(servo_2_offset,2)
            self.servo_offset[2] = round(servo_3_offset,2)
            self.saveServoOffset()
            if self.readServoOffset() == self.servo_offset:
                print "    2.3 Mark Completed Flag in EEPROM"
                self.uarm.writeEEPROM(EEPROM_DATA_TYPE_BYTE, CALIBRATION_SERVO_FLAG, CALIBRATION_SERVO_FLAG)
            else:
                print "Error - 2, servo offset not equal to EEPROM"
                print "Error - 2, servo_offset: ", self.servo_offset
                print "Error - 2, readServoOffset: ", self.readServoOffset()

    def calibrate_stretch_servo_offset(self):
        print "3. Start Calibrate Stretch Offset"
        INIT_POS_L = 139
        INIT_POS_R = 26
        SAMPLING_DEADZONE = 2

        initPosL = INIT_POS_L - 12
        initPosR = INIT_POS_R - 12
        minAngle_L = self.uarm.readAnalog(SERVO_LEFT_ANALOG_PIN) - 16;
        minAngle_R = self.uarm.readAnalog(SERVO_RIGHT_ANALOG_PIN) - 16;
        print 'minAngle_L: ', minAngle_L
        print 'minAngle_R: ', minAngle_R

        self.uarm.writeServoAngle(SERVO_LEFT_NUM, initPosL, 0)
        self.uarm.writeServoAngle(SERVO_RIGHT_NUM, initPosR, 0)
        time.sleep(1)
        while self.uarm.readAnalog(SERVO_RIGHT_ANALOG_PIN) < (minAngle_R - SAMPLING_DEADZONE):
            initPosR = initPosR + 1
            self.uarm.writeServoAngle(SERVO_RIGHT_NUM, initPosR, 0 )
            print 'initPosR: ', initPosR
            time.sleep(0.05)

        while self.uarm.readAnalog(SERVO_RIGHT_ANALOG_PIN) > (minAngle_R + SAMPLING_DEADZONE):
            initPosR = initPosR - 1
            self.uarm.writeServoAngle(SERVO_RIGHT_NUM, initPosR, 0 )
            print 'initPosR: ', initPosR
            time.sleep(0.05)

        while self.uarm.readAnalog(SERVO_LEFT_ANALOG_PIN) < (minAngle_L - SAMPLING_DEADZONE):
            initPosL = initPosL + 1
            self.uarm.writeServoAngle(SERVO_LEFT_NUM, initPosL, 0 )
            print 'initPosL: ', initPosL
            time.sleep(0.05)

        while self.uarm.readAnalog(SERVO_LEFT_ANALOG_PIN) > (minAngle_L + SAMPLING_DEADZONE):
            initPosL = initPosL - 1
            self.uarm.writeServoAngle(SERVO_LEFT_NUM, initPosL, 0 )
            print 'initPosL: ', initPosL
            time.sleep(0.05)

        offsetL = initPosL - INIT_POS_L + 3
        offsetR = initPosR - INIT_POS_R + 3
        print "    3.1 Saving Stretch Offset into EEPROM"
        self.uarm.writeEEPROM(EEPROM_DATA_TYPE_FLOAT, OFFSET_STRETCH_START_ADDRESS, offsetL)
        self.uarm.writeEEPROM(EEPROM_DATA_TYPE_FLOAT, OFFSET_STRETCH_START_ADDRESS + 4, offsetR)
        print "    3.2 Mark Completed Flag in EEPROM"
        self.uarm.writeEEPROM(EEPROM_DATA_TYPE_BYTE, CALIBRATION_STRETCH_FLAG, CALIBRATION_STRETCH_FLAG)
        print offsetL,offsetR


    def saveLinearOffset(self):
        print "    1.2 Saving Servo Offset into EEPROM"
        intercept_address = LINEAR_INTERCEPT_START_ADDRESS
        slope_address = LINEAR_SLOPE_START_ADDRESS
        for i in range(4):
            print intercept_address, self.linear_offset[i]['INTERCEPT']
            print slope_address, self.linear_offset[i]['SLOPE']
            self.uarm.writeEEPROM(EEPROM_DATA_TYPE_FLOAT, intercept_address, self.linear_offset[i]['INTERCEPT'])
            time.sleep(0.5)
            self.uarm.writeEEPROM(EEPROM_DATA_TYPE_FLOAT, slope_address, self.linear_offset[i]['SLOPE'])
            time.sleep(0.5)
            intercept_address = intercept_address + 4
            slope_address = slope_address + 4

    def saveServoOffset(self):
        print "    2.1 Saving Servo Offset into EEPROM"
        address = OFFSET_START_ADDRESS
        for i in self.servo_offset:
            self.uarm.writeEEPROM(EEPROM_DATA_TYPE_FLOAT, address, i)
            address = address + 4

    def readServoOffset(self):
        address = OFFSET_START_ADDRESS
        read_servo_offset = []
        for i in range(3):
            read_servo_offset.append(round(self.uarm.readEEPROM(EEPROM_DATA_TYPE_FLOAT, address),2))
            address = address + 4
        return read_servo_offset

    def readLinearOffset(self):
        intercept_address = LINEAR_INTERCEPT_START_ADDRESS
        slope_address = LINEAR_SLOPE_START_ADDRESS
        read_linear_offset = []
        for i in range(4):
            linear_data = copy.deepcopy(self.linear_data);
            linear_data['INTERCEPT'] = round(self.uarm.readEEPROM(EEPROM_DATA_TYPE_FLOAT, intercept_address),2)
            linear_data['SLOPE'] = round(self.uarm.readEEPROM(EEPROM_DATA_TYPE_FLOAT, slope_address),2)
            read_linear_offset.append(linear_data);
            intercept_address = intercept_address + 4
            slope_address = slope_address + 4
        return read_linear_offset
