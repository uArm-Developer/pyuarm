from __future__ import print_function
import serial
import time
import binascii

from util import *
from distutils.version import LooseVersion
from version import support_versions


class uArm(object):
    """
    **uArm** class is let you make an instance for uArm.

    eg.

    ::

        >>> import pyuarm
        >>> uarm = pyuarm.uArm()
        Initialize uArm, port is /dev/cu.usbserial-A600CVS1...
        Firmware Version: 1.5.11

    :param port: uArm Port name, Default is **None**

    :param debug: Debug Mode Control Flag, If debug is **True**, Will display all in/out serial message(in Hex Format)

    :param timeout: Serial Timeout parameter, Default is **5** Seconds.

    :raise NoUArmPortException: No uArm available
    :raise UnknownFirmwareException: unrecognized firmware version
    """

    def __init__(self, port=None, debug=False, timeout=5):

        if port is None:
            ports = uarm_ports()
            if len(ports) > 0:
                port = ports[0]
            else:
                raise NoUArmPortException("No uArm is connected.")
        self.port = port
        self.debug = debug
        print("Initialize uArm, port is {0}...".format(self.port))
        self.sp = serial.Serial(port, baudrate=57600, timeout=timeout)
        time.sleep(3)
        try:
            self.get_firmware_version()
            print("Firmware Version: {0}".format(self.firmware_version))
        except TypeError as e:
            raise UnknownFirmwareException(
                "Unknown Firmware Version, Please use 'python -m pyuarm.tools.firmware_helper' upgrade your firmware")

        for v in support_versions:
            if LooseVersion(v) == LooseVersion(str(self.firmware_major_version) + "." + str(self.firmware_minor_version)):
                return
        raise UnSupportedFirmwareVersionException('Unsupported firmware version: {0}, Please flash the support version {1}'.format(self.firmware_version, support_versions))

    def is_connected(self):
        """
        This function will detect if uArm is connected

        :returns: True - Connected, False - Disconnected
        """
        if not self.sp.isOpen():
            return False
        else:
            return True

    def disconnect(self):
        """
        Close serial connection and release the uArm Port.
        """
        self.sp.close()

    def reconnect(self):
        """
        Reconnect serial connection with uArm Port.
        """
        if not self.is_connected():
            self.sp.open()
            self.get_firmata_version()
            self.get_firmware_version()

    def get_firmata_version(self):
        """
        Read frimata version after initialize the uArm.
        """
        while self.sp.readable():
            read_byte = self.serial_read()
            if read_byte == END_SYSEX:
                break
            if read_byte == START_SYSEX:
                read_byte = self.serial_read()
                if read_byte == REPORT_FIRMATA_VERSION:
                    frimata_major_version = self.serial_read()
                    frimata_minor_version = self.serial_read()
                    self.firmata_version = str(frimata_major_version) + "." + str(frimata_minor_version)

    def read_servo_angle(self, servo_number=None, with_offset=True):
        """
        Read Servo Angle from servo_number,
        if servo_number is None, will return all servo angles (SERVO_BOTTOM, SERVO_LEFT, SERVO_RIGHT, SERVO_HAND).

        eg.

        ::

            >>> import pyuarm
            >>> uarm = pyuarm.uArm(debug=True)
            Initialize uArm, port is /dev/cu.usbserial-A600CRCD...
            f925Serial Read: f079135504107206d04606907206d06107406102e06906e06f0f7
            Serial Write:f0aa23f7
            Serial Read: f0aa2315bf7
            Firmware Version: 1.5.11
            >>> uarm.read_servo_angle(pyuarm.SERVO_BOTTOM)
            Serial Write:f0aa100001f7
            Serial Read: f0aa05c034f7
            92.52
            >>> uarm.read_servo_angle(pyuarm.SERVO_BOTTOM,False)
            Serial Write:f0aa100000f7
            Serial Read: f0aa058015f7
            88.21
            >>> uarm.read_servo_angle()
            Serial Write: f0aa100001f7
            Serial Read: f0aa00270016f7
            Serial Write: f0aa100101f7
            Serial Read: f0aa016a0037f7
            Serial Write: f0aa100201f7
            Serial Read: f0aa02140000f7
            Serial Write: f0aa100301f7
            Serial Read: f0aa0306004bf7
            [39.22, 106.55, 20.0, 6.75]

        :param servo_number:    SERVO_BOTTOM
                                SERVO_LEFT
                                SERVO_RIGHT
                                SERVO_RIGHT
        :param with_offset: default - True

        """
        if servo_number is not None:

            msg = bytearray([START_SYSEX, UARM_CODE, READ_ANGLE])
            msg.extend(getOne7BitBytesFloatArray(servo_number))

            msg.extend(getOne7BitBytesFloatArray(1 if with_offset else 0))
            msg.append(END_SYSEX)
            self.serial_write(msg)
            while self.sp.readable():
                read_byte = self.serial_read()
                received_data = []
                if read_byte == START_SYSEX:
                    read_byte = self.serial_read()
                    if read_byte == UARM_CODE:
                        read_byte = self.serial_read()
                        while read_byte != END_SYSEX:
                            received_data.append(read_byte)
                            read_byte = self.serial_read()
                        if received_data[0] == servo_number:
                            return received_data[2] * 128 + received_data[1] + received_data[3] / 100.00
        else:
            servo_angles = [self.read_servo_angle(SERVO_BOTTOM, with_offset),
                            self.read_servo_angle(SERVO_LEFT, with_offset),
                            self.read_servo_angle(SERVO_RIGHT, with_offset),
                            self.read_servo_angle(SERVO_HAND, with_offset)]
            return servo_angles


    def read_eeprom(self, data_type, eeprom_address):
        """
        Read data from EEPROM

        Byte: 1 Byte

        Integer: 2 Bytes

        Float: 4 Bytes

        Please reference Arduino EEPROMGet_.

        .. _EEPROMGet: https://www.arduino.cc/en/Reference/EEPROMGet

        :param data_type:   EEPROM_DATA_TYPE_BYTE

                            EEPROM_DATA_TYPE_FLOAT

                            EEPROM_DATA_TYPE_INTEGER

        :param eeprom_address: EEPROM Address
        :returns: byte, integer, float
        """
        msg = bytearray([START_SYSEX, UARM_CODE, READ_EEPROM])
        msg.append(data_type)
        msg.extend(getTwo7BitBytesIntegerArray(eeprom_address))
        msg.append(END_SYSEX)

        self.serial_write(msg)
        while self.sp.readable():
            read_byte = self.serial_read()
            received_data = []
            if read_byte == START_SYSEX:
                read_byte = self.serial_read()
                if read_byte == UARM_CODE:
                    read_byte = self.serial_read()
                    if read_byte == READ_EEPROM:
                        read_byte = self.serial_read()
                        while read_byte != END_SYSEX:
                            received_data.append(read_byte)
                            read_byte = self.serial_read()
                        res_eeprom_add = received_data[1] * 128 + received_data[0]
                        if res_eeprom_add == eeprom_address:
                            if data_type == EEPROM_DATA_TYPE_BYTE:
                                return (received_data[3] << 7) + received_data[2]
                            if data_type == EEPROM_DATA_TYPE_FLOAT:
                                val = (received_data[4] << 7) + received_data[3] + float(received_data[5]) / 100.00
                                val = val if received_data[2] == 0 else -val
                                return val
                            if data_type == EEPROM_DATA_TYPE_INTEGER:
                                val = (received_data[4] << 7) + received_data[3]
                                val = val if received_data[2] == 0 else -val
                                return val

    def read_digital(self, pin_num, pin_mode):
        """
        Read Digital from PIN

        Please reference Arduino DigitalPINs_.

        .. _DigitalPINs: https://www.arduino.cc/en/Tutorial/DigitalPins

        :param pin_num: Integer 1 to 13
        :param pin_mode: PULL_UP, INPUT
        :returns: Digital Value - HIGH, LOW

        """
        msg = bytearray([START_SYSEX, UARM_CODE, READ_DIGITAL])
        msg.extend(getOne7BitBytesFloatArray(pin_num))
        msg.extend(getOne7BitBytesFloatArray(pin_mode))
        msg.append(END_SYSEX)

        self.serial_write(msg)
        while self.sp.readable():
            read_byte = self.serial_read()
            received_data = []
            if read_byte == START_SYSEX:
                read_byte = self.serial_read()
                if read_byte == UARM_CODE:
                    read_byte = self.serial_read()
                    while read_byte != END_SYSEX:
                        received_data.append(read_byte)
                        read_byte = self.serial_read()
                    if received_data[0] == pin_num:
                        return received_data[1]

    def read_analog(self, pin_num):
        """
        Read Analog from PIN

        Please reference Arduino AnalogRead_.

        .. _AnalogRead: https://www.arduino.cc/en/Reference/AnalogRead

        :param pin_num: Integer 1 to 13
        :returns: Analog Value - Integer

        """
        msg = bytearray([START_SYSEX, UARM_CODE, READ_ANALOG])
        msg.extend(getOne7BitBytesFloatArray(pin_num))
        msg.append(END_SYSEX)
        self.serial_write(msg)
        while self.sp.readable():
            read_byte = self.serial_read()
            received_data = []
            if read_byte == START_SYSEX:
                read_byte = self.serial_read()
                if read_byte == UARM_CODE:
                    read_byte = self.serial_read()
                    while read_byte != END_SYSEX:
                        received_data.append(read_byte)
                        read_byte = self.serial_read()
                    if received_data[0] == pin_num:
                        return received_data[2] * 128 + received_data[1]

    def read_coordinate(self):
        """
        Read Coordinate from uArm.

        :return: Coordinate array, x, y, z, Float type

        """

        msg = bytearray([START_SYSEX, UARM_CODE, READ_COORDS])
        msg.append(END_SYSEX)
        self.serial_write(msg)

        if self.sp.readable():

            if self.serial_read() == START_SYSEX:
                if self.serial_read() == UARM_CODE:
                    if self.serial_read() == READ_COORDS:
                        coordinate = [getFloatFromFour7BitBytes(self.serial_read(4)), getFloatFromFour7BitBytes(self.serial_read(4)),
                                      getFloatFromFour7BitBytes(self.serial_read(4))] #x, y, z
                        if self.serial_read() == END_SYSEX: # END_SYSEX
                            return coordinate

    def write_eeprom(self, data_type, eeprom_add, eeprom_val):
        """
        Write Data to EEPROM

        Please reference Arduino EEPROMPut_.

        :: _EEPROMPut: https://www.arduino.cc/en/Reference/EEPROMPut

        :param data_type: EEPROM_TYPE_BYTE, EEPROM_TYPE_INTEGER, EEPROM_TYPE_FLOAT
        :param eeprom_add: EEPROM address Integer
        :param eeprom_val: EEPROM Value - Byte, Integer, Float

        """
        msg = bytearray([START_SYSEX, UARM_CODE, WRITE_EEPROM, data_type])
        msg.extend(getTwo7BitBytesIntegerArray(eeprom_add))
        if data_type == EEPROM_DATA_TYPE_BYTE:
            msg.extend(getTwo7BitBytesIntegerArray(eeprom_val))
        if data_type == EEPROM_DATA_TYPE_FLOAT:
            msg.extend(getFour7BitBytesFloatArray(eeprom_val))
        if data_type == EEPROM_DATA_TYPE_INTEGER:
            msg.extend(getThree7BitBytesIntegerArray(eeprom_val))
        msg.append(END_SYSEX)
        self.serial_write(msg)

    def write_analog(self, pin_number, pin_value):
        """
        Write Analog to PIN

        Please reference Arduino AnalogWrite_.

        :: _AnalogWrite: https://www.arduino.cc/en/Reference/AnalogWrite
        :param pin_number: PIN Number Integer 0 - 13
        :param pin_value: Analog Value

        """
        msg = bytearray([START_SYSEX, UARM_CODE, WRITE_ANALOG])
        msg.extend(getOne7BitBytesFloatArray(pin_number))
        msg.extend(getTwo7BitBytesIntegerArray(pin_value))
        msg.append(END_SYSEX)
        self.serial_write(msg)

    def write_digital(self, pin_number, pin_mode):
        """
        Write Digital to PIN

        Please reference Arduino DigitalWrite_.

        :: _DigitalWrite: https://www.arduino.cc/en/Reference/DigitalWrite

        :param pin_number: PIN Number - Integer 0~13
        :param pin_mode: Digital Value - HIGH, LOW

        """
        msg = bytearray([START_SYSEX, UARM_CODE, WRITE_DIGITAL])
        msg.extend(getOne7BitBytesFloatArray(pin_number))
        msg.extend(getOne7BitBytesFloatArray(pin_mode))
        msg.append(END_SYSEX)
        self.serial_write(msg)

    def detach_all_servos(self):
        """
        Detach All Servos

        Unlock the servo after detach.
        """
        self.set_servo_status(SERVO_BOTTOM, False)
        self.set_servo_status(SERVO_LEFT, False)
        self.set_servo_status(SERVO_RIGHT, False)
        self.set_servo_status(SERVO_HAND, False)

    def attach_all_servos(self):
        """
        Attach All Servos

        Lock the servo.
        """
        self.set_servo_status(SERVO_BOTTOM, True)
        self.set_servo_status(SERVO_LEFT, True)
        self.set_servo_status(SERVO_RIGHT, True)
        self.set_servo_status(SERVO_HAND, True)

    def set_servo_status(self, servo_number, status):
        """
        Set Servo Status
        :param servo_number: SERVO_BOTTOM_NUM, SERVO_LEFT, SERVO_RIGHT, SERVO_HAND
        :param status: True - Attach, False - Detach
        """
        msg = bytearray([START_SYSEX, UARM_CODE, SERVO_STATUS])
        msg.extend(getOne7BitBytesFloatArray(servo_number))
        msg.extend(getOne7BitBytesFloatArray(1 if status else 0))
        msg.append(END_SYSEX)
        self.serial_write(msg)

    def write_servo_angle(self, servo_number, servo_angle, with_offset):
        """
        Write Servo Angle

        :param servo_number: SERVO_BOTTOM_NUM, SERVO_LEFT, SERVO_RIGHT, SERVO_HAND
        :param servo_angle: float type between 0.00 ~ 180.00
        :param with_offset: True, False

        """
        servo_number = int(servo_number)
        servo_angle = float(servo_angle)
        with_offset = int(with_offset)
        msg = bytearray([START_SYSEX, UARM_CODE, WRITE_ANGLE])
        msg.extend(getOne7BitBytesFloatArray(servo_number))
        msg.extend(getThree7BitBytesFloatArray(servo_angle))
        msg.extend(getOne7BitBytesFloatArray(with_offset))
        msg.append(END_SYSEX)
        self.serial_write(msg)

    def write_left_right_servo_angle(self, servo_left_angle, servo_right_angle, with_offset):
        """

        :param servo_left_angle:
        :param servo_right_angle:
        :param with_offset:

        """
        with_offset = int(with_offset)
        servo_left_angle = float(servo_left_angle)
        servo_right_angle = float(servo_right_angle)
        msg = bytearray([START_SYSEX, UARM_CODE, WRITE_LEFT_RIGHT_ANGLE])
        msg.extend(getThree7BitBytesFloatArray(servo_left_angle))
        msg.extend(getThree7BitBytesFloatArray(servo_right_angle))
        msg.extend(getOne7BitBytesFloatArray(with_offset))
        msg.append(END_SYSEX)
        self.serial_write(msg)

    def move_to(self, x, y, z, hand_angle=None, relative_flags=ABSOLUTE, time_spend=2, path_type=PATH_LINEAR, ease_type=INTERP_EASE_INOUT_CUBIC):
        """
        Move uArm to a `coordinate(x,y,z)` or `Angles(bottom,left,right,hand)`.

        Default parameters `move_to(x,y,z,0, ABSOLUTE, 2, PATH_LINEAR, INTERP_EASE_INOUT_CUBIC)`

        Move uArm to a `coordinate(x,y,z)` in 2 seconds.

        :param x: Float type, X Axis.
        :param y: Float type, Y Axis.
        :param z: Float type, Z Axis.
        :param hand_angle: Float Type, Hand Angle.
        :param relative_flags: ABSOLUTE, RELATIVE, default is ABSOLUTE
        :param time_spend: Float type, time_spend, default is 2
        :param path_type: Path Type, PATH_LINEAR, PATH_ANGLES, default is PATH_LINEAR
        :param ease_type: Ease Type, INTERP_EASE_INOUT_CUBIC, INTERP_LINEAR, INTERP_EASE_INOUT, INTERP_EASE_IN, INTERP_EASE_OUT

        """
        enable_hand = 1 if hand_angle is not None else 0
        x, y, z = float(x), float(y), float(z)
        msg = bytearray([START_SYSEX, UARM_CODE, WRITE_COORDS])
        msg.extend(getFour7BitBytesFloatArray(x))
        msg.extend(getFour7BitBytesFloatArray(y))
        msg.extend(getFour7BitBytesFloatArray(z))
        msg.extend(getThree7BitBytesFloatArray(hand_angle if hand_angle is not None else 0))
        msg.extend(getOne7BitBytesFloatArray(relative_flags))
        msg.extend(getThree7BitBytesFloatArray(time_spend))
        msg.extend(getOne7BitBytesFloatArray(path_type))
        msg.extend(getOne7BitBytesFloatArray(ease_type))
        msg.extend(getOne7BitBytesFloatArray(enable_hand))
        msg.append(END_SYSEX)
        time.sleep(0.01)
        self.serial_write(msg)

    def pump_control(self, val):
        """
        Control Pump On or Off
        :param val: True is On, False is Off.

        """
        pump_status = 1 if val else 0
        msg = bytearray([START_SYSEX, UARM_CODE, PUMP_STATUS])
        msg.extend(getOne7BitBytesFloatArray(pump_status))
        msg.append(END_SYSEX)
        self.serial_write(msg)

    def gripper_control(self, val):
        """
        Control Gripper On or Off
        :param val: True is On, False is Off.

        """
        gripper_status = 1 if val else 0
        msg = bytearray([START_SYSEX, UARM_CODE, GRIPPER_STATUS])
        msg.extend(getOne7BitBytesFloatArray(gripper_status))
        msg.append(END_SYSEX)
        self.serial_write(msg)

    def write_stretch(self, length, height):
        """
        Write Stretch is another control method for uArm.

        Length means uArm Y Axis. between (0, 195)
        Height means uArm Z Axis. between (-150, 130)

        :param length: Float Type, between (0, 195)
        :param height: Float Type, between (-150, 130)

        """
        length = float(length)
        height = float(height)
        msg = bytearray([START_SYSEX, UARM_CODE, WRITE_STRETCH])
        msg.extend(getFour7BitBytesFloatArray(length))
        msg.extend(getFour7BitBytesFloatArray(height))
        msg.append(END_SYSEX)
        self.serial_write(msg)

    def write_serial_number(self, serial_number):
        """
        Write Serial Number to uArm.
        Serial Number is 15 digital number
        eg. UARM030715011B
        :param serial_number:

        """
        msg = bytearray([START_SYSEX, UARM_CODE, WRITE_SERIAL_NUMBER])
        for c in serial_number:
            msg.append(ord(c))
        msg.append(END_SYSEX)
        self.serial_write(msg)

    def read_serial_number(self):
        """
        Read Serial Number from uArm.
        Serial Number is 15 digital number
        eg. UARM030715011B
        """
        msg = bytearray([START_SYSEX, UARM_CODE, READ_SERIAL_NUMBER, END_SYSEX])
        self.serial_write(msg)
        while self.sp.readable():
            read_byte = self.serial_read()
            received_data = []
            if read_byte == START_SYSEX:
                read_byte = self.serial_read()
                if read_byte == UARM_CODE:
                    read_byte = self.serial_read()
                    if read_byte == READ_SERIAL_NUMBER:
                        read_byte = self.serial_read()
                        while read_byte != END_SYSEX:
                            received_data.append(read_byte)
                            read_byte = self.serial_read()
                        sn_array = []
                        for r in received_data:
                            sn_array.append(chr(r))
                        return ''.join(sn_array)

    def alarm(self, times, run_time, stop_time):
        """
        Alarm the Buzzer.
        eg.

        ::

            >>> import pyuarm
            >>> uarm = pyuarm.uArm(debug=True)
            Initialize uArm, port is /dev/cu.usbserial-A600CVS9...
            f925Serial Read: f079135504107206d04606907206d06107406102e06906e06f0f7
            Serial Write:f0aa23f7
            Serial Read: f0aa2315bf7
            Firmware Version: 1.5.11
            >>> uarm.alarm(1, 100, 100)
            Serial Write:f0aa24016464f7
            >>> uarm.alarm(3, 100, 100)
            Serial Write:f0aa24036464f7


        :param times: Alarm times
        :param run_time: Alarm Run Times.
        :param stop_time: Alarm Stop Times.

        """
        msg = bytearray([START_SYSEX, UARM_CODE, BUZZER_ALERT, times, run_time, stop_time, END_SYSEX])
        self.serial_write(msg)

    def get_firmware_version(self):
        """
        Read Firmware Vresion from uArm.
        """
        if self.is_connected():
            msg = bytearray([START_SYSEX, UARM_CODE, REPORT_FIRMWARE_VERSION, END_SYSEX])
            self.serial_write(msg)
            while self.sp.readable():
                read_byte = self.serial_read()
                received_data = []
                if read_byte == START_SYSEX:
                    read_byte = self.serial_read()
                    if read_byte == UARM_CODE:
                        read_byte = self.serial_read()
                        if read_byte == REPORT_FIRMWARE_VERSION:
                            read_byte = self.serial_read()
                            while read_byte != END_SYSEX:
                                received_data.append(read_byte)
                                read_byte = self.serial_read()
                            self.firmware_major_version = received_data[0]
                            self.firmware_minor_version = received_data[1]
                            self.firmware_bugfix = received_data[2]
                            self.firmware_version = str(self.firmware_major_version) + "." + str(
                                self.firmware_minor_version) + "." + str(self.firmware_bugfix)
                            break
        else:
            print("uArm is not Connected")

    def serial_write(self, msg):
        """
        Write message to Serial Port.
        If debug is True, will display all Serial Write message.

        :param msg: Serial Message, bytearray.

        """
        if self.debug:
            print("Serial Write: {0}".format(binascii.hexlify(msg)))
        self.sp.write(msg)

    def serial_read(self, count=1):
        """
        Read one byte from Serial Port. If Debug is True, will display all Serial Read message.
        """
        if count == 1:
            read_byte = ord(self.sp.read(1))
            if self.debug:
                if read_byte == START_SYSEX:
                    print ("Serial Read:", end=' ')
                print(format(read_byte, '02x'), end='')
                if read_byte == END_SYSEX:
                    print("")
            return read_byte
        else:
            read_bytes = self.sp.read(count)
            if self.debug:
                print(binascii.hexlify(read_bytes), end='')
            return read_bytes
